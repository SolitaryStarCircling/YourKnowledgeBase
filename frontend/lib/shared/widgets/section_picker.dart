/// 板块下拉选择器：导入 / 搜索 / 问答页共用，可选"不限"。
library;

import 'package:flutter/material.dart';

import '../../app/app_scope.dart';
import '../api/api_models.dart';
import '../state/app_settings.dart';

class SectionPicker extends StatefulWidget {
  const SectionPicker({
    super.key,
    required this.value,
    required this.onChanged,
    this.label = '板块',
    this.allowAny = true,
  });

  final String? value;
  final ValueChanged<String?> onChanged;
  final String label;

  /// true 时提供"不限板块"空选项（搜索 / 问答用）；导入页关掉
  final bool allowAny;

  @override
  State<SectionPicker> createState() => _SectionPickerState();
}

class _SectionPickerState extends State<SectionPicker> {
  AppSettings? _settings;
  List<SectionItem> _sections = [];
  bool _loading = true;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final settings = AppScope.of(context).settings;
    if (!identical(settings, _settings)) {
      _settings?.removeListener(_onSectionsChanged);
      settings.addListener(_onSectionsChanged);
      _settings = settings;
      _load();
    }
  }

  /// 板块增删改后（AppSettings.bumpSections）自动刷新下拉
  void _onSectionsChanged() {
    if (mounted) _load();
  }

  Future<void> _load() async {
    final scope = AppScope.of(context);
    try {
      final sections = await scope.api.listSections();
      if (mounted) {
        setState(() {
          _sections = sections;
          _loading = false;
        });
      }
    } catch (_) {
      // 板块加载失败不阻塞主流程，仅让下拉为空
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _settings?.removeListener(_onSectionsChanged);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final names = _sections.map((s) => s.name).toList();
    // 当前值不在列表里（如板块被删）时回退，避免 Dropdown 断言崩溃
    final effective = names.contains(widget.value) ? widget.value : null;
    return DropdownButtonFormField<String?>(
      initialValue: effective,
      decoration: InputDecoration(
        labelText: widget.label,
        border: const OutlineInputBorder(),
      ),
      items: [
        if (widget.allowAny)
          const DropdownMenuItem<String?>(value: null, child: Text('不限板块')),
        ...names.map(
          (n) => DropdownMenuItem<String?>(value: n, child: Text(n)),
        ),
      ],
      onChanged: _loading ? null : widget.onChanged,
    );
  }
}
