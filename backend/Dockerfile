# Railway などでビルドが失敗する場合に Dockerfile で明示的にビルドする
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENV PORT=8000
EXPOSE 8000

# 起動スクリプトで PORT を読むので、Railway の Start Command 上書き時も確実に動く
CMD ["./entrypoint.sh"]
