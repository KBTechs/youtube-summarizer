"""
Groq API を使用した YouTube 字幕テキスト要約サービス。

Groq Python SDK を利用し、長い字幕テキストをチャンク分割して
段階的に要約を生成するパイプラインを提供する。
"""

import os
import logging
from dataclasses import dataclass

from groq import AsyncGroq

logger = logging.getLogger(__name__)

# --- 定数 ---
MODEL_ID = "llama-3.3-70b-versatile"
# 1チャンクあたりの最大文字数(日本語は1文字≒1-2トークン、余裕を持たせる)
DEFAULT_CHUNK_SIZE = 8000
# チャンク間のオーバーラップ文字数(文脈の断絶を防ぐ)
DEFAULT_CHUNK_OVERLAP = 500
# API呼び出し時の最大出力トークン数
MAX_OUTPUT_TOKENS = 4096
# 要約の一貫性・具体性のため低めに（0=決定的、1=ばらつき大）
DEFAULT_TEMPERATURE = 0.3


# --- プロンプトテンプレート ---

CHUNK_SUMMARY_PROMPT = """\
あなたはYouTube動画の字幕テキストを要約する専門家です。
動画のタイトル（参考）: {video_title}

以下は動画の字幕テキストの一部(パート {part_number}/{total_parts})です。

<transcript_chunk>
{chunk}
</transcript_chunk>

このパートの内容を以下の形式で要約してください:
- 主要なポイントを箇条書きで3〜5個抽出
- 各ポイントは1〜2文で簡潔に、具体的に記述する（「いろいろ」「さまざま」などの曖昧表現は避ける）
- 字幕に書かれている事実・発言に基づき、推測や一般論を混ぜない
- 専門用語はそのまま残す

出力は箇条書きのみにしてください。"""

FINAL_SUMMARY_PROMPT = """\
あなたはYouTube動画の字幕テキストを要約する専門家です。
動画のタイトル（参考）: {video_title}

以下は動画全体の字幕テキストから抽出した各パートの要約です。

<partial_summaries>
{partial_summaries}
</partial_summaries>

上記の部分要約を統合し、以下のJSON形式で最終的な要約を生成してください。
JSONのみを出力し、それ以外のテキストは含めないでください。

{{
  "title": "動画の内容を端的に表す日本語タイトル(20文字以内)",
  "summary": "動画全体の概要を3〜5文で記述した要約文",
  "key_points": [
    {{ "text": "重要ポイント1", "start_seconds": null }},
    {{ "text": "重要ポイント2", "start_seconds": null }}
  ],
  "topics": ["トピック1", "トピック2"]
}}

注意:
- title は動画の核心を捉えた簡潔なものにする
- summary は動画を見ていない人にも内容が伝わるように、具体的に書く。曖昧な表現は避ける
- key_points は3〜7個。各要素は {{ "text": "1文で簡潔に、内容が分かるように", "start_seconds": null }}(部分要約からは時刻が出ないため null)
- topics は動画の主題を表すキーワードを2〜5個。抽象的な単語より、動画で扱っている具体的な語を使う"""

SHORT_TEXT_PROMPT = """\
あなたはYouTube動画の字幕テキストを要約する専門家です。
動画のタイトル（参考）: {video_title}

以下は動画の字幕テキスト全文です。各行は [秒数] の後にその時刻の字幕が続きます。

<transcript>
{transcript}
</transcript>

上記の字幕テキストから、以下のJSON形式で要約を生成してください。
JSONのみを出力し、それ以外のテキストは含めないでください。

{{
  "title": "動画の内容を端的に表す日本語タイトル(20文字以内)",
  "summary": "動画全体の概要を3〜5文で記述した要約文",
  "key_points": [
    {{ "text": "重要ポイント1", "start_seconds": 該当する [秒数] の整数 }},
    {{ "text": "重要ポイント2", "start_seconds": 該当する [秒数] の整数 }}
  ],
  "topics": ["トピック1", "トピック2"]
}}

注意:
- title は動画の核心を捉えた簡潔なものにする
- summary は動画を見ていない人にも内容が伝わるように、具体的に書く。曖昧な表現は避ける
- key_points は3〜7個。各要素は {{ "text": "1文で簡潔に、内容が分かるように", "start_seconds": そのポイントが話されている箇所の [秒数] の整数 }}。該当する秒数が分からない場合は null
- topics は動画の主題を表すキーワードを2〜5個。抽象的な単語より、動画で扱っている具体的な語を使う"""


# --- データクラス ---

@dataclass
class KeyPointItem:
    """キーポイント1件(開始秒数は任意)"""
    text: str
    start_seconds: int | None = None


@dataclass
class SummaryResult:
    """要約結果を格納するデータクラス。"""
    title: str
    summary: str
    key_points: list[KeyPointItem]
    topics: list[str]
    chunk_count: int = 1
    model: str = MODEL_ID


@dataclass
class ChunkInfo:
    """分割されたチャンクの情報。"""
    text: str
    part_number: int
    total_parts: int


# --- メインサービス ---

class SummarizerService:
    """
    Groq API を使って字幕テキストを要約するサービス。

    短いテキストは直接要約し、長いテキストはチャンク分割 → 各チャンク要約 → 統合要約
    のパイプラインで処理する。
    """

    def __init__(
        self,
        api_key: str | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        """
        Args:
            api_key: Groq API キー。未指定時は環境変数 GROQ_API_KEY を使用。
            chunk_size: 1チャンクあたりの最大文字数。
            chunk_overlap: チャンク間のオーバーラップ文字数。
        """
        resolved_key = api_key or os.getenv("GROQ_API_KEY")
        if not resolved_key:
            raise ValueError(
                "APIキーが設定されていません。引数 api_key または環境変数 GROQ_API_KEY を設定してください。"
            )
        self.client = AsyncGroq(api_key=resolved_key)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def summarize_transcript(
        self, transcript: str, video_title: str | None = None
    ) -> SummaryResult:
        """
        字幕テキストを受け取り、構造化された要約を返す。

        短いテキスト(1チャンク以内)は直接要約し、
        長いテキストはチャンク分割パイプラインで処理する。

        Args:
            transcript: YouTube動画の字幕テキスト全文。
            video_title: 動画のタイトル（要約の手がかり。省略可）。

        Returns:
            SummaryResult: 構造化された要約結果。

        Raises:
            groq.APIError: API呼び出しに失敗した場合。
            ValueError: 字幕テキストが空の場合。
        """
        transcript = transcript.strip()
        if not transcript:
            raise ValueError("字幕テキストが空です。")

        title_hint = (video_title or "").strip() or "（取得していません）"
        chunks = self._split_into_chunks(transcript)

        if len(chunks) == 1:
            logger.info("短いテキスト: 直接要約を実行")
            return await self._summarize_short(transcript, video_title=title_hint)
        else:
            logger.info("長いテキスト: %d チャンクに分割して要約", len(chunks))
            return await self._summarize_long(chunks, video_title=title_hint)

    def _split_into_chunks(self, text: str) -> list[ChunkInfo]:
        """テキストをチャンクに分割する。"""
        if len(text) <= self.chunk_size:
            return [ChunkInfo(text=text, part_number=1, total_parts=1)]

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            if end >= len(text):
                chunks.append(text[start:])
                break

            split_pos = self._find_split_position(text, start, end)
            chunks.append(text[start:split_pos])

            start = split_pos - self.chunk_overlap
            if start < 0:
                start = 0

        total = len(chunks)
        return [
            ChunkInfo(text=chunk, part_number=i + 1, total_parts=total)
            for i, chunk in enumerate(chunks)
        ]

    @staticmethod
    def _find_split_position(text: str, start: int, end: int) -> int:
        """自然な区切り位置を探す。"""
        search_start = max(start, end - (end - start) // 5)
        segment = text[search_start:end]

        for delimiter in ["。", "\n\n", "\n", "、", ".", " "]:
            pos = segment.rfind(delimiter)
            if pos != -1:
                return search_start + pos + len(delimiter)

        return end

    async def _summarize_short(
        self, transcript: str, video_title: str = "（取得していません）"
    ) -> SummaryResult:
        """短いテキストを直接要約する。"""
        prompt = SHORT_TEXT_PROMPT.format(
            transcript=transcript,
            video_title=video_title,
        )
        raw = await self._call_api(prompt)
        return self._parse_summary_response(raw, chunk_count=1)

    async def _summarize_long(
        self,
        chunks: list[ChunkInfo],
        video_title: str = "（取得していません）",
    ) -> SummaryResult:
        """長いテキストをチャンク分割パイプラインで要約する。"""
        partial_summaries: list[str] = []
        for chunk in chunks:
            logger.info("チャンク %d/%d を要約中...", chunk.part_number, chunk.total_parts)
            prompt = CHUNK_SUMMARY_PROMPT.format(
                part_number=chunk.part_number,
                total_parts=chunk.total_parts,
                chunk=chunk.text,
                video_title=video_title,
            )
            result = await self._call_api(prompt)
            partial_summaries.append(f"【パート {chunk.part_number}】\n{result}")

        logger.info("部分要約を統合中...")
        combined = "\n\n".join(partial_summaries)
        prompt = FINAL_SUMMARY_PROMPT.format(
            partial_summaries=combined,
            video_title=video_title,
        )
        raw = await self._call_api(prompt)
        return self._parse_summary_response(raw, chunk_count=len(chunks))

    async def _call_api(self, prompt: str) -> str:
        """Groq API を呼び出す。"""
        chat_completion = await self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_ID,
            max_completion_tokens=MAX_OUTPUT_TOKENS,
            temperature=DEFAULT_TEMPERATURE,
        )
        return chat_completion.choices[0].message.content or ""

    @staticmethod
    def _parse_summary_response(raw: str, chunk_count: int) -> SummaryResult:
        """APIレスポンスのJSON文字列をパースして SummaryResult に変換する。"""
        import json

        text = raw.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines[1:] if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("JSONパースに失敗しました。フォールバック値を使用します。")
            return SummaryResult(
                title="要約の生成に部分的に成功",
                summary=raw[:500],
                key_points=[KeyPointItem("要約結果のパースに失敗しました。生テキストを確認してください。")],
                topics=[],
                chunk_count=chunk_count,
            )

        raw_kps = data.get("key_points", [])
        key_points: list[KeyPointItem] = []
        for item in raw_kps:
            if isinstance(item, str):
                key_points.append(KeyPointItem(text=item, start_seconds=None))
            elif isinstance(item, dict):
                text_val = item.get("text", "")
                sec = item.get("start_seconds")
                if sec is not None and not isinstance(sec, int):
                    sec = int(sec) if sec is not None else None
                key_points.append(KeyPointItem(text=text_val, start_seconds=sec))
            else:
                key_points.append(KeyPointItem(text=str(item), start_seconds=None))

        return SummaryResult(
            title=data.get("title", "タイトル不明"),
            summary=data.get("summary", ""),
            key_points=key_points,
            topics=data.get("topics", []),
            chunk_count=chunk_count,
        )
