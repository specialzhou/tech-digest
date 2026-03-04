#!/bin/bash
# Auto-capture epro-lite memories from recent OpenClaw sessions
# Run this via cron every few minutes

set -e

EPRO_LITE_DIR="/root/.openclaw/workspace/memory/epro-lite"
SESSIONS_DIR="/root/.openclaw/agents/main/sessions"
TMP_DIR="/tmp/epro-lite-capture"

mkdir -p "$TMP_DIR"

# Find recent session files (modified in last 10 minutes)
find "$SESSIONS_DIR" -name "*.jsonl" -mmin -10 -type f 2>/dev/null | while read session_file; do
    session_id=$(basename "$session_file" .jsonl)
    output_file="$TMP_DIR/session_$session_id.json"
    
    # Skip if already processed
    if [ -f "$output_file" ]; then
        continue
    fi
    
    # Extract messages from jsonl session file
    python3 -c "
import json
import sys

messages = []
with open('$session_file', 'r') as f:
    for line in f:
        try:
            entry = json.loads(line.strip())
            if entry.get('type') == 'message' and 'message' in entry:
                msg = entry['message']
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    messages.append({'role': msg['role'], 'content': msg['content']})
        except:
            continue

with open('$output_file', 'w') as f:
    json.dump(messages, f, indent=2)

print(len(messages))
" 2>/dev/null || continue
    
    # Capture memories
    msg_count=$(cat "$output_file" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d))")
    if [ "$msg_count" -gt 2 ]; then
        echo "Capturing memories from session $session_id ($msg_count messages)..."
        python3 "$EPRO_LITE_DIR/openclaw_integration.py" capture "$output_file" 2>&1 | head -20
    fi
done

# Cleanup old temp files (older than 1 hour)
find "$TMP_DIR" -name "*.json" -mmin +60 -delete 2>/dev/null || true

echo "Auto-capture completed at $(date)"
