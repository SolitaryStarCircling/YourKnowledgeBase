/// 阅览画面的阅读区组件：文档列表/切换 + 正文卡 + AI 引用高亮段与来源徽章。
///
/// 配色全部取自 [ReadPalette]，A 赛博霓虹 / B 暖纸书屋只换色、组件复用。
library;

import 'package:flutter/material.dart';

import '../../shared/theme/read_palette.dart';
import 'read_demo.dart';

/// 阅读区：宽屏左文档列表 + 右正文卡；窄屏顶部下拉切换 + 正文卡。
class ReadingArea extends StatelessWidget {
  const ReadingArea({
    super.key,
    required this.doc,
    required this.docs,
    required this.palette,
    required this.onSelect,
  });
  final ReadDoc doc;
  final List<ReadDoc> docs;
  final ReadPalette palette;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 720;
    final body = DocBody(doc: doc, palette: palette);

    if (!wide) {
      return ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _DocSwitcher(docs: docs, doc: doc, palette: palette, onSelect: onSelect),
          const SizedBox(height: 12),
          body,
        ],
      );
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 240,
          child: _DocList(docs: docs, doc: doc, palette: palette, onSelect: onSelect),
        ),
        const VerticalDivider(thickness: 1, width: 1),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [body],
          ),
        ),
      ],
    );
  }
}

/// 窄屏文档切换：下拉选择。
class _DocSwitcher extends StatelessWidget {
  const _DocSwitcher({
    required this.docs,
    required this.doc,
    required this.palette,
    required this.onSelect,
  });
  final List<ReadDoc> docs;
  final ReadDoc doc;
  final ReadPalette palette;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<int>(
      initialValue: docs.indexOf(doc),
      decoration: InputDecoration(
        filled: true,
        fillColor: palette.inputBg,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: palette.inputBorder),
        ),
      ),
      items: [
        for (var i = 0; i < docs.length; i++)
          DropdownMenuItem(value: i, child: Text(docs[i].title, overflow: TextOverflow.ellipsis)),
      ],
      onChanged: (v) {
        if (v != null) onSelect(v);
      },
    );
  }
}

/// 宽屏文档列表：点击切换。
class _DocList extends StatelessWidget {
  const _DocList({
    required this.docs,
    required this.doc,
    required this.palette,
    required this.onSelect,
  });
  final List<ReadDoc> docs;
  final ReadDoc doc;
  final ReadPalette palette;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      itemCount: docs.length,
      itemBuilder: (context, i) {
        final d = docs[i];
        final active = d == doc;
        return InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () => onSelect(i),
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 4),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: active ? palette.accent.withValues(alpha: 0.14) : Colors.transparent,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: active ? palette.accent : palette.surfaceBorder),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  d.title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: palette.textPrimary,
                    fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${d.category} · ${d.time}',
                  style: TextStyle(color: palette.textSecondary, fontSize: 12),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// 正文卡：标题 + meta + 正文（含高亮引用段）+ AI 来源徽章。
class DocBody extends StatelessWidget {
  const DocBody({super.key, required this.doc, required this.palette});
  final ReadDoc doc;
  final ReadPalette palette;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: palette.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: palette.surfaceBorder),
        boxShadow: [
          BoxShadow(color: palette.shadow, blurRadius: 24, offset: const Offset(0, 8)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            doc.title,
            style: TextStyle(
              color: palette.textPrimary,
              fontSize: 24,
              height: 1.3,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '${doc.source} · ${doc.words} · ${doc.time}',
            style: TextStyle(color: palette.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 20),
          for (final p in doc.paragraphs) _ParaBlock(para: p, palette: palette),
          const SizedBox(height: 20),
          _AiBadge(source: doc.title, palette: palette),
        ],
      ),
    );
  }
}

/// 一段正文；高亮段带描边容器与角标编号。
class _ParaBlock extends StatelessWidget {
  const _ParaBlock({required this.para, required this.palette});
  final ReadPara para;
  final ReadPalette palette;

  @override
  Widget build(BuildContext context) {
    final base = TextStyle(color: palette.textPrimary, fontSize: 16, height: 1.9);

    if (!para.highlight) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 16),
        child: Text(para.text, style: base),
      );
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        color: palette.highlightBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: palette.highlightBorder),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: Text(para.text, style: base)),
          if (para.cite != null)
            Container(
              margin: const EdgeInsets.only(left: 8, top: 2),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: palette.accent,
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                '[${para.cite}]',
                style: TextStyle(
                  color: palette.accentContrast,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// AI 引用来源徽章。
class _AiBadge extends StatelessWidget {
  const _AiBadge({required this.source, required this.palette});
  final String source;
  final ReadPalette palette;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: palette.badgeBg,
        borderRadius: BorderRadius.circular(999),
        boxShadow: [
          BoxShadow(color: palette.shadow, blurRadius: 18, offset: const Offset(0, 4)),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.auto_awesome, size: 16, color: palette.badgeText),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              'AI 引用 · 来自「$source」',
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: palette.badgeText,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
