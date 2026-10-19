"""本地配置存储（LocalConfigStore 端口实现）：backend/.env 文件，只落本地不进 git。"""

from pathlib import Path

from app.core.ports.local_config_store import LocalConfigStore

_TEMPLATE = """# 个人 AI 知识库 BYOK 配置（本文件不进 git；Key 只存本地）
# 通用 OpenAI 兼容嵌入接口（任何兼容 /embeddings 的厂商均可）
EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small

# RAG 问答（任何兼容 /chat/completions 的厂商均可）
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
"""


class EnvFileConfigStore(LocalConfigStore):
    def __init__(self, env_path: str | Path) -> None:
        self._path = Path(env_path)

    def load_all(self) -> dict[str, str]:
        if not self._path.is_file():
            return {}
        values: dict[str, str] = {}
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
        return values

    def set(self, name: str, value: str) -> None:
        lines = self._read_lines()
        new_line = f"{name}={value}"
        for i, line in enumerate(lines):
            if line.strip().partition("=")[0].strip() == name:
                lines[i] = new_line
                break
        else:
            lines.append(new_line)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def clear(self, name: str) -> None:
        if not self._path.is_file():
            return
        lines = [
            line for line in self._read_lines() if line.strip().partition("=")[0].strip() != name
        ]
        self._path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def init_template(self) -> bool:
        if self._path.is_file():
            return False
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(_TEMPLATE, encoding="utf-8")
        return True

    def _read_lines(self) -> list[str]:
        if not self._path.is_file():
            return []
        return self._path.read_text(encoding="utf-8").splitlines()
