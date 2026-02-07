"""
API エンドポイントのテスト
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.youtube import YouTubeTranscriptError

client = TestClient(app)


class TestHealth:
    """ヘルスチェックのテスト"""

    def test_health_returns_200(self):
        """GET /health が 200 と status: ok を返す"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSummarize:
    """要約APIのテスト"""

    def test_summarize_invalid_url_returns_422(self):
        """無効なURLで 422 バリデーションエラーになる"""
        response = client.post(
            "/api/summarize",
            json={"url": "https://example.com/not-youtube"},
        )
        assert response.status_code == 422

    def test_summarize_missing_url_returns_422(self):
        """url なしで 422 になる"""
        response = client.post(
            "/api/summarize",
            json={},
        )
        assert response.status_code == 422

    @patch("app.routers.summarize.fetch_transcript", new_callable=AsyncMock)
    def test_summarize_no_transcript_returns_404(self, mock_fetch):
        """字幕がない場合 404 と detail を返す"""
        mock_fetch.side_effect = YouTubeTranscriptError(
            "この動画には利用可能な字幕がありません",
            error_code="NO_TRANSCRIPT",
        )
        response = client.post(
            "/api/summarize",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "language": "ja"},
        )
        assert response.status_code == 404
        body = response.json()
        assert "detail" in body
        assert body["detail"]["error_code"] == "NO_TRANSCRIPT"
