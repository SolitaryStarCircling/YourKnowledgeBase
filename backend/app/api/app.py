"""FastAPI 应用工厂：装配路由 + 统一错误映射。

错误映射约定：
- ValueError / FileNotFoundError -> 400（用例层的友好报错，如板块不存在、文档无文本）
- RuntimeError -> 503（缺 Key 的指引、上游服务失败）
- 其他异常 -> 500 固定文案（不向响应泄露内部细节）
- 请求校验错误 -> 422，只回 loc/msg/type，剥掉 input/ctx（防止请求体/头部密钥被回显）
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import config as config_routes
from app.api.routes import documents as documents_routes
from app.api.routes import query as query_routes
from app.api.routes import sections as sections_routes
from app.bootstrap import ServiceContainer, build_api_container


def create_app(container: ServiceContainer | None = None) -> FastAPI:
    """创建应用；container 为 None 时用真实组装根（测试可注入内存假件）。"""
    app = FastAPI(title="个人 AI 知识库", version="0.1.0")
    app.state.container = container if container is not None else build_api_container()

    # Web 端（浏览器）跨域必须放行，否则网页版前端无法调用本服务。
    # 本地优先应用无 Cookie / 鉴权，且服务默认只在本机与局域网可达，放开来源限制。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(documents_routes.router)
    app.include_router(query_routes.router)
    app.include_router(sections_routes.router)
    app.include_router(config_routes.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(ValueError)
    async def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(FileNotFoundError)
    async def handle_file_not_found(request: Request, exc: FileNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(RuntimeError)
    async def handle_runtime_error(request: Request, exc: RuntimeError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "服务内部错误"})

    return app
