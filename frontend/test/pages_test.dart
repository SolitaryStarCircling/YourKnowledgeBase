/// 页面交互测试：MockClient 假后端，验证导入 / 搜索 / 问答 / 板块主流程。
library;

import 'dart:convert';

import 'package:cybrary/app/app_scope.dart';
import 'package:cybrary/features/ask/ask_page.dart';
import 'package:cybrary/features/import/import_page.dart';
import 'package:cybrary/features/search/search_page.dart';
import 'package:cybrary/features/sections/sections_page.dart';
import 'package:cybrary/shared/api/api_client.dart';
import 'package:cybrary/shared/state/app_settings.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

ApiClient _client(MockClient mock) =>
    ApiClient(settings: AppSettings(), client: mock);

Widget _wrap(Widget child, ApiClient api) => AppScope(
  settings: AppSettings(),
  api: api,
  child: MaterialApp(home: Scaffold(body: child)),
);

http.Response _json(Object data) =>
    http.Response.bytes(utf8.encode(jsonEncode(data)), 200);

/// 空板块列表响应，SectionPicker 会请求它
http.Response _sections() => _json([]);

void main() {
  testWidgets('导入页提交后展示导入结果', (tester) async {
    final api = _client(
      MockClient((request) async {
        if (request.url.path == '/sections') return _sections();
        return _json({
          'status': 'created',
          'doc_id': 'doc-1',
          'title': '测试笔记',
          'chunk_count': 2,
        });
      }),
    );
    await tester.pumpWidget(_wrap(const ImportPage(), api));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), r'D:\notes\a.md');
    await tester.tap(find.text('导入'));
    await tester.pumpAndSettle();

    expect(find.textContaining('测试笔记'), findsWidgets);
    expect(find.text('分块数：2'), findsOneWidget);
  });

  testWidgets('搜索页展示命中片段与来源', (tester) async {
    final api = _client(
      MockClient((request) async {
        if (request.url.path == '/sections') return _sections();
        return _json({
          'hits': [
            {
              'chunk_id': 'c1',
              'doc_id': 'd1',
              'index': 0,
              'text': '命中的片段内容',
              'title': '测试笔记',
              'source': 'note.md',
              'score': 0.812,
            },
          ],
        });
      }),
    );
    await tester.pumpWidget(_wrap(const SearchPage(), api));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), '怎么选型');
    await tester.tap(find.text('语义搜索'));
    await tester.pumpAndSettle();

    expect(find.text('命中的片段内容'), findsOneWidget);
    expect(find.textContaining('note.md'), findsOneWidget);
    expect(find.textContaining('0.812'), findsOneWidget);
  });

  testWidgets('问答页展示回答与引用来源', (tester) async {
    final api = _client(
      MockClient((request) async {
        if (request.url.path == '/sections') return _sections();
        return _json({
          'text': '这是回答正文 [1]',
          'citations': [
            {
              'marker': 1,
              'chunk_id': 'c1',
              'doc_id': 'd1',
              'title': '测试笔记',
              'source': 'note.md',
              'excerpt': '被引用的片段',
              'score': 0.9,
            },
          ],
        });
      }),
    );
    await tester.pumpWidget(_wrap(const AskPage(), api));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), '为什么');
    await tester.tap(find.text('提问'));
    await tester.pumpAndSettle();

    expect(find.text('这是回答正文 [1]'), findsOneWidget);
    expect(find.text('[1]'), findsOneWidget);
    expect(find.text('被引用的片段'), findsOneWidget);
  });

  testWidgets('板块页新建板块后出现在列表', (tester) async {
    final sections = <Map<String, dynamic>>[];
    final api = _client(
      MockClient((request) async {
        if (request.method == 'POST') {
          final body = jsonDecode(
            utf8.decode(request.bodyBytes),
          ) as Map<String, dynamic>;
          sections.add({
            'section_id': 's${sections.length}',
            'name': body['name'],
            'description': body['description'] ?? '',
          });
          return _json(sections.last);
        }
        return _json(sections);
      }),
    );
    await tester.pumpWidget(_wrap(const SectionsPage(), api));
    await tester.pumpAndSettle();

    expect(find.text('还没有板块，点右下角新建一个'), findsOneWidget);

    await tester.tap(find.text('新建板块'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).first, '技术');
    await tester.tap(find.text('确定'));
    await tester.pumpAndSettle();

    expect(find.text('技术'), findsOneWidget);
  });
}
