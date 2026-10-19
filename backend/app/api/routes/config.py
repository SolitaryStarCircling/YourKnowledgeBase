"""BYOK 配置路由：GET /config、PUT /config/{name}、DELETE /config/{name}。

程序绝不代写 Key：Key 类配置写入一律拒绝（400），会话头里的 Key 只进内存。
"""

import os

from fastapi import APIRouter, Response

from app.api.deps import ContainerDep, SessionDep
from app.api.schemas import ConfigItem, ConfigSetRequest, ConfigVarResponse
from app.usecases.clear_provider_config import clear_provider_config
from app.usecases.configure_provider import configure_provider
from app.usecases.show_config_status import show_config_status

router = APIRouter()


@router.get("/config", response_model=list[ConfigItem])
def config_status(container: ContainerDep, session: SessionDep) -> list[ConfigItem]:
    statuses = show_config_status(session=session, env=os.environ, store=container.config_store)
    return [
        ConfigItem(name=s.name, source=s.source, display_value=s.display_value) for s in statuses
    ]


@router.put("/config/{name}", response_model=ConfigVarResponse)
def config_set(name: str, body: ConfigSetRequest, container: ContainerDep) -> ConfigVarResponse:
    var = configure_provider(name, body.value, store=container.config_store)
    return ConfigVarResponse(name=var)


@router.delete("/config/{name}", status_code=204)
def config_clear(name: str, container: ContainerDep) -> Response:
    clear_provider_config(name, store=container.config_store)
    return Response(status_code=204)
