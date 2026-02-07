# Railway などでビルドが失敗する場合に Dockerfile で明示的にビルドする
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Railway は実行時に PORT を注入。sh -c で展開しないと "$PORT" がそのまま渡ってエラーになる
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
