# リポジトリルートの Dockerfile（Railway のビルドコンテキストがルートの場合用）
# backend だけをコピーして API をビルドする
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/
COPY backend/entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENV PORT=8000
EXPOSE 8000

# 起動スクリプトで PORT を読むので、Railway の Start Command 上書き時も確実に動く
CMD ["./entrypoint.sh"]
