#!/usr/bin/env python3
"""
OpenClaw Session Hooks for epro-lite Memory

This script is called by OpenClaw at session start and end.

Usage:
  # Session start - recall memories
  python3 session_hooks.py start "<user_message>"
  
  # Session end - capture memories
  python3 session_hooks.py end /path/to/messages.json
"""

import json
import sys
import os
import subprocess

EPRO_LITE_DIR = "/root/.openclaw/workspace/memory/epro-lite"
INTEGRATION_SCRIPT = os.path.join(EPRO_LITE_DIR, "openclaw_integration.py")

def recall_memories(query: str, max_results: int = 3) -> str:
    """
    Recall memories for a query and return formatted context string.
    
    Args:
        query: User's message or session context
        max_results: Maximum number of memories to return
    
    Returns:
        Formatted string of relevant memories
    """
    try:
        result = subprocess.run(
            ["python3", INTEGRATION_SCRIPT, "recall", query],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"Recall error: {result.stderr}", file=sys.stderr)
            return ""
        
        memories = json.loads(result.stdout)
        
        if not memories:
            return ""
        
        # Format memories as context
        lines = ["## 🧠 相关记忆"]
        for mem in memories[:max_results]:
            category_label = {
                "profile": "👤 用户信息",
                "preferences": "⭐ 偏好习惯",
                "entities": "📌 实体",
                "events": "📅 事件",
                "cases": "💡 案例",
                "patterns": "🔁 模式"
            }.get(mem["category"], mem["category"])
            
            lines.append(f"- **{category_label}**: {mem['l0']}")
        
        lines.append("")
        return "\n".join(lines)
    
    except Exception as e:
        print(f"Recall exception: {e}", file=sys.stderr)
        return ""


def capture_memories(messages_path: str) -> dict:
    """
    Capture memories from session messages.
    
    Args:
        messages_path: Path to JSON file containing session messages
    
    Returns:
        Dict with capture results
    """
    try:
        result = subprocess.run(
            ["python3", INTEGRATION_SCRIPT, "capture", messages_path],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode != 0:
            print(f"Capture error: {result.stderr}", file=sys.stderr)
            return {"error": result.stderr}
        
        return json.loads(result.stdout)
    
    except Exception as e:
        print(f"Capture exception: {e}", file=sys.stderr)
        return {"error": str(e)}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "start":
        # Session start - recall memories
        user_message = sys.argv[2]
        context = recall_memories(user_message)
        
        if context:
            print(context)
        else:
            print("No relevant memories found.")
    
    elif command == "end":
        # Session end - capture memories
        messages_path = sys.argv[2]
        
        if not os.path.exists(messages_path):
            print(f"Error: messages file not found: {messages_path}", file=sys.stderr)
            sys.exit(1)
        
        result = capture_memories(messages_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
