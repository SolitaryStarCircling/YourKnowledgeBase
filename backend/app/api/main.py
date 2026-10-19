"""uvicorn 入口：`uvicorn app.api.main:app`。

全局实例单独放一个文件，避免测试 import 路由模块时就拼装真实 LanceDB / SQLite。
"""

from app.api.app import create_app

app = create_app()
