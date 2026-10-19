/// 数据模型解析测试：对齐后端 app/api/schemas.py 的字段。
library;

import 'package:cybrary/shared/api/api_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ImportResult', () {
    test('解析导入结果', () {
      final r = ImportResult.fromJson({
        'status': 'created',
        'doc_id': 'doc-1',
        'title': '测试笔记',
        'chunk_count': 3,
      });
      expect(r.status, 'created');
      expect(r.docId, 'doc-1');
      expect(r.title, '测试笔记');
      expect(r.chunkCount, 3);
    });
  });

  group('SearchHit', () {
    test('解析命中片段', () {
      final h = SearchHit.fromJson({
        'chunk_id': 'doc-1#0',
        'doc_id': 'doc-1',
        'index': 0,
        'text': '片段内容',
        'title': '测试笔记',
        'source': 'note.md',
        'score': 0.87,
      });
      expect(h.chunkId, 'doc-1#0');
      expect(h.index, 0);
      expect(h.score, 0.87);
    });
  });

  group('AskAnswer', () {
    test('解析回答与引用', () {
      final a = AskAnswer.fromJson({
        'text': '回答正文 [1]',
        'citations': [
          {
            'marker': 1,
            'chunk_id': 'doc-1#0',
            'doc_id': 'doc-1',
            'title': '测试笔记',
            'source': 'note.md',
            'excerpt': '被引用的片段',
            'score': 0.9,
          },
        ],
      });
      expect(a.text, '回答正文 [1]');
      expect(a.citations, hasLength(1));
      expect(a.citations.single.marker, 1);
      expect(a.citations.single.excerpt, '被引用的片段');
    });

    test('无引用时返回空列表', () {
      final a = AskAnswer.fromJson({'text': '答', 'citations': []});
      expect(a.citations, isEmpty);
    });
  });

  group('SectionItem / ConfigItem', () {
    test('解析板块', () {
      final s = SectionItem.fromJson({
        'section_id': 'sec-1',
        'name': '技术',
        'description': '技术笔记',
      });
      expect(s.sectionId, 'sec-1');
      expect(s.name, '技术');
    });

    test('解析配置状态（脱敏值原样保留）', () {
      final c = ConfigItem.fromJson({
        'name': 'LLM_API_KEY',
        'source': 'session',
        'display_value': 'sk-****1234',
      });
      expect(c.name, 'LLM_API_KEY');
      expect(c.source, 'session');
      expect(c.displayValue, 'sk-****1234');
    });
  });
}
