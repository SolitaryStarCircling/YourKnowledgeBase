/// 应用级依赖注入：把 AppSettings + ApiClient 传给整棵组件树，免去重型状态框架。
library;

import 'package:flutter/widgets.dart';

import '../shared/api/api_client.dart';
import '../shared/state/app_settings.dart';

class AppScope extends InheritedWidget {
  const AppScope({
    super.key,
    required this.settings,
    required this.api,
    required super.child,
  });

  final AppSettings settings;
  final ApiClient api;

  static AppScope of(BuildContext context) {
    final scope = context.dependOnInheritedWidgetOfExactType<AppScope>();
    assert(scope != null, 'AppScope 未挂载到组件树');
    return scope!;
  }

  @override
  bool updateShouldNotify(AppScope oldWidget) =>
      settings != oldWidget.settings || api != oldWidget.api;
}
