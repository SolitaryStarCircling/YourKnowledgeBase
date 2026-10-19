"""用例：写入非密配置项（Base URL / Model）到本地 .env。

安全红线：Key 类配置不写入任何配置文件，本用例负责把守这道门。
"""

from app.core.ports.local_config_store import LocalConfigStore
from app.core.services.secrets import is_secret_var, normalize_var_name

_SECRET_REFUSAL = (
    "{var} 是密钥，按安全红线不允许写入任何配置文件。\n"
    "  可选：① 手动填入 backend/.env 或设置同名环境变量（持久）；"
    "② 命令加 --api-key 参数仅本次会话使用（进程退出即失效）。"
)


def configure_provider(name: str, value: str, *, store: LocalConfigStore) -> str:
    """把配置项写入本地 .env；密钥类拒绝落盘。返回规范化变量名。"""
    var = normalize_var_name(name)
    if is_secret_var(var):
        raise ValueError(_SECRET_REFUSAL.format(var=var))

    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{var} 的值不能为空（要删除请用 config clear）")

    store.set(var, cleaned)
    return var
