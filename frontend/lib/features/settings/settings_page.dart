/// 设置页：后端地址、BYOK 会话密钥（仅内存）、配置状态查看与非密项维护。
library;

import 'package:flutter/material.dart';

import '../../app/app_scope.dart';
import '../../shared/api/api_client.dart';
import '../../shared/api/api_models.dart';
import '../../shared/state/app_settings.dart';
import 'config_item_tile.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final _baseUrlController = TextEditingController();
  final _embeddingKeyController = TextEditingController();
  final _llmKeyController = TextEditingController();

  AppSettings? _settings;
  ApiClient? _api;
  List<ConfigItem> _config = [];
  String? _configError;
  bool _obscure = true;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // InheritedWidget 不能在 initState 里读，首次进入时灌入当前值
    if (identical(_settings, AppScope.of(context).settings)) return;
    _settings = AppScope.of(context).settings;
    _api = AppScope.of(context).api;
    _baseUrlController.text = _settings!.baseUrl;
    _embeddingKeyController.text = _settings!.embeddingApiKey;
    _llmKeyController.text = _settings!.llmApiKey;
    _loadConfig();
  }

  Future<void> _loadConfig() async {
    try {
      final config = await _api!.getConfig();
      if (!mounted) return;
      setState(() {
        _config = config;
        _configError = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _configError = '$e');
    }
  }

  void _saveBaseUrl() {
    _settings!.updateBaseUrl(_baseUrlController.text);
    _baseUrlController.text = _settings!.baseUrl;
    _snack('后端地址已保存');
  }

  void _saveSessionKeys() {
    _settings!.updateSessionKeys(
      embedding: _embeddingKeyController.text,
      llm: _llmKeyController.text,
    );
    _snack('会话密钥已保存到内存，应用退出即失效');
  }

  void _snack(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    _embeddingKeyController.dispose();
    _llmKeyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('连接', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        TextField(
          controller: _baseUrlController,
          decoration: const InputDecoration(
            labelText: '后端地址',
            hintText: 'http://192.168.1.5:8000（局域网连 PC 时填 PC 的 IP）',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerLeft,
          child: FilledButton(
            onPressed: _saveBaseUrl,
            child: const Text('保存地址'),
          ),
        ),
        const SizedBox(height: 24),
        Text('会话密钥（BYOK）', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 4),
        Text(
          '仅存内存、随请求头发往后端、退出即失效；要持久化请手动配置 backend/.env 或环境变量。',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _embeddingKeyController,
          obscureText: _obscure,
          decoration: InputDecoration(
            labelText: 'EMBEDDING_API_KEY（本次会话）',
            border: const OutlineInputBorder(),
            suffixIcon: IconButton(
              icon: Icon(_obscure ? Icons.visibility : Icons.visibility_off),
              onPressed: () => setState(() => _obscure = !_obscure),
            ),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _llmKeyController,
          obscureText: _obscure,
          decoration: const InputDecoration(
            labelText: 'LLM_API_KEY（本次会话）',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerLeft,
          child: FilledButton(
            onPressed: _saveSessionKeys,
            child: const Text('保存到本次会话'),
          ),
        ),
        const SizedBox(height: 24),
        Row(
          children: [
            Expanded(
              child: Text(
                '配置状态',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            IconButton(
              tooltip: '刷新',
              onPressed: _loadConfig,
              icon: const Icon(Icons.refresh),
            ),
          ],
        ),
        const SizedBox(height: 8),
        if (_configError != null) Text(_configError!),
        for (final item in _config)
          ConfigItemTile(item: item, api: _api!, onChanged: _loadConfig),
      ],
    );
  }
}
