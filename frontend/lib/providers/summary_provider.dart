import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/summary.dart';
import '../services/api_service.dart';

/// APIサービスのプロバイダー
final apiServiceProvider = Provider<ApiService>((ref) {
  final service = ApiService();
  ref.onDispose(() => service.dispose());
  return service;
});

/// 要約の状態を表すクラス
sealed class SummaryState {
  const SummaryState();
}

class SummaryInitial extends SummaryState {
  const SummaryInitial();
}

class SummaryLoading extends SummaryState {
  const SummaryLoading();
}

class SummaryLoaded extends SummaryState {
  final VideoSummary summary;
  const SummaryLoaded(this.summary);
}

class SummaryError extends SummaryState {
  final String message;
  const SummaryError(this.message);
}

/// 要約状態を管理するNotifier
class SummaryNotifier extends StateNotifier<SummaryState> {
  final ApiService _apiService;

  SummaryNotifier(this._apiService) : super(const SummaryInitial());

  /// YouTube URLから要約を取得
  Future<void> summarize(String url) async {
    state = const SummaryLoading();
    try {
      final summary = await _apiService.summarize(url: url);
      state = SummaryLoaded(summary);
    } on ApiException catch (e) {
      state = SummaryError(e.message);
    } catch (e) {
      state = const SummaryError('通信エラーが発生しました。ネットワーク接続を確認してください。');
    }
  }

  /// 状態をリセット
  void reset() {
    state = const SummaryInitial();
  }
}

/// 要約状態のプロバイダー
final summaryProvider =
    StateNotifierProvider<SummaryNotifier, SummaryState>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return SummaryNotifier(apiService);
});
