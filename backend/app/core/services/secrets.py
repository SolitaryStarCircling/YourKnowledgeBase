"""密钥与配置解析的纯规则：白名单、脱敏、来源优先级（不碰磁盘和网络）。"""

from collections.abc import Mapping

# 统一命名（不绑定厂商）
ALLOWED_VARS = frozenset(
    {
        "LLM_API_KEY",
        "LLM_BASE_URL",
        "LLM_MODEL",
        "EMBEDDING_API_KEY",
        "EMBEDDING_BASE_URL",
        "EMBEDDING_MODEL",
    }
)

# 未配置时的默认值；密钥没有默认值
DEFAULTS = {
    "EMBEDDING_BASE_URL": "https://api.openai.com/v1",
    "EMBEDDING_MODEL": "text-embedding-3-small",
    "LLM_BASE_URL": "https://api.openai.com/v1",
    "LLM_MODEL": "gpt-4o-mini",
}

# 来源标记，优先级从高到低
SOURCE_SESSION = "session"
SOURCE_ENV = "env"
SOURCE_FILE = "file"
SOURCE_DEFAULT = "default"
SOURCE_MISSING = "missing"


def normalize_var_name(name: str) -> str:
    """规范化变量名（去空白、转大写）；白名单之外的报错。"""
    cleaned = name.strip().upper()
    if cleaned not in ALLOWED_VARS:
        raise ValueError(f"不支持的配置项：{name}（可配置：{'、'.join(sorted(ALLOWED_VARS))}）")
    return cleaned


def is_secret_var(name: str) -> bool:
    """API Key 类配置（以 _API_KEY 结尾）是密钥，受安全红线约束。"""
    return name.strip().upper().endswith("_API_KEY")


def mask_secret(value: str) -> str:
    """脱敏显示密钥：只露末 4 位，短值全遮。任何展示场景都必须经过它。"""
    if not value:
        return "（未设置）"
    if len(value) <= 8:
        return "****"
    return f"****...{value[-4:]}"


def resolve_value(
    name: str,
    *,
    session: Mapping[str, str],
    env: Mapping[str, str],
    file_values: Mapping[str, str],
) -> tuple[str, str]:
    """按优先级取配置值：运行时输入（会话）> 环境变量 > .env 文件 > 默认值。

    空字符串视为未设置。返回 (值, 来源标记)；取不到返回 ("", "missing")。
    """
    var = normalize_var_name(name)
    for source, values in (
        (SOURCE_SESSION, session),
        (SOURCE_ENV, env),
        (SOURCE_FILE, file_values),
    ):
        value = (values.get(var) or "").strip()
        if value:
            return value, source

    default = DEFAULTS.get(var, "")
    if default:
        return default, SOURCE_DEFAULT
    return "", SOURCE_MISSING
