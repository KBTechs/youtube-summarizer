"""
YouTube字幕取得サービスのテスト
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.youtube import extract_video_id, fetch_transcript, YouTubeTranscriptError


class TestExtractVideoId:
    """動画ID抽出のテスト"""

    def test_standard_url(self):
        """標準的なYouTube URLからIDを抽出できる"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url(self):
        """短縮URLからIDを抽出できる"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        """Shorts URLからIDを抽出できる"""
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        """追加パラメータ付きURLからIDを抽出できる"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_url_without_www(self):
        """www無しのURLからIDを抽出できる"""
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url_raises_error(self):
        """無効なURLでエラーが発生する"""
        with pytest.raises(YouTubeTranscriptError) as exc_info:
            extract_video_id("https://example.com/video")
        assert exc_info.value.error_code == "INVALID_URL"

    def test_empty_url_raises_error(self):
        """空のURLでエラーが発生する"""
        with pytest.raises(YouTubeTranscriptError):
            extract_video_id("")


class TestFetchTranscript:
    """字幕取得のテスト"""

    @pytest.mark.asyncio
    async def test_fetch_transcript_success(self):
        """正常に字幕を取得できる"""
        # モックの字幕データ
        mock_entry = MagicMock()
        mock_entry.text = "こんにちは"
        mock_entry.start = 0.0
        mock_entry.duration = 2.5
        mock_transcript_data = [mock_entry]

        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = mock_transcript_data

        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.return_value = mock_transcript

        with patch(
            "app.services.youtube.YouTubeTranscriptApi",
        ) as MockApi, patch(
            "app.services.youtube.TextFormatter.format_transcript",
            return_value="こんにちは",
        ):
            MockApi.return_value.list.return_value = mock_transcript_list
            result = await fetch_transcript(
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                language="ja",
            )

        assert result.video_id == "dQw4w9WgXcQ"
        assert result.language == "ja"
        assert len(result.segments) == 1
        assert result.segments[0].text == "こんにちは"
        assert result.full_text == "こんにちは"

    @pytest.mark.asyncio
    async def test_fetch_transcript_no_subtitles(self):
        """字幕が存在しない場合にエラーが発生する"""
        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.side_effect = Exception("Not found")
        mock_transcript_list.find_generated_transcript.side_effect = Exception("Not found")

        with patch(
            "app.services.youtube.YouTubeTranscriptApi",
        ) as MockApi:
            MockApi.return_value.list.return_value = mock_transcript_list
            with pytest.raises(YouTubeTranscriptError) as exc_info:
                await fetch_transcript(
                    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    language="ja",
                )
            assert exc_info.value.error_code in ("NO_TRANSCRIPT", "FETCH_FAILED")

    @pytest.mark.asyncio
    async def test_fetch_transcript_invalid_url(self):
        """無効なURLでエラーが発生する"""
        with pytest.raises(YouTubeTranscriptError) as exc_info:
            await fetch_transcript(url="https://example.com/video")
        assert exc_info.value.error_code == "INVALID_URL"


class TestYouTubeTranscriptError:
    """カスタム例外のテスト"""

    def test_default_error_code(self):
        """デフォルトのエラーコードが設定される"""
        error = YouTubeTranscriptError("テストエラー")
        assert error.error_code == "TRANSCRIPT_ERROR"
        assert str(error) == "テストエラー"

    def test_custom_error_code(self):
        """カスタムエラーコードを設定できる"""
        error = YouTubeTranscriptError("テストエラー", error_code="CUSTOM_ERROR")
        assert error.error_code == "CUSTOM_ERROR"
