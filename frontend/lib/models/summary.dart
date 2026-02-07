/// キーポイント1件（任意で開始秒数付き）
class KeyPointItem {
  final String text;
  final int? startSeconds;

  const KeyPointItem({required this.text, this.startSeconds});

  /// 「MM:SS」形式の時刻（startSeconds がない場合は null）
  String? get formattedTime {
    if (startSeconds == null) return null;
    final m = startSeconds! ~/ 60;
    final s = startSeconds! % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }
}

/// YouTube動画の要約データモデル
class VideoSummary {
  final String videoId;
  final String title;
  final String summaryTitle;
  final List<KeyPointItem> keyPoints;
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
  /// key_points は [ "文字列" ] または [ { "text": "...", "start_seconds": 123 } ] の両方に対応
  factory VideoSummary.fromJson(Map<String, dynamic> json) {
    final rawKeyPoints = json['key_points'] as List<dynamic>? ?? [];
    final keyPoints = rawKeyPoints.map<KeyPointItem>((e) {
      if (e is String) return KeyPointItem(text: e);
      final m = e as Map<String, dynamic>;
      final sec = m['start_seconds'];
      return KeyPointItem(
        text: m['text'] as String? ?? '',
        startSeconds: sec is int ? sec : (sec != null ? int.tryParse(sec.toString()) : null),
      );
    }).toList();

    // video_title: YouTubeの動画タイトル（取得できた場合）。なければAI要約タイトルにフォールバック
    final videoTitle = json['video_title'] as String?;
    final aiTitle = json['title'] as String? ?? '';
    return VideoSummary(
      videoId: json['video_id'] as String,
      title: (videoTitle != null && videoTitle.isNotEmpty) ? videoTitle : aiTitle,
      summaryTitle: aiTitle,
      keyPoints: keyPoints,
      detailedSummary: json['summary'] as String,
      topics: List<String>.from(json['topics'] as List? ?? []),
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

  /// 動画の再生URL（オプションで開始秒数）
  String videoUrl([int? startAtSeconds]) {
    final base = 'https://www.youtube.com/watch?v=$videoId';
    if (startAtSeconds != null && startAtSeconds > 0) {
      return '$base&t=$startAtSeconds';
    }
    return base;
  }
}
