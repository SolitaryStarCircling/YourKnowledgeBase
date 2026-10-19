/// 配置项卡片：展示来源与脱敏值；非密项支持写入 / 清除，密钥项禁止落盘。
library;

import 'package:flutter/material.dart';

import '../../shared/api/api_client.dart';
import '../../shared/api/api_models.dart';

/// 配置来源的中文标签
const sourceLabels = {
  'session': '本次会话',
  'env': '环境变量',
  'file': '.env 文件',
  'default': '默认值',
  'missing': '未设置',
};

/// 与后端 is_secret_var 保持一致：*_API_KEY 是密钥
bool isSecretVar(String name) => name.trim().toUpperCase().endsWith('_API_KEY');

class ConfigItemTile extends StatelessWidget {
  const ConfigItemTile({
    super.key,
    required this.item,
    required this.api,
    required this.onChanged,
  });

  final ConfigItem item;
  final ApiClient api;

  /// 写入 / 清除成功后的回调，用于刷新列表
  final VoidCallback onChanged;

  Future<void> _edit(BuildContext context) async {
    final initial = item.displayValue == '（未设置）' ? '' : item.displayValue;
    final value = await showDialog<String>(
      context: context,
      builder: (_) => _EditValueDialog(name: item.name, initial: initial),
    );
    if (value == null || !context.mounted) return;
    try {
      await api.setConfig(item.name, value);
      onChanged();
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _clear(BuildContext context) async {
    try {
      await api.clearConfig(item.name);
      onChanged();
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final secret = isSecretVar(item.name);
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(item.name),
        subtitle: Text(
          '${sourceLabels[item.source] ?? item.source} · ${item.displayValue}',
        ),
        trailing: secret
            ? const Chip(label: Text('密钥不落盘'))
            : Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: const Icon(Icons.edit),
                    tooltip: '修改',
                    onPressed: () => _edit(context),
                  ),
                  IconButton(
                    icon: const Icon(Icons.delete_outline),
                    tooltip: '清除',
                    onPressed: () => _clear(context),
                  ),
                ],
              ),
      ),
    );
  }
}

class _EditValueDialog extends StatefulWidget {
  const _EditValueDialog({required this.name, required this.initial});

  final String name;
  final String initial;

  @override
  State<_EditValueDialog> createState() => _EditValueDialogState();
}

class _EditValueDialogState extends State<_EditValueDialog> {
  late final _controller = TextEditingController(text: widget.initial);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('修改 ${widget.name}'),
      content: TextField(
        controller: _controller,
        autofocus: true,
        decoration: const InputDecoration(border: OutlineInputBorder()),
        onSubmitted: (v) => Navigator.of(context).pop(v.trim()),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('取消'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(_controller.text.trim()),
          child: const Text('保存'),
        ),
      ],
    );
  }
}
