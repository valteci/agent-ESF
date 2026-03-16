from __future__ import annotations

from fastapi import Request

from esf_agent_service.application.container import ServiceContainer


def get_container(request: Request) -> ServiceContainer:
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("Service container was not initialized.")
    return container
