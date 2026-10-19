/// 阅览画面配色 token：方案 A「赛博霓虹」与方案 B「暖纸书屋」共用同一套组件，只换颜色。
///
/// 通过 ThemeExtension 注入主题；模式切换只换 ThemeData，组件代码完全复用。
library;

import 'package:flutter/material.dart';

/// 阅览画面专用配色。B 暖纸书屋 = 亮色（默认），A 赛博霓虹 = 暗色。
class ReadPalette extends ThemeExtension<ReadPalette> {
  const ReadPalette({
    required this.backgroundTop,
    required this.backgroundBottom,
    required this.surface,
    required this.surfaceBorder,
    required this.textPrimary,
    required this.textSecondary,
    required this.accent,
    required this.accentContrast,
    required this.highlightBg,
    required this.highlightBorder,
    required this.badgeBg,
    required this.badgeText,
    required this.chipBorder,
    required this.inputBg,
    required this.inputBorder,
    required this.shadow,
  });

  /// 页面渐变：上 / 下两端色
  final Color backgroundTop;
  final Color backgroundBottom;

  /// 卡片与描边
  final Color surface;
  final Color surfaceBorder;

  /// 文字
  final Color textPrimary;
  final Color textSecondary;

  /// 品牌强调色及其上的对比文字
  final Color accent;
  final Color accentContrast;

  /// AI 引用高亮段落
  final Color highlightBg;
  final Color highlightBorder;

  /// AI 引用徽章
  final Color badgeBg;
  final Color badgeText;

  /// 分类 chips 与输入框
  final Color chipBorder;
  final Color inputBg;
  final Color inputBorder;

  /// 卡片投影 / 辉光色
  final Color shadow;

  /// 当前主题里的阅览配色
  static ReadPalette of(BuildContext context) =>
      Theme.of(context).extension<ReadPalette>()!;

  @override
  ReadPalette copyWith({
    Color? backgroundTop,
    Color? backgroundBottom,
    Color? surface,
    Color? surfaceBorder,
    Color? textPrimary,
    Color? textSecondary,
    Color? accent,
    Color? accentContrast,
    Color? highlightBg,
    Color? highlightBorder,
    Color? badgeBg,
    Color? badgeText,
    Color? chipBorder,
    Color? inputBg,
    Color? inputBorder,
    Color? shadow,
  }) {
    return ReadPalette(
      backgroundTop: backgroundTop ?? this.backgroundTop,
      backgroundBottom: backgroundBottom ?? this.backgroundBottom,
      surface: surface ?? this.surface,
      surfaceBorder: surfaceBorder ?? this.surfaceBorder,
      textPrimary: textPrimary ?? this.textPrimary,
      textSecondary: textSecondary ?? this.textSecondary,
      accent: accent ?? this.accent,
      accentContrast: accentContrast ?? this.accentContrast,
      highlightBg: highlightBg ?? this.highlightBg,
      highlightBorder: highlightBorder ?? this.highlightBorder,
      badgeBg: badgeBg ?? this.badgeBg,
      badgeText: badgeText ?? this.badgeText,
      chipBorder: chipBorder ?? this.chipBorder,
      inputBg: inputBg ?? this.inputBg,
      inputBorder: inputBorder ?? this.inputBorder,
      shadow: shadow ?? this.shadow,
    );
  }

  @override
  ReadPalette lerp(ReadPalette? other, double t) {
    if (other is! ReadPalette) return this;
    return ReadPalette(
      backgroundTop: Color.lerp(backgroundTop, other.backgroundTop, t)!,
      backgroundBottom: Color.lerp(
        backgroundBottom,
        other.backgroundBottom,
        t,
      )!,
      surface: Color.lerp(surface, other.surface, t)!,
      surfaceBorder: Color.lerp(surfaceBorder, other.surfaceBorder, t)!,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      accent: Color.lerp(accent, other.accent, t)!,
      accentContrast: Color.lerp(accentContrast, other.accentContrast, t)!,
      highlightBg: Color.lerp(highlightBg, other.highlightBg, t)!,
      highlightBorder: Color.lerp(highlightBorder, other.highlightBorder, t)!,
      badgeBg: Color.lerp(badgeBg, other.badgeBg, t)!,
      badgeText: Color.lerp(badgeText, other.badgeText, t)!,
      chipBorder: Color.lerp(chipBorder, other.chipBorder, t)!,
      inputBg: Color.lerp(inputBg, other.inputBg, t)!,
      inputBorder: Color.lerp(inputBorder, other.inputBorder, t)!,
      shadow: Color.lerp(shadow, other.shadow, t)!,
    );
  }
}

/// 方案 B「暖纸书屋」：米色纸感 + 琥珀暖调（亮色）。
const paperPalette = ReadPalette(
  backgroundTop: Color(0xFFFBF5EA),
  backgroundBottom: Color(0xFFF6ECD9),
  surface: Color(0xFFFFFDF8),
  surfaceBorder: Color(0xFFEAD9BC),
  textPrimary: Color(0xFF3D2B1F),
  textSecondary: Color(0xFF8A6D4E),
  accent: Color(0xFFB4692C),
  accentContrast: Color(0xFFFFF6EC),
  highlightBg: Color(0xFFF5E4C8),
  highlightBorder: Color(0xFFD9A85E),
  badgeBg: Color(0xFFB4692C),
  badgeText: Color(0xFFFFF6EC),
  chipBorder: Color(0xFFE0CBAA),
  inputBg: Color(0xFFFFFDF8),
  inputBorder: Color(0xFFE0CBAA),
  shadow: Color(0x33B4692C),
);

/// 方案 A「赛博霓虹」：深蓝紫渐变 + 靛紫霓虹、青色高亮（暗色）。
const neonPalette = ReadPalette(
  backgroundTop: Color(0xFF12142C),
  backgroundBottom: Color(0xFF23264F),
  surface: Color(0xFF1B1E3B),
  surfaceBorder: Color(0xFF3A3F6B),
  textPrimary: Color(0xFFEAEAFF),
  textSecondary: Color(0xFFA6A9D4),
  accent: Color(0xFF7C6CF0),
  accentContrast: Color(0xFFFFFFFF),
  highlightBg: Color(0x2222D3EE),
  highlightBorder: Color(0xFF22D3EE),
  badgeBg: Color(0xFF6C5CE7),
  badgeText: Color(0xFFFFFFFF),
  chipBorder: Color(0xFF4A4F86),
  inputBg: Color(0xFF1B1E3B),
  inputBorder: Color(0xFF4A4F86),
  shadow: Color(0x6622D3EE),
);
