/// API 客户端测试：全部走 MockClient，不发真实请求、不花 API 钱。
library;

import 'dart:convert';

import 'package:cybrary/shared/api/api_client.dart';
import 'package:cybrary/shared/state/app_settings.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

ApiClient _client(AppSettings settings, MockClient mock) =>
    ApiClient(settings: settings, client: mock);

void main() {
  group('请求头与会话密钥', () {
    test('会话密钥随请求头发送，空则不带', () async {
      final settings = AppSettings()
        ..updateSessionKeys(embedding: 'emb-key', llm: 'llm-key');
      http.Request? seen;
      final api = _client(
        settings,
        MockClient((request) async {
          seen = request;
          return http.Response.bytes(utf8.encode('[]'), 200);
        }),
      );
      await api.listSections();
      expect(seen!.headers['X-Embedding-Api-Key'], 'emb-key');
      expect(seen!.headers['X-Llm-Api-Key'], 'llm-key');

      final bare = AppSettings();
      final bareApi = _client(
        bare,
        MockClient((request) async {
          seen = request;
          return http.Response.bytes(utf8.encode('[]'), 200);
        }),
      );
      await bareApi.listSections();
      expect(seen!.headers.containsKey('X-Embedding-Api-Key'), isFalse);
    });
  });

  group('文档与查询', () {
    test('importDocument 解析结果并带上板块', () async {
      final settings = AppSettings();
      Map<String, dynamic>? body;
      final api = _client(
        settings,
        MockClient((request) async {
          body = jsonDecode(
            utf8.decode(request.bodyBytes),
          ) as Map<String, dynamic>;
          return http.Response.bytes(
            utf8.encode(
              jsonEncode({
                'status': 'created',
                'doc_id': 'doc-1',
                'title': '测试笔记',
                'chunk_count': 2,
              }),
            ),
            200,
          );
        }),
      );
      final r = await api.importDocument(r'D:\notes\a.md', section: '技术');
      expect(body!['source'], r'D:\notes\a.md');
      expect(body!['section'], '技术');
      expect(r.status, 'created');
      expect(r.chunkCount, 2);
    });

    test('search 与 ask 解析响应', () async {
      final settings = AppSettings();
      var asked = false;
      final api = _client(
        settings,
        MockClient((request) async {
          if (request.url.path == '/search') {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'hits': [
                    {
                      'chunk_id': 'c1',
                      'doc_id': 'd1',
                      'index': 0,
                      'text': 't',
                      'title': 'ti',
                      'source': 's',
                      'score': 0.5,
                    },
                  ],
                }),
              ),
              200,
            );
          }
          asked = true;
          return http.Response.bytes(
            utf8.encode(
              jsonEncode({
                'text': '答案 [1]',
                'citations': [
                  {
                    'marker': 1,
                    'chunk_id': 'c1',
                    'doc_id': 'd1',
                    'title': 'ti',
                    'source': 's',
                    'excerpt': 'e',
                    'score': 0.5,
                  },
                ],
              }),
            ),
            200,
          );
        }),
      );
      final hits = await api.search('怎么选型', topK: 3);
      expect(hits.single.score, 0.5);
      final answer = await api.ask('为什么');
      expect(asked, isTrue);
      expect(answer.citations.single.marker, 1);
    });
  });

  group('错误映射', () {
    test('非 2xx 抛 ApiException 并取 detail 文案', () async {
      final api = _client(
        AppSettings(),
        MockClient(
          (_) async => http.Response.bytes(
            utf8.encode(jsonEncode({'detail': '板块不存在'})),
            404,
          ),
        ),
      );
      expect(
        () => api.deleteSection('不存在'),
        throwsA(
          isA<ApiException>()
              .having((e) => e.statusCode, 'statusCode', 404)
              .having((e) => e.message, 'message', '板块不存在'),
        ),
      );
    });

    test('非 JSON 错误响应给通用文案', () async {
      final api = _client(
        AppSettings(),
        MockClient((_) async => http.Response.bytes(utf8.encode('oops'), 500)),
      );
      expect(
        () => api.getConfig(),
        throwsA(
          isA<ApiException>().having(
            (e) => e.message,
            'message',
            contains('HTTP 500'),
          ),
        ),
      );
    });
  });

  group('配置', () {
    test('setConfig 发送 value，clearConfig 走 DELETE', () async {
      http.Request? seen;
      final api = _client(
        AppSettings(),
        MockClient((request) async {
          seen = request;
          if (request.method == 'DELETE') {
            return http.Response.bytes(const [], 204);
          }
          return http.Response.bytes(
            utf8.encode(jsonEncode({'name': 'LLM_MODEL'})),
            200,
          );
        }),
      );
      await api.setConfig('LLM_MODEL', 'gpt-x');
      expect(seen!.method, 'PUT');
      expect(utf8.decode(seen!.bodyBytes), contains('gpt-x'));

      await api.clearConfig('LLM_MODEL');
      expect(seen!.method, 'DELETE');
    });
  });
}
