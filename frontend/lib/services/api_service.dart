import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/summary.dart';

/// バックエンドAPIとの通信を担当するサービス
class ApiService {
  // バックエンドのベースURL（開発環境）
  static const String _baseUrl = 'http://localhost:8000';

  final http.Client _client;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  /// YouTube URLを送信して要約を取得する
  Future<VideoSummary> summarize({
    required String url,
    String language = 'ja',
  }) async {
    final response = await _client.post(
      Uri.parse('$_baseUrl/api/summarize'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'url': url,
        'language': language,
      }),
    );

    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return VideoSummary.fromJson(json);
    } else {
      final errorBody = jsonDecode(response.body) as Map<String, dynamic>;
      final detail = errorBody['detail'];
      final String message = _extractErrorMessage(detail);
      throw ApiException(message: message, statusCode: response.statusCode);
    }
  }

  /// バックエンドの detail が文字列・オブジェクト・配列のどれでもメッセージを抽出
  static String _extractErrorMessage(dynamic detail) {
    if (detail == null) return '要約の取得に失敗しました';
    if (detail is String) return detail;
    if (detail is Map<String, dynamic>) {
      final msg = detail['detail'] ?? detail['message'];
      if (msg is String) return msg;
    }
    // 422 バリデーションエラーなどで detail が配列の場合
    if (detail is List && detail.isNotEmpty) {
      final first = detail.first;
      if (first is Map<String, dynamic>) {
        final msg = first['msg'] ?? first['message'];
        if (msg is String) return msg;
      }
    }
    return '要約の取得に失敗しました';
  }

  void dispose() {
    _client.close();
  }
}

/// API通信時のエラー
class ApiException implements Exception {
  final String message;
  final int statusCode;

  const ApiException({required this.message, required this.statusCode});

  @override
  String toString() => 'ApiException($statusCode): $message';
}
