/// 问答页：基于检索片段的 RAG 问答，回答带 [n] 引用与来源出处。
library;

import 'package:flutter/material.dart';

import '../../app/app_scope.dart';
import '../../shared/api/api_models.dart';
import '../../shared/widgets/section_picker.dart';

class AskPage extends StatefulWidget {
  const AskPage({super.key});

  @override
  State<AskPage> createState() => _AskPageState();
}

class _AskPageState extends State<AskPage> {
  final _questionController = TextEditingController();
  String? _section;
  int _topK = 5;
  bool _busy = false;
  AskAnswer? _answer;
  String? _error;

  @override
  void dispose() {
    _questionController.dispose();
    super.dispose();
  }

  Future<void> _ask() async {
    final question = _questionController.text.trim();
    if (question.isEmpty) {
      setState(() => _error = '请先输入问题');
      return;
    }
    final api = AppScope.of(context).api;
    setState(() {
      _busy = true;
      _error = null;
      _answer = null;
    });
    try {
      final answer = await api.ask(question, topK: _topK, section: _section);
      if (!mounted) return;
      setState(() {
        _answer = answer;
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
          controller: _questionController,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(
            labelText: '向知识库提问',
            hintText: '例如：这份资料里 RAG 的引用是怎么保证真实的？',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            SizedBox(
              width: 120,
              child: DropdownButtonFormField<int>(
                initialValue: _topK,
                decoration: const InputDecoration(
                  labelText: '检索片段数',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 3, child: Text('3')),
                  DropdownMenuItem(value: 5, child: Text('5')),
                  DropdownMenuItem(value: 10, child: Text('10')),
                ],
                onChanged: (v) => setState(() => _topK = v ?? 5),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: SectionPicker(
                value: _section,
                onChanged: (v) => setState(() => _section = v),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: _busy ? null : _ask,
          icon: _busy
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.auto_awesome),
          label: Text(_busy ? '思考中…' : '提问'),
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
        if (_answer != null) ...[
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('回答', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  SelectableText(_answer!.text),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text('引用来源', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          if (_answer!.citations.isEmpty)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(12),
                child: Text('回答没有命中可引用的片段，请确认已导入相关文档'),
              ),
            ),
          for (final c in _answer!.citations) _CitationCard(citation: c),
        ],
      ],
    );
  }
}

class _CitationCard extends StatelessWidget {
  const _CitationCard({required this.citation});

  final Citation citation;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(radius: 14, child: Text('[${citation.marker}]')),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    citation.title,
                    style: Theme.of(context).textTheme.titleSmall,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Text(
                  citation.score.toStringAsFixed(3),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(citation.source, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 4),
            Text(citation.excerpt),
          ],
        ),
      ),
    );
  }
}
