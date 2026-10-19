/// 后端 HTTP 客户端：封装全部接口调用、BYOK 会话头与错误映射。
///
/// 出网只在本类发生；页面层只跟它打交道，不直接 import http。
library;

import 'dart:convert';

import 'package:http/http.dart' as http;

import '../state/app_settings.dart';
import 'api_models.dart';

/// 后端返回的业务错误（400/404/422/503 等），message 取自响应的 detail。
class ApiException implements Exception {
  ApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({required this.settings, http.Client? client})
    : _client = client ?? http.Client();

  final AppSettings settings;
  final http.Client _client;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    // BYOK 会话模式：Key 只随请求头进内存，不落任何文件
    if (settings.embeddingApiKey.isNotEmpty)
      'X-Embedding-Api-Key': settings.embeddingApiKey,
    if (settings.llmApiKey.isNotEmpty) 'X-Llm-Api-Key': settings.llmApiKey,
  };

  Uri _uri(String path) =>
      Uri.parse('${settings.baseUrl.replaceAll(RegExp(r'/+$'), '')}$path');

  // ---------- 文档 ----------

  Future<ImportResult> importDocument(String source, {String? section}) async {
    final json = await _send(
      'POST',
      '/documents/import',
      body: {'source': source, 'section': ?section},
    );
    return ImportResult.fromJson(json);
  }

  // ---------- 查询 ----------

  Future<List<SearchHit>> search(
    String query, {
    int topK = 5,
    String? section,
  }) async {
    final json = await _send(
      'POST',
      '/search',
      body: {'query': query, 'top_k': topK, 'section': ?section},
    );
    return (json['hits'] as List<dynamic>)
        .map((e) => SearchHit.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<AskAnswer> ask(
    String question, {
    int topK = 5,
    String? section,
  }) async {
    final json = await _send(
      'POST',
      '/ask',
      body: {'question': question, 'top_k': topK, 'section': ?section},
    );
    return AskAnswer.fromJson(json);
  }

  // ---------- 板块 ----------

  Future<List<SectionItem>> listSections() async {
    final json = await _send('GET', '/sections');
    return (json as List<dynamic>)
        .map((e) => SectionItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<SectionItem> createSection(
    String name, {
    String description = '',
  }) async {
    final json = await _send(
      'POST',
      '/sections',
      body: {'name': name, 'description': description},
    );
    return SectionItem.fromJson(json);
  }

  Future<SectionItem> updateSection(
    String name, {
    String? newName,
    String? description,
  }) async {
    final json = await _send(
      'PATCH',
      '/sections/${Uri.encodeComponent(name)}',
      body: {'new_name': ?newName, 'description': ?description},
    );
    return SectionItem.fromJson(json);
  }

  Future<void> deleteSection(String name) async {
    await _send('DELETE', '/sections/${Uri.encodeComponent(name)}');
  }

  // ---------- 配置 ----------

  Future<List<ConfigItem>> getConfig() async {
    final json = await _send('GET', '/config');
    return (json as List<dynamic>)
        .map((e) => ConfigItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> setConfig(String name, String value) async {
    await _send('PUT', '/config/$name', body: {'value': value});
  }

  Future<void> clearConfig(String name) async {
    await _send('DELETE', '/config/$name');
  }

  // ---------- 传输层 ----------

  Future<dynamic> _send(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    final uri = _uri(path);
    final payload = body == null ? null : jsonEncode(body);
    late http.Response response;
    switch (method) {
      case 'GET':
        response = await _client.get(uri, headers: _headers);
      case 'POST':
        response = await _client.post(uri, headers: _headers, body: payload);
      case 'PATCH':
        response = await _client.patch(uri, headers: _headers, body: payload);
      case 'PUT':
        response = await _client.put(uri, headers: _headers, body: payload);
      case 'DELETE':
        response = await _client.delete(uri, headers: _headers);
      default:
        throw ArgumentError('不支持的请求方法：$method');
    }
    return _decode(response);
  }

  dynamic _decode(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return null;
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw ApiException(response.statusCode, _extractDetail(response));
  }

  /// 提取后端 detail 文案；解析失败给通用提示，不暴露原始报文。
  String _extractDetail(http.Response response) {
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map<String, dynamic> && decoded['detail'] != null) {
        final detail = decoded['detail'];
        return detail is String ? detail : detail.toString();
      }
    } catch (_) {
      // 非 JSON 响应，落到通用文案
    }
    return '请求失败（HTTP ${response.statusCode}）';
  }
}
