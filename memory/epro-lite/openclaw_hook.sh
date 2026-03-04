#!/bin/bash
# OpenClaw Session Hook Script for epro-lite Memory
# 
# This script is called by OpenClaw at session boundaries.
# 
# Usage (session start):
#   ./openclaw_hook.sh start "user's message here"
#
# Usage (session end):
#   ./openclaw_hook.sh end /path/to/messages.json

set -e

EPRO_LITE_DIR="/root/.openclaw/workspace/memory/epro-lite"
HOOKS_SCRIPT="$EPRO_LITE_DIR/session_hooks.py"

case "$1" in
    start)
        # Session start - recall memories and output context
        if [ -z "$2" ]; then
            echo "Error: missing user message" >&2
            exit 1
        fi
        python3 "$HOOKS_SCRIPT" start "$2"
        ;;
    
    end)
        # Session end - capture memories from messages
        if [ -z "$2" ]; then
            echo "Error: missing messages file" >&2
            exit 1
        fi
        python3 "$HOOKS_SCRIPT" end "$2"
        ;;
    
    *)
        echo "Usage: $0 {start|end} <argument>" >&2
        echo "  start <user_message>  - Recall memories for user message" >&2
        echo "  end <messages.json>   - Capture memories from session" >&2
        exit 1
        ;;
esac
