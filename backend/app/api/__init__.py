"""API 入口层：HTTP 接口（FastAPI）。

只做请求解析、用例调用与错误映射，业务逻辑全部在用例层；
依赖拼装在 app.bootstrap（组装根）。
"""
