import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/summary_provider.dart';
import 'summary_screen.dart';

/// ホーム画面: YouTube URLの入力と要約リクエスト
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final _urlController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  /// YouTube URLのバリデーション
  String? _validateUrl(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'URLを入力してください';
    }
    final url = value.trim();
    // YouTube URLの基本的なパターンチェック
    final youtubeRegex = RegExp(
      r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/).+',
    );
    if (!youtubeRegex.hasMatch(url)) {
      return '有効なYouTube URLを入力してください';
    }
    return null;
  }

  /// 要約処理を開始
  Future<void> _onSummarize() async {
    if (!_formKey.currentState!.validate()) return;

    final url = _urlController.text.trim();
    ref.read(summaryProvider.notifier).summarize(url);

    // 要約結果画面へ遷移
    if (mounted) {
      Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => const SummaryScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // アプリアイコン
                  Icon(
                    Icons.smart_display_rounded,
                    size: 72,
                    color: colorScheme.primary,
                  ),
                  const SizedBox(height: 16),

                  // タイトル
                  Text(
                    'YouTube要約',
                    style: textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'YouTube動画のURLを入力すると、AIが内容を要約します',
                    style: textTheme.bodyMedium?.copyWith(
                      color: colorScheme.onSurfaceVariant,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 40),

                  // URL入力フォーム
                  Form(
                    key: _formKey,
                    child: Column(
                      children: [
                        TextFormField(
                          controller: _urlController,
                          validator: _validateUrl,
                          decoration: InputDecoration(
                            hintText: 'https://www.youtube.com/watch?v=...',
                            labelText: 'YouTube URL',
                            prefixIcon: const Icon(Icons.link),
                            suffixIcon: IconButton(
                              icon: const Icon(Icons.clear),
                              onPressed: () => _urlController.clear(),
                            ),
                          ),
                          keyboardType: TextInputType.url,
                          textInputAction: TextInputAction.done,
                          onFieldSubmitted: (_) => _onSummarize(),
                        ),
                        const SizedBox(height: 20),

                        // 要約ボタン
                        SizedBox(
                          width: double.infinity,
                          height: 52,
                          child: FilledButton.icon(
                            onPressed: _onSummarize,
                            icon: const Icon(Icons.auto_awesome),
                            label: const Text(
                              '要約する',
                              style: TextStyle(fontSize: 16),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 48),

                  // 使い方の説明
                  _buildFeatureRow(
                    context,
                    icon: Icons.content_paste,
                    text: 'YouTube URLを貼り付け',
                  ),
                  const SizedBox(height: 12),
                  _buildFeatureRow(
                    context,
                    icon: Icons.summarize,
                    text: 'AIが動画の内容を自動で要約',
                  ),
                  const SizedBox(height: 12),
                  _buildFeatureRow(
                    context,
                    icon: Icons.checklist,
                    text: 'キーポイントを一覧で確認',
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureRow(
    BuildContext context, {
    required IconData icon,
    required String text,
  }) {
    final colorScheme = Theme.of(context).colorScheme;
    return Row(
      children: [
        Icon(icon, size: 20, color: colorScheme.primary),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            text,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: colorScheme.onSurfaceVariant,
                ),
          ),
        ),
      ],
    );
  }
}
