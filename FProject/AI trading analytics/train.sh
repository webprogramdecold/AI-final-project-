#!/usr/bin/env bash
# Train the advanced AI model for AI Trading Analytics.
# Must be run from the AI trading analytics folder (contains app.py and services/).

cd "$(dirname "$0")"

if command -v python3 &>/dev/null; then
    exec python3 -m services.train_advanced_ai_model "$@"
else
    exec python -m services.train_advanced_ai_model "$@"
fi

