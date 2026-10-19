/// 运行时设置：后端地址 + BYOK 会话密钥。
///
/// 密钥只存内存（会话模式），应用退出即失效——与后端安全红线一致，
/// 持久化的密钥配置请用后端 `.env` / 环境变量模式。
library;

import 'package:flutter/foundation.dart';

class AppSettings extends ChangeNotifier {
  String baseUrl = 'http://localhost:8000';
  String embeddingApiKey = '';
  String llmApiKey = '';

  /// 界面模式：false=暖纸书屋（B·亮色），true=赛博霓虹（A·暗色）。
  /// 只存布尔，映射到 ThemeMode 由 main.dart 处理，保持本类零 UI 依赖。
  bool isDark = false;

  /// 板块列表变更标记：板块 CRUD 时 +1，SectionPicker 监听它来刷新下拉
  int sectionsVersion = 0;

  /// 切换阅览/界面风格（模式切换按钮）。
  void toggleTheme() {
    isDark = !isDark;
    notifyListeners();
  }

  void updateBaseUrl(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty || trimmed == baseUrl) return;
    baseUrl = trimmed;
    notifyListeners();
  }

  void updateSessionKeys({String? embedding, String? llm}) {
    if (embedding != null) embeddingApiKey = embedding.trim();
    if (llm != null) llmApiKey = llm.trim();
    notifyListeners();
  }

  void bumpSections() {
    sectionsVersion++;
    notifyListeners();
  }
}
