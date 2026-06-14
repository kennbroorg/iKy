"""Pydantic models for API request/response validation."""

from typing import Annotated

from pydantic import BaseModel, Field


class ModuleRequest(BaseModel):
    """Standard request body for OSINT module endpoints.

    The ``dev_mode`` flag controls whether the task wrapper short-circuits to
    the local ``outputs/output-<module>.json`` golden file (when present).
    Defaults to ``True`` for backwards compatibility — frontend dev workflow
    relies on the golden files.  Callers (e.g. ``scripts/test-module.sh
    --save``) can pass ``dev_mode: false`` to force a real call.
    """

    username: str = ""
    from_m: Annotated[str, Field(alias="from")] = ""
    dev_mode: bool = True
    # Opt-in flag consumed only by the ``darkweb`` module to enable its
    # unfiltered engines.  Ignored by every other module.
    include_unfiltered: bool = False

    model_config = {"populate_by_name": True}


class TweetimentRequest(ModuleRequest):
    """Tweetiment endpoint accepts an extra ``task_id`` parameter."""

    task_id: str = ""


class DorksRequest(ModuleRequest):
    """Dorks endpoint accepts an extra ``dorks`` parameter."""

    dorks: str = ""


class TwitterInfoRequest(ModuleRequest):
    """Twitter comparison info endpoint accepts ``module_name``."""

    module_name: str = ""


class TwitterCompRequest(ModuleRequest):
    """Twitter comparison endpoint accepts date range and ``module_name``."""

    date_from: str = ""
    date_to: str = ""
    module_name: str = ""


class ModuleResponse(BaseModel):
    """Standard response from a module dispatch."""

    module: str
    task: str
    param: str
    from_m: str


class TwitterCompResponse(BaseModel):
    """Twitter comparison response includes date range."""

    module: str
    task: str
    param: str
    date_from: str
    date_to: str
    from_m: str


class TaskStateResponse(BaseModel):
    """Response from GET /state/{task_id}/{task_app}."""

    state: str
    task_id: str
    task_app: str


class TaskResultResponse(BaseModel):
    """Response from GET /result/{task_id}."""

    result: dict | list | str | None = None


class TaskListResponse(BaseModel):
    """Response from GET /tasklist."""

    modules: list[str]


class ApiKeyItem(BaseModel):
    """Single API key entry."""

    id: int | None = None
    name: str | None = None
    key: str | None = None
