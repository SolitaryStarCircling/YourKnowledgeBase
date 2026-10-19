/// 阅览画面测试：演示文档渲染、AI 引用高亮、分类筛选与文档切换。
library;

import 'package:cybrary/features/read/read_page.dart';
import 'package:cybrary/shared/theme/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// 用暖纸主题包裹，确保 ReadPalette 扩展已注入。
Widget _wrap(Widget child) => MaterialApp(
  theme: buildPaperTheme(),
  home: Scaffold(body: child),
);

void main() {
  testWidgets('渲染正文、AI 引用高亮段与来源徽章', (tester) async {
    await tester.pumpWidget(_wrap(const ReadPage()));
    await tester.pumpAndSettle();

    // 标题出现在文档列表与正文卡两处
    expect(find.text('语义搜索与 RAG 入门笔记'), findsWidgets);
    // 高亮段正文与角标编号
    expect(find.textContaining('不允许模型编造来源'), findsOneWidget);
    expect(find.text('[1]'), findsOneWidget);
    // AI 来源徽章
    expect(find.textContaining('AI 引用'), findsOneWidget);
  });

  testWidgets('分类 chips 筛选文档', (tester) async {
    await tester.pumpWidget(_wrap(const ReadPage()));
    await tester.pumpAndSettle();

    await tester.tap(find.text('灵感'));
    await tester.pumpAndSettle();

    expect(find.text('产品灵感速记'), findsWidgets);
    expect(find.text('语义搜索与 RAG 入门笔记'), findsNothing);
  });

  testWidgets('点击文档列表切换正文', (tester) async {
    await tester.pumpWidget(_wrap(const ReadPage()));
    await tester.pumpAndSettle();

    await tester.tap(find.text('深度学习笔记 · 第 3 章'));
    await tester.pumpAndSettle();

    expect(find.textContaining('反向传播的核心'), findsOneWidget);
    expect(find.text('[2]'), findsOneWidget);
  });
}
