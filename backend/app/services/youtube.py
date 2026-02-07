"""
YouTube 字幕取得サービス

ライブラリ選定: youtube-transcript-api を採用
- 理由:
  1. 軽量(字幕取得に特化、yt-dlpは汎用的で依存が大きい)
  2. 字幕取得APIが直感的で使いやすい
  3. 言語指定・フォールバック対応が組み込み済み
  4. 動画のダウンロードは不要なため、yt-dlpはオーバースペック
"""

import re
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from app.models.schemas import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class YouTubeTranscriptError(Exception):
    """字幕取得に関するカスタム例外"""

    def __init__(self, message: str, error_code: str = "TRANSCRIPT_ERROR"):
        """エラーメッセージとコードを設定する。"""
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


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
