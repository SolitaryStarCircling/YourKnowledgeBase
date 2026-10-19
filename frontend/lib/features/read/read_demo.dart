/// 阅览画面演示数据与模型。
///
/// v1 后端暂无文档正文/列表接口，此处提供演示文档渲染阅读体验；
/// 接入真实数据时用后端返回构造 [ReadDoc] 即可，组件无需改动。
library;

/// 一段正文；[highlight] 标记 AI 引用高亮段，[cite] 为角标编号。
class ReadPara {
  const ReadPara(this.text, {this.highlight = false, this.cite});
  final String text;
  final bool highlight;
  final String? cite;
}

/// 一篇可切换的文档。
class ReadDoc {
  const ReadDoc({
    required this.title,
    required this.source,
    required this.words,
    required this.time,
    required this.category,
    required this.paragraphs,
  });
  final String title;
  final String source;
  final String words;
  final String time;
  final String category;
  final List<ReadPara> paragraphs;
}

/// 阅览画面的演示文档列表。
const demoDocs = <ReadDoc>[
  ReadDoc(
    title: '语义搜索与 RAG 入门笔记',
    source: 'demo_note.md',
    words: '1288 字',
    time: '2 小时前',
    category: '技术',
    paragraphs: [
      ReadPara(
        '语义搜索与传统关键词搜索的最大区别在于：它比较的是含义而不是字面。'
        '关键词搜索要求查询词和文档用词匹配，而语义搜索先把文本转成向量，'
        '再在向量空间里找距离最近的片段。',
      ),
      ReadPara(
        'RAG 回答里的引用必须来自真实检索到的片段，不允许模型编造来源。'
        '否则用户无法核实答案，知识库就失去了可信度。',
        highlight: true,
        cite: '1',
      ),
      ReadPara(
        '分块把长文切成几百字的小段，每段独立向量化。相邻分块保留少量重叠，'
        '可以避免一句话被拦腰切断在两个分块边界上。',
      ),
    ],
  ),
  ReadDoc(
    title: '深度学习笔记 · 第 3 章',
    source: 'dl_notes.pdf',
    words: '3420 字',
    time: '昨天',
    category: '读书笔记',
    paragraphs: [
      ReadPara('反向传播的核心是链式法则：把损失对每个参数的梯度逐层拆解并复用中间结果。'),
      ReadPara(
        '学习率过大时损失会震荡不收敛，过小则训练缓慢；warmup 能在起步阶段稳定梯度尺度。',
        highlight: true,
        cite: '2',
      ),
      ReadPara('批归一化通过标准化每层输入，缓解内部协变量偏移，从而允许更大的学习率。'),
    ],
  ),
  ReadDoc(
    title: '产品灵感速记',
    source: 'ideas.txt',
    words: '640 字',
    time: '3 天前',
    category: '灵感',
    paragraphs: [
      ReadPara('知识库的价值不在“存得多”，而在“找得到、引得准”。'),
      ReadPara('引用可核实是信任的底线，宁可少答也不编造来源。', highlight: true, cite: '3'),
      ReadPara('先做好增量更新，再考虑多知识库切换。'),
    ],
  ),
];
