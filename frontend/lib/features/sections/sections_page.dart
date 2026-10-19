/// 板块页：板块列表的增删改；变更后通知 AppSettings，联动各页下拉。
library;

import 'package:flutter/material.dart';

import '../../app/app_scope.dart';
import '../../shared/api/api_models.dart';
import 'section_edit_dialog.dart';

class SectionsPage extends StatefulWidget {
  const SectionsPage({super.key});

  @override
  State<SectionsPage> createState() => _SectionsPageState();
}

class _SectionsPageState extends State<SectionsPage> {
  List<SectionItem> _sections = [];
  bool _loading = true;
  String? _error;
  bool _loadedOnce = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // 首次进入时加载；InheritedWidget 不能在 initState 里读
    if (!_loadedOnce) {
      _loadedOnce = true;
      _load();
    }
  }

  Future<void> _load() async {
    final api = AppScope.of(context).api;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final sections = await api.listSections();
      if (!mounted) return;
      setState(() {
        _sections = sections;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = '$e';
        _loading = false;
      });
    }
  }

  /// CRUD 成功后刷新列表并通知其他页面的板块下拉
  void _afterChange() {
    AppScope.of(context).settings.bumpSections();
    _load();
  }

  Future<void> _create() async {
    final form = await showSectionEditDialog(context);
    if (form == null || !mounted) return;
    try {
      await AppScope.of(context).api
          .createSection(form.name, description: form.description);
      if (!mounted) return;
      _afterChange();
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = '$e');
    }
  }

  Future<void> _edit(SectionItem item) async {
    final form = await showSectionEditDialog(
      context,
      initialName: item.name,
      initialDescription: item.description,
    );
    if (form == null || !mounted) return;
    try {
      await AppScope.of(context).api.updateSection(
        item.name,
        newName: form.name == item.name ? null : form.name,
        description: form.description,
      );
      if (!mounted) return;
      _afterChange();
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = '$e');
    }
  }

  Future<void> _delete(SectionItem item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('删除板块「${item.name}」？'),
        content: const Text('板块删除后文档仍在库中，只是不再归属该板块。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('删除'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await AppScope.of(context).api.deleteSection(item.name);
      if (!mounted) return;
      _afterChange();
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = '$e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _create,
        icon: const Icon(Icons.create_new_folder),
        label: const Text('新建板块'),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!),
            const SizedBox(height: 8),
            OutlinedButton(onPressed: _load, child: const Text('重试')),
          ],
        ),
      );
    }
    if (_sections.isEmpty) {
      return const Center(child: Text('还没有板块，点右下角新建一个'));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _sections.length,
      itemBuilder: (context, index) {
        final item = _sections[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            title: Text(item.name),
            subtitle: item.description.isEmpty ? null : Text(item.description),
            trailing: PopupMenuButton<String>(
              onSelected: (action) {
                if (action == 'edit') _edit(item);
                if (action == 'delete') _delete(item);
              },
              itemBuilder: (context) => const [
                PopupMenuItem(value: 'edit', child: Text('编辑')),
                PopupMenuItem(value: 'delete', child: Text('删除')),
              ],
            ),
          ),
        );
      },
    );
  }
}
