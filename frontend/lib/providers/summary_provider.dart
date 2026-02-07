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

/// 要約履歴を管理するNotifier（メモリ上に保持、アプリ終了で消える）
class SummaryHistoryNotifier extends StateNotifier<List<VideoSummary>> {
  SummaryHistoryNotifier() : super([]);

  void add(VideoSummary summary) {
    state = [summary, ...state];
  }

  void removeAt(int index) {
    state = [...state]..removeAt(index);
  }

  void clear() {
    state = [];
  }
}

final summaryHistoryProvider =
    StateNotifierProvider<SummaryHistoryNotifier, List<VideoSummary>>((ref) {
  return SummaryHistoryNotifier();
});

/// YouTube URL から動画ID（11文字）を抽出
String? _extractVideoId(String url) {
  final trimmed = url.trim();
  final patterns = [
    RegExp(r'[?&]v=([\w-]{11})'),
    RegExp(r'youtu\.be/([\w-]{11})'),
    RegExp(r'shorts/([\w-]{11})'),
  ];
  for (final p in patterns) {
    final m = p.firstMatch(trimmed);
    if (m != null) return m.group(1);
  }
  return null;
}

/// 要約状態を管理するNotifier
class SummaryNotifier extends StateNotifier<SummaryState> {
  final ApiService _apiService;
  final SummaryHistoryNotifier _history;

  SummaryNotifier(this._apiService, this._history) : super(const SummaryInitial());

  /// YouTube URLから要約を取得（履歴に同じ動画があればAPIは呼ばず表示する）
  Future<void> summarize(String url) async {
    final videoId = _extractVideoId(url);
    if (videoId != null) {
      final existingList = _history.state.where((s) => s.videoId == videoId).toList();
      if (existingList.isNotEmpty) {
        state = SummaryLoaded(existingList.first);
        return;
      }
    }

    state = const SummaryLoading();
    try {
      final summary = await _apiService.summarize(url: url);
      state = SummaryLoaded(summary);
      _history.add(summary);
    } on ApiException catch (e) {
      state = SummaryError(e.message);
    } catch (e) {
      state = const SummaryError('通信エラーが発生しました。ネットワーク接続を確認してください。');
    }
  }

  /// 履歴から要約を表示
  void loadFromHistory(VideoSummary summary) {
    state = SummaryLoaded(summary);
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
  final history = ref.watch(summaryHistoryProvider.notifier);
  return SummaryNotifier(apiService, history);
});
