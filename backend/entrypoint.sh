#!/bin/sh
# Railway などが注入する PORT を必ずここで読んでから uvicorn に渡す
port="${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$port"
