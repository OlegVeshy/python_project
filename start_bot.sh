#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
    echo "Virtual environment was not found."
    echo "Create it and install dependencies first:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

exec .venv/bin/python -m calendar_bot.main
