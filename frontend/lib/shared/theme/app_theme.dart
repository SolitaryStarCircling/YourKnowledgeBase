/// 由 ReadPalette 生成两套 ThemeData：亮=暖纸书屋（B）、暗=赛博霓虹（A）。
///
/// 切换主题只换 ThemeData，组件代码完全复用；阅览画面从
/// `ReadPalette.of(context)` 取色绘制渐变、卡片、高亮与徽章。
library;

import 'package:flutter/material.dart';

import 'read_palette.dart';

/// 亮色主题：方案 B「暖纸书屋」。
ThemeData buildPaperTheme() => _build(palette: paperPalette, brightness: Brightness.light);

/// 暗色主题：方案 A「赛博霓虹」。
ThemeData buildNeonTheme() => _build(palette: neonPalette, brightness: Brightness.dark);

ThemeData _build({
  required ReadPalette palette,
  required Brightness brightness,
}) {
  final scheme = ColorScheme.fromSeed(
    seedColor: palette.accent,
    brightness: brightness,
    surface: palette.surface,
  );

  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: scheme,
    scaffoldBackgroundColor: palette.backgroundBottom,
    // 阅览配色随主题下发，供 ReadPalette.of(context) 读取
    extensions: [palette],
    appBarTheme: AppBarTheme(
      backgroundColor: palette.surface,
      foregroundColor: palette.textPrimary,
      elevation: 0,
      surfaceTintColor: Colors.transparent,
    ),
    cardTheme: CardThemeData(
      color: palette.surface,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: palette.surfaceBorder),
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: Colors.transparent,
      side: BorderSide(color: palette.chipBorder),
      labelStyle: TextStyle(color: palette.textSecondary),
      selectedColor: palette.accent.withValues(alpha: 0.16),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: palette.inputBg,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: palette.inputBorder),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: palette.inputBorder),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: palette.accent, width: 1.6),
      ),
      hintStyle: TextStyle(color: palette.textSecondary),
    ),
    dividerTheme: DividerThemeData(color: palette.surfaceBorder, thickness: 1),
  );
}
