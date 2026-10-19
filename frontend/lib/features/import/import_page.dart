/// 导入页：填本地文件路径或网页 URL，可选板块，导入知识库。
library;

import 'package:flutter/material.dart';

import '../../app/app_scope.dart';
import '../../shared/api/api_models.dart';
import '../../shared/widgets/section_picker.dart';

/// 后端增量状态的中文标签
const _statusLabels = {
  'created': '新建',
  'updated': '更新（内容有变化）',
  'skipped': '跳过（内容无变化）',
};

class ImportPage extends StatefulWidget {
  const ImportPage({super.key});

  @override
  State<ImportPage> createState() => _ImportPageState();
}

class _ImportPageState extends State<ImportPage> {
  final _sourceController = TextEditingController();
  String? _section;
  bool _busy = false;
  ImportResult? _result;
  String? _error;

  @override
  void dispose() {
    _sourceController.dispose();
    super.dispose();
  }

  Future<void> _import() async {
    final source = _sourceController.text.trim();
    if (source.isEmpty) {
      setState(() => _error = '请先填写文件路径或网页 URL');
      return;
    }
    final api = AppScope.of(context).api;
    setState(() {
      _busy = true;
      _error = null;
      _result = null;
    });
    try {
      final result = await api.importDocument(source, section: _section);
      if (!mounted) return;
      setState(() {
        _result = result;
        _busy = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = '$e';
        _busy = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        TextField(
          controller: _sourceController,
          decoration: const InputDecoration(
            labelText: '文件路径或网页 URL',
            hintText: r'D:\notes\ai.md 或 https://example.com/post',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        SectionPicker(
          value: _section,
          label: '所属板块（可选）',
          onChanged: (v) => setState(() => _section = v),
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: _busy ? null : _import,
          icon: _busy
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.upload_file),
          label: Text(_busy ? '导入中…' : '导入'),
        ),
        const SizedBox(height: 16),
        if (_error != null)
          Card(
            color: Theme.of(context).colorScheme.errorContainer,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Text(
                _error!,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onErrorContainer,
                ),
              ),
            ),
          ),
        if (_result != null) _ResultCard(result: _result!),
      ],
    );
  }
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});

  final ImportResult result;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('导入结果', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text('状态：${_statusLabels[result.status] ?? result.status}'),
            Text('标题：${result.title}'),
            Text('文档 ID：${result.docId}'),
            Text('分块数：${result.chunkCount}'),
          ],
        ),
      ),
    );
  }
}
