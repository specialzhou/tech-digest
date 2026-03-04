#!/usr/bin/env python3
"""
Save OpenClaw session messages to a file for epro-lite capture.

This script reads session messages from stdin or a file and saves them
to the epro-lite messages format.

Usage:
  # From stdin (piped from OpenClaw)
  echo '{"messages": [...]}' | python3 save_session.py /tmp/session.json
  
  # From file
  python3 save_session.py /tmp/session.json --input /path/to/input.json
"""

import json
import sys
import os

def save_messages(output_path: str, messages: list):
    """
    Save messages in epro-lite format.
    
    Args:
        output_path: Path to save messages
        messages: List of message dicts with 'role' and 'content'
    """
    # Convert to epro-lite format if needed
    epro_format = []
    for msg in messages:
        if isinstance(msg, dict):
            # Handle different message formats
            if 'role' in msg and 'content' in msg:
                epro_format.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            elif 'sender' in msg and 'text' in msg:
                # Telegram-style format
                role = 'user' if msg.get('sender') == 'user' else 'assistant'
                epro_format.append({
                    'role': role,
                    'content': msg['text']
                })
            elif 'from' in msg and 'message' in msg:
                # Another common format
                role = 'user' if msg.get('from') == 'user' else 'assistant'
                epro_format.append({
                    'role': role,
                    'content': msg['message']
                })
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(epro_format, f, ensure_ascii=False, indent=2)
    
    return len(epro_format)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 save_session.py <output.json> [--input <input.json>]")
        sys.exit(1)
    
    output_path = sys.argv[1]
    input_path = None
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--input' and i + 1 < len(sys.argv):
            input_path = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # Read messages
    if input_path:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # Read from stdin
        data = json.load(sys.stdin)
    
    # Extract messages from different formats
    if isinstance(data, list):
        messages = data
    elif isinstance(data, dict):
        if 'messages' in data:
            messages = data['messages']
        elif 'session' in data and 'messages' in data['session']:
            messages = data['session']['messages']
        else:
            # Assume the dict itself is a message list
            messages = [data]
    else:
        print(f"Error: Unknown data format: {type(data)}", file=sys.stderr)
        sys.exit(1)
    
    # Save
    count = save_messages(output_path, messages)
    print(f"Saved {count} messages to {output_path}")


if __name__ == "__main__":
    main()
