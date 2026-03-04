#!/usr/bin/env python3
"""
epro-lite: Lightweight memory manager for OpenClaw
Supports optional vector search with embedding API
"""

import json
import os
import re
import uuid
import time
import requests
from datetime import datetime
from typing import Optional, List
from openai import OpenAI

class EproLite:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = "/root/.openclaw/workspace/memory/epro-lite/config.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.storage_path = self.config['storage']['path']
        self.backup_path = self.config['storage']['backupPath']
        self.memories = self._load_memories()
        
        # Initialize LLM client (OpenAI-compatible)
        llm_cfg = self.config['llm']
        self.client = OpenAI(
            api_key=llm_cfg['apiKey'],
            base_url=llm_cfg['baseUrl'],
            timeout=llm_cfg.get('timeout', 120)
        )
        self.model = llm_cfg['model']
        
        # Initialize embedding config
        emb_cfg = self.config.get('embedding', {})
        self.use_embedding = emb_cfg.get('enabled', False) and bool(emb_cfg.get('apiKey', ''))
        self.emb_config = emb_cfg
    
    def _load_memories(self) -> dict:
        """Load memories from JSON file"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"memories": [], "version": 1}
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding vector from API"""
        if not self.use_embedding:
            return None
        
        try:
            url = f"{self.emb_config['baseUrl'].rstrip('/')}/services/embeddings/text-embedding/text-embedding"
            headers = {
                'Authorization': f"Bearer {self.emb_config['apiKey']}",
                'Content-Type': 'application/json'
            }
            data = {
                'model': self.emb_config['model'],
                'input': {'texts': [text]}
            }
            
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            
            if 'output' in result and 'embeddings' in result['output']:
                return result['output']['embeddings'][0]['embedding']
            return None
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not a or not b:
            return 0.0
        
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    
    def _save_memories(self):
        """Save memories to JSON file with backup"""
        if self.config['storage']['autoBackup'] and os.path.exists(self.storage_path):
            # Create backup
            backup_num = 0
            while backup_num < self.config['storage']['maxBackups']:
                backup_file = f"{self.backup_path}.{backup_num}"
                if not os.path.exists(backup_file):
                    with open(self.storage_path, 'r', encoding='utf-8') as src:
                        with open(backup_file, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                    break
                backup_num += 1
            # Rotate backups
            for i in range(self.config['storage']['maxBackups'] - 1, 0, -1):
                old = f"{self.backup_path}.{i-1}"
                new = f"{self.backup_path}.{i}"
                if os.path.exists(old):
                    os.rename(old, new) if os.path.exists(old) else None
        
        # Save current
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)
    
    def extract_memories(self, conversation: str) -> list:
        """Extract memories from conversation using LLM"""
        prompt = f"""You are a memory extraction assistant. Analyze the conversation and extract memorable information.

Categories:
- profile: User identity, static attributes (name, role, etc.)
- preferences: User tendencies, habits, preferences
- entities: Projects, people, organizations mentioned
- events: Decisions, milestones, things that happened
- cases: Problem + solution pairs
- patterns: Reusable processes and methods

Conversation:
{conversation[:self.config['extraction']['maxChars']]}

Extract memories in JSON format:
[
  {{
    "category": "profile|preferences|entities|events|cases|patterns",
    "l0": "One sentence summary",
    "l1": {{"key": "value"}},
    "l2": "Full narrative description",
    "keywords": ["keyword1", "keyword2"]
  }}
]

Return ONLY valid JSON array, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            # Extract JSON from response
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                candidates = json.loads(match.group())
                return candidates
            return []
        except Exception as e:
            print(f"Extraction error: {e}")
            return []
    
    def dedup_check(self, candidate: dict) -> tuple:
        """Check if memory is duplicate using LLM"""
        if not self.memories['memories']:
            return True, "new"
        
        # Get similar memories by keyword matching first
        candidate_keywords = set(candidate.get('keywords', []))
        similar = []
        for mem in self.memories['memories']:
            mem_keywords = set(mem.get('keywords', []))
            overlap = len(candidate_keywords & mem_keywords)
            if overlap >= 1 or mem['category'] == candidate['category']:
                similar.append(mem)
        
        if not similar:
            return True, "new"
        
        # Use LLM to decide
        prompt = f"""Compare these memories and decide if the new one is a duplicate.

New Memory:
Category: {candidate['category']}
Summary: {candidate['l0']}
Details: {candidate['l2']}

Existing Memories:
{json.dumps(similar[:3], ensure_ascii=False, indent=2)}

Respond with ONLY one word:
- CREATE: if new memory adds unique information
- MERGE: if new memory updates existing (specify which ID)
- SKIP: if new memory is duplicate

Format: CREATE or MERGE:<id> or SKIP"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            decision = response.choices[0].message.content.strip().upper()
            
            if decision == "SKIP":
                return False, "duplicate"
            elif decision.startswith("MERGE:"):
                merge_id = decision.split(":")[1].strip()
                return False, f"merge:{merge_id}"
            else:
                return True, "new"
        except Exception as e:
            print(f"Dedup error: {e}")
            return True, "new"
    
    def add_memory(self, candidate: dict) -> Optional[dict]:
        """Add a memory after dedup check"""
        is_new, result = self.dedup_check(candidate)
        
        if not is_new:
            if result.startswith("merge:"):
                merge_id = result.split(":")[1]
                # Merge logic
                for mem in self.memories['memories']:
                    if mem['id'] == merge_id:
                        mem['l2'] = candidate['l2']
                        mem['updated_at'] = datetime.now().isoformat()
                        mem['keywords'] = list(set(mem.get('keywords', []) + candidate.get('keywords', [])))
                        self._save_memories()
                        return mem
            return None
        
        # Create new memory
        memory = {
            "id": str(uuid.uuid4()),
            "category": candidate['category'],
            "l0": candidate['l0'],
            "l1": candidate.get('l1', {}),
            "l2": candidate['l2'],
            "keywords": candidate.get('keywords', []),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "access_count": 0
        }
        
        # Add embedding if enabled
        if self.use_embedding:
            embedding = self._get_embedding(memory['l0'] + ' ' + memory['l2'])
            if embedding:
                memory['embedding'] = embedding
        
        self.memories['memories'].append(memory)
        self._save_memories()
        return memory
    
    def recall(self, query: str, category: str = None) -> list:
        """Recall relevant memories for a query using hybrid search (vector + keyword)"""
        if not self.memories['memories']:
            return []
        
        import re
        query_keywords = set(re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+|\d+\.\d+\.\d+\.\d+', query.lower()))
        scored = {}  # id -> (score, mem)
        
        # Vector search (if enabled)
        if self.use_embedding:
            query_embedding = self._get_embedding(query)
            if query_embedding:
                for mem in self.memories['memories']:
                    if category and mem['category'] != category:
                        continue
                    
                    mem_embedding = mem.get('embedding')
                    if not mem_embedding:
                        mem_embedding = self._get_embedding(mem['l0'] + ' ' + mem['l2'])
                        if mem_embedding:
                            mem['embedding'] = mem_embedding
                    
                    if mem_embedding:
                        similarity = self._cosine_similarity(query_embedding, mem_embedding)
                        if similarity >= self.config['recall'].get('minRelevance', 0.4):
                            # Scale similarity to 0-10 range
                            scored[mem['id']] = (similarity * 10, mem.copy())
        
        # Keyword search
        for mem in self.memories['memories']:
            if category and mem['category'] != category:
                continue
            
            mem_keywords = set(kw.lower() for kw in mem.get('keywords', []))
            overlap = len(query_keywords & mem_keywords)
            
            if any(kw in mem['l0'].lower() for kw in query_keywords):
                overlap += 2
            if any(kw in mem['l2'].lower() for kw in query_keywords):
                overlap += 1
            
            if overlap > 0:
                if mem['id'] in scored:
                    # Combine scores (vector + keyword)
                    old_score, _ = scored[mem['id']]
                    scored[mem['id']] = (old_score + overlap, mem.copy())
                else:
                    scored[mem['id']] = (overlap, mem.copy())
        
        # Sort by combined score
        sorted_scores = sorted(scored.values(), key=lambda x: x[0], reverse=True)
        
        # Return results
        results = [mem for _, mem in sorted_scores[:self.config['recall']['maxResults']]]
        for mem in results:
            mem['access_count'] = mem.get('access_count', 0) + 1
        self._save_memories()
        return results
    
    def _recall_vector(self, query: str, category: str = None) -> list:
        """Recall memories using vector similarity"""
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            # Fallback to keyword
            return self.recall(query, category)
        
        scored = []
        for mem in self.memories['memories']:
            if category and mem['category'] != category:
                continue
            
            # Get stored embedding or compute on the fly
            mem_embedding = mem.get('embedding')
            if not mem_embedding:
                mem_embedding = self._get_embedding(mem['l0'] + ' ' + mem['l2'])
                mem['embedding'] = mem_embedding  # Cache for next time
            
            if mem_embedding:
                similarity = self._cosine_similarity(query_embedding, mem_embedding)
                if similarity >= self.config['recall'].get('minRelevance', 0.6):
                    scored.append((similarity, mem.copy()))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Return results
        results = [mem for _, mem in scored[:self.config['recall']['maxResults']]]
        
        # Update access count
        for mem in results:
            mem['access_count'] = mem.get('access_count', 0) + 1
        self._save_memories()
        
        return results
    
    def _recall_vector_with_llm_rerank(self, scored: list) -> list:
        """Use LLM to re-rank top results"""
        if len(scored) > 3:
            top = scored[:self.config['recall']['maxResults'] * 2]
            prompt = f"""Rank these memories by relevance to the query.

Query: {query}

Memories:
{json.dumps([m for _, m in top], ensure_ascii=False, indent=2)}

Return ONLY the IDs of the top {self.config['recall']['maxResults']} most relevant memories, one per line."""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.1
                )
                
                ids = [line.strip() for line in response.choices[0].message.content.strip().split('\n') if line.strip()]
                
                # Reorder by LLM ranking
                ranked = []
                for mid in ids:
                    for _, mem in scored:
                        if mem['id'] == mid:
                            ranked.append(mem)
                            break
                
                # Update access count
                for mem in ranked[:self.config['recall']['maxResults']]:
                    mem['access_count'] = mem.get('access_count', 0) + 1
                self._save_memories()
                
                return ranked[:self.config['recall']['maxResults']]
            except Exception as e:
                print(f"Recall re-rank error: {e}")
        
        # Fallback to keyword scoring
        results = [mem for _, mem in scored[:self.config['recall']['maxResults']]]
        for mem in results:
            mem['access_count'] = mem.get('access_count', 0) + 1
        self._save_memories()
        return results
    
    def process_conversation(self, messages: list) -> dict:
        """Process a conversation and extract/store memories"""
        # Convert messages to string
        conversation = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages])
        
        # Check if extraction should be triggered
        trigger_keywords = self.config['extraction']['triggerKeywords']
        should_extract = any(kw in conversation for kw in trigger_keywords)
        
        if not should_extract and len(messages) < self.config['extraction']['minMessages']:
            return {"extracted": 0, "stored": 0, "reason": "no_trigger"}
        
        # Extract candidates
        candidates = self.extract_memories(conversation)
        
        # Store valid memories
        stored = []
        for candidate in candidates:
            result = self.add_memory(candidate)
            if result:
                stored.append(result)
        
        return {
            "extracted": len(candidates),
            "stored": len(stored),
            "memories": stored
        }


# CLI for testing
if __name__ == "__main__":
    import sys
    
    epro = EproLite()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "extract":
            # Test extraction
            conversation = """
            用户：我叫舟哥，喜欢用 Python 做量化交易
            助手：好的舟哥，我记住了
            用户：别忘了我不喜欢复杂的配置
            """
            result = epro.process_conversation([{"role": "user", "content": conversation}])
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif command == "recall":
            query = sys.argv[2] if len(sys.argv) > 2 else "Python"
            results = epro.recall(query)
            print(json.dumps(results, ensure_ascii=False, indent=2))
        
        elif command == "list":
            print(json.dumps(epro.memories, ensure_ascii=False, indent=2))
        
        elif command == "clear":
            epro.memories = {"memories": [], "version": 1}
            epro._save_memories()
            print("Memories cleared")
        
        else:
            print("Usage: python memory_manager.py [extract|recall|list|clear]")
    else:
        print("epro-lite memory manager")
        print(f"Storage: {epro.storage_path}")
        print(f"Memories: {len(epro.memories['memories'])}")
        print("Commands: extract, recall, list, clear")
