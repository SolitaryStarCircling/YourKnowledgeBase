/// 板块编辑对话框：新建 / 重命名 / 改描述共用，返回填写结果。
library;

import 'package:flutter/material.dart';

class SectionFormResult {
  const SectionFormResult({required this.name, required this.description});

  final String name;
  final String description;
}

/// 弹出编辑表单；取消返回 null。[initialName] 非空即编辑模式。
Future<SectionFormResult?> showSectionEditDialog(
  BuildContext context, {
  String initialName = '',
  String initialDescription = '',
}) {
  return showDialog<SectionFormResult>(
    context: context,
    builder: (_) => _SectionEditDialog(
      initialName: initialName,
      initialDescription: initialDescription,
    ),
  );
}

class _SectionEditDialog extends StatefulWidget {
  const _SectionEditDialog({
    required this.initialName,
    required this.initialDescription,
  });

  final String initialName;
  final String initialDescription;

  @override
  State<_SectionEditDialog> createState() => _SectionEditDialogState();
}

class _SectionEditDialogState extends State<_SectionEditDialog> {
  late final _nameController = TextEditingController(text: widget.initialName);
  late final _descController = TextEditingController(
    text: widget.initialDescription,
  );
  String? _error;

  @override
  void dispose() {
    _nameController.dispose();
    _descController.dispose();
    super.dispose();
  }

  void _submit() {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      setState(() => _error = '板块名称不能为空');
      return;
    }
    Navigator.of(context).pop(
      SectionFormResult(name: name, description: _descController.text.trim()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.initialName.isEmpty ? '新建板块' : '编辑板块'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _nameController,
            autofocus: true,
            decoration: const InputDecoration(
              labelText: '板块名称',
              border: OutlineInputBorder(),
            ),
            onSubmitted: (_) => _submit(),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _descController,
            minLines: 1,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: '描述（可选）',
              border: OutlineInputBorder(),
            ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('取消'),
        ),
        FilledButton(onPressed: _submit, child: const Text('确定')),
      ],
    );
  }
}
