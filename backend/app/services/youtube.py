"""
YouTube 字幕取得サービス

ライブラリ選定: youtube-transcript-api を採用
- 理由:
  1. 軽量(字幕取得に特化、yt-dlpは汎用的で依存が大きい)
  2. 字幕取得APIが直感的で使いやすい
  3. 言語指定・フォールバック対応が組み込み済み
  4. 動画のダウンロードは不要なため、yt-dlpはオーバースペック

クラウド(Railway等)ではYouTubeがIPをブロックすることがあるため、
環境変数 YOUTUBE_PROXY_URL を設定するとプロキシ経由で取得する。
例: http://proxy.example.com:8080 または socks5://user:pass@host:1080
"""

import os
import re
import logging
import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from app.models.schemas import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)

# 1.0.0+ でプロキシ対応。未対応バージョンでは None のまま
_proxy_config = None
try:
    from youtube_transcript_api.proxies import GenericProxyConfig

    _proxy_url = (os.getenv("YOUTUBE_PROXY_URL") or "").strip()
    if _proxy_url:
        _proxy_config = GenericProxyConfig(http_url=_proxy_url, https_url=_proxy_url)
        logger.info("YouTube 字幕取得: プロキシを有効にしました")
except ImportError:
    pass


class YouTubeTranscriptError(Exception):
    """字幕取得に関するカスタム例外"""

    def __init__(self, message: str, error_code: str = "TRANSCRIPT_ERROR"):
        """エラーメッセージとコードを設定する。"""
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


async def fetch_video_title(video_id: str) -> str:
    """
    YouTube oEmbed API で動画タイトルを取得する。
    失敗時は空文字を返す（要約はタイトルなしで継続）。
    """
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    proxy = (os.getenv("YOUTUBE_PROXY_URL") or "").strip() or None
    try:
        async with httpx.AsyncClient(proxy=proxy, timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            title = (data.get("title") or "").strip()
            if title:
                logger.info("動画タイトル取得: %s", title[:50])
            return title
    except Exception as e:
        logger.debug("動画タイトル取得スキップ: %s", e)
        return ""


def extract_video_id(url: str) -> str:
    """
    YouTube URLから動画IDを抽出する

    対応フォーマット:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    """
    patterns = [
        r"(?:youtube\.com/watch\?v=)([\w-]{11})",
        r"(?:youtu\.be/)([\w-]{11})",
        r"(?:youtube\.com/shorts/)([\w-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise YouTubeTranscriptError(
        "URLから動画IDを抽出できませんでした",
        error_code="INVALID_URL",
    )


async def fetch_transcript(
    url: str,
    language: str = "ja",
) -> TranscriptResult:
    """
    YouTube動画の字幕を取得する

    Args:
        url: YouTube動画のURL
        language: 字幕の言語コード(デフォルト: ja)

    Returns:
        TranscriptResult: 字幕取得結果

    Raises:
        YouTubeTranscriptError: 字幕取得に失敗した場合
    """
    video_id = extract_video_id(url)
    logger.info(f"字幕取得開始: video_id={video_id}, language={language}")

    try:
        # 指定言語の字幕を取得(見つからない場合は自動生成字幕にフォールバック)
        if _proxy_config is not None:
            ytt_api = YouTubeTranscriptApi(proxy_config=_proxy_config)
        else:
            ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        try:
            # まず手動作成の字幕を試行
            transcript = transcript_list.find_transcript([language])
        except Exception:
            try:
                # 自動生成字幕にフォールバック
                transcript = transcript_list.find_generated_transcript([language])
            except Exception:
                # 英語字幕にフォールバックし、翻訳可能か確認
                try:
                    transcript = transcript_list.find_transcript(["en"])
                    if language != "en":
                        transcript = transcript.translate(language)
                except Exception:
                    raise YouTubeTranscriptError(
                        f"この動画には利用可能な字幕がありません(言語: {language})",
                        error_code="NO_TRANSCRIPT",
                    )

        # 字幕データを取得
        transcript_data = transcript.fetch()

        # セグメントに変換
        segments = [
            TranscriptSegment(
                text=entry.text,
                start=entry.start,
                duration=entry.duration,
            )
            for entry in transcript_data
        ]

        # フルテキストを結合
        formatter = TextFormatter()
        full_text = formatter.format_transcript(transcript_data)

        logger.info(
            f"字幕取得成功: video_id={video_id}, "
            f"segments={len(segments)}, chars={len(full_text)}"
        )

        return TranscriptResult(
            video_id=video_id,
            title="",  # タイトルは別途取得が必要(将来拡張)
            language=language,
            segments=segments,
            full_text=full_text,
        )

    except YouTubeTranscriptError:
        raise
    except Exception as e:
        logger.error(f"字幕取得中にエラーが発生: {e}")
        raise YouTubeTranscriptError(
            f"字幕の取得に失敗しました: {str(e)}",
            error_code="FETCH_FAILED",
        )
