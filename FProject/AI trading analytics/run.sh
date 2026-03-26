#!/usr/bin/env bash
# Run AI Trading Analytics. Must be run from the AI trading analytics folder (contains app.py and templates).
cd "$(dirname "$0")"
if command -v python3 &>/dev/null; then
    exec python3 app.py "$@"
else
    exec python app.py "$@"
fi
