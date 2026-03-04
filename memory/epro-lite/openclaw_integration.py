#!/usr/bin/env python3
"""
OpenClaw integration for epro-lite memory
Call this from OpenClaw sessions to capture and recall memories
"""

import json
import sys
from memory_manager import EproLite

def capture(session_messages: list) -> dict:
    """
    Capture memories from a conversation
    
    Args:
        session_messages: List of message dicts with 'role' and 'content'
    
    Returns:
        dict with extraction results
    """
    epro = EproLite()
    result = epro.process_conversation(session_messages)
    return result

def recall(query: str, category: str = None) -> list:
    """
    Recall relevant memories for a query
    
    Args:
        query: Search query
        category: Optional category filter
    
    Returns:
        List of relevant memories
    """
    epro = EproLite()
    return epro.recall(query, category)

def get_memories(category: str = None) -> list:
    """
    Get all memories, optionally filtered by category
    
    Args:
        category: Optional category filter
    
    Returns:
        List of memories
    """
    epro = EproLite()
    memories = epro.memories['memories']
    if category:
        memories = [m for m in memories if m['category'] == category]
    return memories

def clear():
    """Clear all memories"""
    epro = EproLite()
    epro.memories = {"memories": [], "version": 1}
    epro._save_memories()
    return {"status": "cleared"}


# CLI interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python openclaw_integration.py capture <messages.json>")
        print("  python openclaw_integration.py recall <query>")
        print("  python openclaw_integration.py get [category]")
        print("  python openclaw_integration.py clear")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "capture":
        if len(sys.argv) < 3:
            print("Error: provide messages.json file")
            sys.exit(1)
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            messages = json.load(f)
        result = capture(messages)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == "recall":
        if len(sys.argv) < 3:
            print("Error: provide query")
            sys.exit(1)
        query = sys.argv[2]
        category = sys.argv[3] if len(sys.argv) > 3 else None
        results = recall(query, category)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    
    elif command == "get":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        memories = get_memories(category)
        print(json.dumps(memories, ensure_ascii=False, indent=2))
    
    elif command == "clear":
        result = clear()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
