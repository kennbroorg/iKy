"""Utility routes: task state/result polling, tasklist, apikey, testing."""

import logging
import os

from celery_app import celery
from factories.configuration import api_keys_read, api_keys_write
from fastapi import APIRouter, HTTPException, Request
from module_registry import MODULE_REGISTRY

logger = logging.getLogger(__name__)

router = APIRouter()

_DEBUG = os.environ.get("FASTAPI_DEBUG", "").lower() in ("1", "true", "yes")


@router.get("/tasklist")
def r_tasklist():
    """Return list of available module routes."""
    # Build the list from the registry + variant routes so it stays in
    # sync automatically.  The old Flask version iterated url_map; here
    # we replicate the same list the frontend expects.
    modules = [
        *sorted(MODULE_REGISTRY.keys()),
        "spotify",
        "tweetiment",
        "dorks",
        "twitter_info",
        "twitter_infos",
        "twitter_comp",
        "twitter_comps",
    ]
    # Deduplicate while preserving order (registry already has some of these)
    seen: set[str] = set()
    unique: list[str] = []
    for m in modules:
        if m not in seen:
            seen.add(m)
            unique.append(m)
    # Add utility routes that Flask's url_map also exposed
    for extra in ("tasklist", "state", "result", "apikey", "testing"):
        if extra not in seen:
            seen.add(extra)
            unique.append(extra)
    return {"modules": unique}


@router.get("/state/{task_id}/{task_app}")
def r_state(task_id: str, task_app: str):
    """Poll the state of a dispatched Celery task."""
    res = celery.AsyncResult(task_id).state
    return {"state": res, "task_id": task_id, "task_app": task_app}


@router.get("/result/{task_id}")
def r_result(task_id: str):
    """Retrieve the result of a completed Celery task."""
    try:
        res = celery.AsyncResult(task_id).get(timeout=120)
    except Exception as exc:
        raise HTTPException(status_code=504, detail="Task timed out or failed") from exc
    return {"result": res}


@router.post("/apikey")
async def r_apikey(request: Request):
    """Read or write API keys.

    - Empty body or non-list body (e.g. ``{}``) → read current keys.
    - Array body → validate and write keys.
    """
    body = await request.body()
    if body:
        api_keys = await request.json()
        # If the body is a list, treat it as a write operation
        if isinstance(api_keys, list):
            if not all(
                isinstance(k, dict) and set(k.keys()) <= {"id", "name", "key"}
                for k in api_keys
            ):
                raise HTTPException(status_code=400, detail="Invalid API key format")
            keys = api_keys_write(api_keys)
            return {"keys": keys}
    # Any non-list body (empty, {}, null) → read
    keys = api_keys_read()
    return {"keys": keys}


@router.post("/testing")
async def r_testing(request: Request):
    """Echo JSON body back — only available in debug mode."""
    if not _DEBUG:
        raise HTTPException(status_code=404, detail="Not Found")
    result = await request.json()
    logger.debug("Testing endpoint received: %s", result)
    return result
