"""用例：清除本地 .env 中的一个配置项。"""

from app.core.ports.local_config_store import LocalConfigStore
from app.core.services.secrets import normalize_var_name


def clear_provider_config(name: str, *, store: LocalConfigStore) -> str:
    """删除配置项；不存在时静默成功。返回规范化变量名。"""
    var = normalize_var_name(name)
    store.clear(var)
    return var
