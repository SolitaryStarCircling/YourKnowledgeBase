"""用例：查看 BYOK 配置状态（Key 一律脱敏，绝不回显原文）。"""

from collections.abc import Mapping
from dataclasses import dataclass

from app.core.ports.local_config_store import LocalConfigStore
from app.core.services.secrets import (
    ALLOWED_VARS,
    is_secret_var,
    mask_secret,
    resolve_value,
)


@dataclass(frozen=True)
class ConfigStatus:
    """一个配置项的状态：名称、来源、展示值（密钥已脱敏）。"""

    name: str
    source: str  # session / env / file / default / missing
    display_value: str


def show_config_status(
    *,
    session: Mapping[str, str] | None = None,
    env: Mapping[str, str] | None = None,
    store: LocalConfigStore,
) -> list[ConfigStatus]:
    """逐项解析配置并给出来源；密钥经脱敏后才进入展示值。"""
    statuses = []
    for name in sorted(ALLOWED_VARS):
        value, source = resolve_value(
            name,
            session=session or {},
            env=env or {},
            file_values=store.load_all(),
        )
        display = mask_secret(value) if is_secret_var(name) else (value or "（未设置）")
        statuses.append(ConfigStatus(name=name, source=source, display_value=display))
    return statuses
