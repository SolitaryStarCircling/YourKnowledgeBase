/// 阅览画面：搜索框 + 分类 chips + 阅读区（文档切换 / 正文 / AI 引用高亮）。
///
/// 配色全部取自 `ReadPalette.of(context)`，A 赛博霓虹 / B 暖纸书屋只换色、组件复用。
library;

import 'package:flutter/material.dart';

import '../../shared/theme/read_palette.dart';
import 'read_demo.dart';
import 'read_view.dart';

class ReadPage extends StatefulWidget {
  const ReadPage({super.key});

  @override
  State<ReadPage> createState() => _ReadPageState();
}

class _ReadPageState extends State<ReadPage> {
  String _category = '全部';
  int _docIndex = 0;

  static const _categories = ['全部', '读书笔记', '技术', '灵感'];

  List<ReadDoc> get _visible => [
        for (final d in demoDocs)
          if (_category == '全部' || d.category == _category) d,
      ];

  @override
  Widget build(BuildContext context) {
    final palette = ReadPalette.of(context);
    final docs = _visible;
    final doc = docs.isEmpty ? null : docs[_docIndex.clamp(0, docs.length - 1)];

    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [palette.backgroundTop, palette.backgroundBottom],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _SearchBar(palette: palette),
          _CategoryChips(
            categories: _categories,
            selected: _category,
            palette: palette,
            onSelected: (c) => setState(() {
              _category = c;
              _docIndex = 0;
            }),
          ),
          Expanded(
            child: doc == null
                ? Center(
                    child: Text(
                      '该分类下暂无文档',
                      style: TextStyle(color: palette.textSecondary),
                    ),
                  )
                : ReadingArea(
                    doc: doc,
                    docs: docs,
                    palette: palette,
                    onSelect: (i) => setState(() => _docIndex = i),
                  ),
          ),
        ],
      ),
    );
  }
}

/// 顶部搜索框：搜索知识库、文档或提问。
class _SearchBar extends StatelessWidget {
  const _SearchBar({required this.palette});
  final ReadPalette palette;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: TextField(
        decoration: InputDecoration(
          hintText: '搜索知识库、文档或提问…',
          prefixIcon: Icon(Icons.search, color: palette.textSecondary),
          filled: true,
          fillColor: palette.inputBg,
          contentPadding: const EdgeInsets.symmetric(vertical: 12),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide(color: palette.inputBorder),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide(color: palette.inputBorder),
          ),
        ),
      ),
    );
  }
}

/// 分类 chips：全部 / 读书笔记 / 技术 / 灵感。
class _CategoryChips extends StatelessWidget {
  const _CategoryChips({
    required this.categories,
    required this.selected,
    required this.palette,
    required this.onSelected,
  });
  final List<String> categories;
  final String selected;
  final ReadPalette palette;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          for (final c in categories)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: ChoiceChip(
                label: Text(c),
                selected: c == selected,
                onSelected: (_) => onSelected(c),
                selectedColor: palette.accent.withValues(alpha: 0.18),
                labelStyle: TextStyle(
                  color: c == selected ? palette.accent : palette.textSecondary,
                  fontWeight: c == selected ? FontWeight.w600 : FontWeight.normal,
                ),
                side: BorderSide(
                  color: c == selected ? palette.accent : palette.chipBorder,
                ),
                backgroundColor: Colors.transparent,
              ),
            ),
        ],
      ),
    );
  }
}
