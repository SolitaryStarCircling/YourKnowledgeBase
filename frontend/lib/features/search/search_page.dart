/// 搜索页：对知识库做语义检索，展示命中片段、来源与相似度。
library;

import 'package:flutter/material.dart';

import '../../app/app_scope.dart';
import '../../shared/api/api_models.dart';
import '../../shared/widgets/section_picker.dart';

class SearchPage extends StatefulWidget {
  const SearchPage({super.key});

  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  final _queryController = TextEditingController();
  String? _section;
  int _topK = 5;
  bool _busy = false;
  bool _searched = false;
  List<SearchHit> _hits = [];
  String? _error;

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final query = _queryController.text.trim();
    if (query.isEmpty) {
      setState(() => _error = '请先输入搜索内容');
      return;
    }
    final api = AppScope.of(context).api;
    setState(() {
      _busy = true;
      _error = null;
      _searched = false;
    });
    try {
      final hits = await api.search(query, topK: _topK, section: _section);
      if (!mounted) return;
      setState(() {
        _hits = hits;
        _searched = true;
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
          controller: _queryController,
          decoration: const InputDecoration(
            labelText: '想查什么',
            hintText: '例如：向量数据库怎么选型',
            border: OutlineInputBorder(),
          ),
          onSubmitted: (_) => _search(),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            SizedBox(
              width: 120,
              child: DropdownButtonFormField<int>(
                initialValue: _topK,
                decoration: const InputDecoration(
                  labelText: '返回条数',
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
          onPressed: _busy ? null : _search,
          icon: _busy
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.search),
          label: Text(_busy ? '检索中…' : '语义搜索'),
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
        if (_searched && _hits.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text('没有命中任何片段，换个说法或先导入一些文档'),
            ),
          ),
        for (final hit in _hits) _HitCard(hit: hit),
      ],
    );
  }
}

class _HitCard extends StatelessWidget {
  const _HitCard({required this.hit});

  final SearchHit hit;

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
                Expanded(
                  child: Text(
                    hit.title,
                    style: Theme.of(context).textTheme.titleSmall,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Chip(
                  label: Text('相似度 ${hit.score.toStringAsFixed(3)}'),
                  visualDensity: VisualDensity.compact,
                ),
              ],
            ),
            Text(
              '${hit.source} · 片段 #${hit.index}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 6),
            Text(hit.text),
          ],
        ),
      ),
    );
  }
}
