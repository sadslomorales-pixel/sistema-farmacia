#!/bin/bash
python -c "from app import init_db; init_db()"
gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 2
