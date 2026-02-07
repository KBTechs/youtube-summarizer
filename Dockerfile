# リポジトリルートの Dockerfile（Railway のビルドコンテキストがルートの場合用）
# backend だけをコピーして API をビルドする
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/

ENV PORT=8000
EXPOSE 8000

# Railway は実行時に PORT を注入。sh -c で展開しないと "$PORT" がそのまま渡ってエラーになる
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
