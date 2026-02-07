/// YouTube動画の要約データモデル
class VideoSummary {
  final String videoId;
  final String title;
  final String summaryTitle;
  final List<String> keyPoints;
  final String detailedSummary;
  final List<String> topics;
  final int? durationSeconds;

  const VideoSummary({
    required this.videoId,
    required this.title,
    required this.summaryTitle,
    required this.keyPoints,
    required this.detailedSummary,
    required this.topics,
    this.durationSeconds,
  });

  /// JSONからモデルを生成
  /// バックエンドのレスポンス形式:
  /// { "video_id", "title", "summary" (string), "key_points", "topics", "language", "transcript_length" }
  factory VideoSummary.fromJson(Map<String, dynamic> json) {
    return VideoSummary(
      videoId: json['video_id'] as String,
      title: json['title'] as String,
      summaryTitle: json['title'] as String,
      keyPoints: List<String>.from(json['key_points'] as List),
      detailedSummary: json['summary'] as String,
      topics: List<String>.from(json['topics'] as List),
      durationSeconds: json['duration_seconds'] as int?,
    );
  }

  /// 動画の長さを「MM:SS」形式で返す
  String get formattedDuration {
    final dur = durationSeconds;
    if (dur == null) return '--:--';
    final minutes = dur ~/ 60;
    final seconds = dur % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  /// YouTubeのサムネイルURLを取得
  String get thumbnailUrl =>
      'https://img.youtube.com/vi/$videoId/hqdefault.jpg';
}
