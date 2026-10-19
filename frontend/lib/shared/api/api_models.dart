/// API 数据模型：与后端 app/api/schemas.py 的字段一一对应，只做数据承载与 JSON 解析。
library;

class ImportResult {
  const ImportResult({
    required this.status,
    required this.docId,
    required this.title,
    required this.chunkCount,
  });

  /// created | updated | skipped
  final String status;
  final String docId;
  final String title;
  final int chunkCount;

  factory ImportResult.fromJson(Map<String, dynamic> json) => ImportResult(
    status: json['status'] as String,
    docId: json['doc_id'] as String,
    title: json['title'] as String,
    chunkCount: (json['chunk_count'] as num).toInt(),
  );
}

class SearchHit {
  const SearchHit({
    required this.chunkId,
    required this.docId,
    required this.index,
    required this.text,
    required this.title,
    required this.source,
    required this.score,
  });

  final String chunkId;
  final String docId;
  final int index;
  final String text;
  final String title;
  final String source;
  final double score;

  factory SearchHit.fromJson(Map<String, dynamic> json) => SearchHit(
    chunkId: json['chunk_id'] as String,
    docId: json['doc_id'] as String,
    index: (json['index'] as num).toInt(),
    text: json['text'] as String,
    title: json['title'] as String,
    source: json['source'] as String,
    score: (json['score'] as num).toDouble(),
  );
}

class Citation {
  const Citation({
    required this.marker,
    required this.chunkId,
    required this.docId,
    required this.title,
    required this.source,
    required this.excerpt,
    required this.score,
  });

  /// 回答正文中的引用编号 [n]
  final int marker;
  final String chunkId;
  final String docId;
  final String title;
  final String source;
  final String excerpt;
  final double score;

  factory Citation.fromJson(Map<String, dynamic> json) => Citation(
    marker: (json['marker'] as num).toInt(),
    chunkId: json['chunk_id'] as String,
    docId: json['doc_id'] as String,
    title: json['title'] as String,
    source: json['source'] as String,
    excerpt: json['excerpt'] as String,
    score: (json['score'] as num).toDouble(),
  );
}

class AskAnswer {
  const AskAnswer({required this.text, required this.citations});

  final String text;
  final List<Citation> citations;

  factory AskAnswer.fromJson(Map<String, dynamic> json) => AskAnswer(
    text: json['text'] as String,
    citations: (json['citations'] as List<dynamic>)
        .map((e) => Citation.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class SectionItem {
  const SectionItem({
    required this.sectionId,
    required this.name,
    required this.description,
  });

  final String sectionId;
  final String name;
  final String description;

  factory SectionItem.fromJson(Map<String, dynamic> json) => SectionItem(
    sectionId: json['section_id'] as String,
    name: json['name'] as String,
    description: json['description'] as String,
  );
}

class ConfigItem {
  const ConfigItem({
    required this.name,
    required this.source,
    required this.displayValue,
  });

  final String name;

  /// session | env | file | default | missing
  final String source;

  /// 已脱敏的显示值，前端原样展示、绝不回传
  final String displayValue;

  factory ConfigItem.fromJson(Map<String, dynamic> json) => ConfigItem(
    name: json['name'] as String,
    source: json['source'] as String,
    displayValue: json['display_value'] as String,
  );
}
