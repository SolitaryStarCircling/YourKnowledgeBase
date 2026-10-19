"""增量更新判定规则（纯 Python）：内容哈希。

导入同一来源时：
- 哈希相同 → 内容未变，跳过重新嵌入（省 API 费用）；
- 哈希不同 → 内容已变，删除旧向量后重新索引。
"""

import hashlib


def compute_content_hash(text: str) -> str:
    """对正文做规范化（去首尾空白）后取 SHA-256，避免空白差异造成伪变更。"""
    normalized = text.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
