/// 个人 AI 知识库客户端入口：组装 AppSettings + ApiClient，挂到 AppScope。
library;

import 'package:flutter/material.dart';

import 'app/app_scope.dart';
import 'app/home_shell.dart';
import 'shared/api/api_client.dart';
import 'shared/state/app_settings.dart';
import 'shared/theme/app_theme.dart';

void main() {
  runApp(const CybraryApp());
}

class CybraryApp extends StatefulWidget {
  const CybraryApp({super.key});

  @override
  State<CybraryApp> createState() => _CybraryAppState();
}

class _CybraryAppState extends State<CybraryApp> {
  // 只建一次、全应用复用；会话密钥随 AppSettings 仅存内存
  final _settings = AppSettings();
  late final ApiClient _api = ApiClient(settings: _settings);

  @override
  Widget build(BuildContext context) {
    return AppScope(
      settings: _settings,
      api: _api,
      // 监听主题切换：模式按钮 toggleTheme 后重建 MaterialApp
      child: ListenableBuilder(
        listenable: _settings,
        builder: (context, _) {
          return MaterialApp(
            title: 'YourKnowledgeBase',
            debugShowCheckedModeBanner: false,
            theme: buildPaperTheme(),
            darkTheme: buildNeonTheme(),
            themeMode: _settings.isDark ? ThemeMode.dark : ThemeMode.light,
            home: const HomeShell(),
          );
        },
      ),
    );
  }
}
