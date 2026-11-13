#!/usr/bin/env bash
# Run from project root: bash scripts/start_linux_mac.sh
set -e
cd "$(dirname "$0")/.."
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py check
python manage.py runserver
