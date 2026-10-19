/// 应用外壳：五个功能页的导航容器。
///
/// 窄屏（手机）用底部导航，宽屏（桌面/Web）用侧边导航栏；
/// IndexedStack 保留各页状态，切换不丢输入与结果。
library;

import 'package:flutter/material.dart';

import '../features/ask/ask_page.dart';
import '../features/import/import_page.dart';
import '../features/read/read_page.dart';
import '../features/search/search_page.dart';
import '../features/sections/sections_page.dart';
import '../features/settings/settings_page.dart';
import '../shared/state/app_settings.dart';
import '../shared/theme/read_palette.dart';
import 'app_scope.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;

  static const _titles = ['阅览', '导入', '搜索', '问答', '板块', '设置'];

  static const _pages = [
    ReadPage(),
    ImportPage(),
    SearchPage(),
    AskPage(),
    SectionsPage(),
    SettingsPage(),
  ];

  static const _destinations = [
    (Icons.menu_book, '阅览'),
    (Icons.upload_file, '导入'),
    (Icons.search, '搜索'),
    (Icons.question_answer, '问答'),
    (Icons.folder, '板块'),
    (Icons.settings, '设置'),
  ];

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 840;
    final settings = AppScope.of(context).settings;
    return Scaffold(
      appBar: AppBar(
        title: Text('YourKnowledgeBase · ${_titles[_index]}'),
        actions: [
          // 模式切换按钮：暖纸书屋（B·亮）⇄ 赛博霓虹（A·暗）
          _ModeToggle(settings: settings),
          const SizedBox(width: 8),
        ],
      ),
      body: Row(
        children: [
          if (wide)
            NavigationRail(
              selectedIndex: _index,
              onDestinationSelected: (i) => setState(() => _index = i),
              labelType: NavigationRailLabelType.all,
              destinations: [
                for (final (icon, label) in _destinations)
                  NavigationRailDestination(
                    icon: Icon(icon),
                    label: Text(label),
                  ),
              ],
            ),
          if (wide) const VerticalDivider(thickness: 1, width: 1),
          Expanded(
            child: IndexedStack(index: _index, children: _pages),
          ),
        ],
      ),
      bottomNavigationBar: wide
          ? null
          : BottomNavigationBar(
              currentIndex: _index,
              onTap: (i) => setState(() => _index = i),
              type: BottomNavigationBarType.fixed,
              items: [
                for (final (icon, label) in _destinations)
                  BottomNavigationBarItem(icon: Icon(icon), label: label),
              ],
            ),
    );
  }
}

/// 模式切换按钮：暖纸书屋（B·亮）⇄ 赛博霓虹（A·暗）。
///
/// 点击调用 `AppSettings.toggleTheme()`，由 main.dart 的 ListenableBuilder 重建主题。
class _ModeToggle extends StatelessWidget {
  const _ModeToggle({required this.settings});
  final AppSettings settings;

  @override
  Widget build(BuildContext context) {
    final palette = ReadPalette.of(context);
    final isDark = settings.isDark;
    // 图标与文案表示"将切换到的目标风格"
    final label = isDark ? '暖纸' : '霓虹';
    final icon = isDark ? Icons.wb_sunny_outlined : Icons.dark_mode_outlined;

    return Tooltip(
      message: '切换风格：暖纸书屋 / 赛博霓虹',
      child: InkWell(
        borderRadius: BorderRadius.circular(999),
        onTap: settings.toggleTheme,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: palette.accent),
            color: palette.accent.withValues(alpha: 0.12),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 18, color: palette.accent),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  color: palette.accent,
                  fontWeight: FontWeight.w600,
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
