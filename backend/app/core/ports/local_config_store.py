"""端口：本地持久配置存储（.env 文件）。实现放 infra/secrets/。"""

from abc import ABC, abstractmethod


class LocalConfigStore(ABC):
    """本地配置文件的读写。安全红线：Key 类条目由用例层禁止写入。"""

    @abstractmethod
    def load_all(self) -> dict[str, str]:
        """读出全部已保存的配置项（未保存的不出现）。"""

    @abstractmethod
    def set(self, name: str, value: str) -> None:
        """写入或覆盖一个配置项（仅非密项允许调用）。"""

    @abstractmethod
    def clear(self, name: str) -> None:
        """删除一个配置项；不存在时静默成功。"""

    @abstractmethod
    def init_template(self) -> bool:
        """生成无值配置模板；已存在则不动。返回是否新建。"""
