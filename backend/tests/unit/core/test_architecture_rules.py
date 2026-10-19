"""架构规则守护测试：依赖方向与 core 零框架依赖（AGENTS.md 硬约束 1/2）。"""

import ast
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[3]
APP_DIR = BACKEND_DIR / "app"

# core/ 禁止出现的框架 / 基础设施依赖（AGENTS.md 明令 + 常见同族）
FORBIDDEN_IN_CORE = {
    "fastapi",
    "pydantic",
    "lancedb",
    "sqlite3",
    "requests",
    "httpx",
    "typer",
    "click",
    "sqlalchemy",
}

# (被检查的包, 不允许 import 的 app 子包)
DIRECTION_RULES = [
    ("core", {"app.infra", "app.usecases", "app.api", "app.cli"}),
    ("usecases", {"app.infra", "app.api", "app.cli"}),
]


def _imports_of(package: str) -> set[str]:
    found: set[str] = set()
    for path in (APP_DIR / package).rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module)
    return found


def test_core_has_no_framework_dependencies():
    imports = _imports_of("core")
    offenders = {name for name in imports if name.split(".")[0] in FORBIDDEN_IN_CORE}
    assert not offenders, f"core/ 出现了框架依赖：{offenders}"


@pytest.mark.parametrize(("package", "forbidden"), DIRECTION_RULES)
def test_dependencies_only_point_inward(package: str, forbidden: set[str]):
    imports = _imports_of(package)
    offenders = {name for name in imports if name in forbidden or name.split(".")[0] in forbidden}
    assert not offenders, f"app/{package}/ 反向依赖了外层：{offenders}"
