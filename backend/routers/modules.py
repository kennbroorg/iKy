"""OSINT module routes — dynamic handler + variant-specific endpoints."""

import logging

from celery_app import celery
from fastapi import APIRouter, HTTPException
from module_registry import MODULE_REGISTRY
from schemas import (
    DorksRequest,
    ModuleRequest,
    TweetimentRequest,
    TwitterCompRequest,
    TwitterInfoRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------
# Variant routes (must be defined BEFORE the dynamic /{module} catch-all)
# ------------------------------------------------------------------


@router.post("/tweetiment")
def r_tweetiment(body: TweetimentRequest):
    """Tweetiment accepts extra ``task_id`` for reading prior results."""
    logger.info(
        "Tweetiment - Detected Username: %s %s %s",
        body.username,
        body.from_m,
        body.task_id,
    )
    res = celery.send_task(
        "modules.tweetiment.tweetiment_tasks.t_tweetiment",
        args=(body.username, body.task_id, body.from_m),
    )
    logger.debug("Tweetiment - Task: %s", res.task_id)
    return {
        "module": "tweetiment",
        "task": res.task_id,
        "param": body.username,
        "from_m": body.from_m,
    }


@router.post("/dorks")
def r_dorks(body: DorksRequest):
    """Dorks accepts extra ``dorks`` search parameter."""
    logger.info(
        "Dorks - Detected Username: %s %s %s",
        body.username,
        body.dorks,
        body.from_m,
    )
    res = celery.send_task(
        "modules.dorks.dorks_tasks.t_dorks",
        args=(body.username, body.dorks),
    )
    logger.debug("Dorks - Task: %s", res.task_id)
    return {
        "module": "dorks",
        "task": res.task_id,
        "param": body.username,
        "from_m": body.from_m,
    }


@router.post("/twitter_info")
def r_twitter_info(body: TwitterInfoRequest):
    """Twitter comparison info (first account)."""
    module = body.module_name if body.module_name else "twitter_info"
    logger.info(
        "Twitter_info first - Detected Username: %s %s %s",
        body.username,
        body.from_m,
        module,
    )
    res = celery.send_task(
        "modules.twitter_comparison.twitter_info_tasks.t_twitter_info",
        args=(body.username, body.from_m, module),
    )
    logger.debug("Twitter_infof - Task: %s", res.task_id)
    return {
        "module": module,
        "task": res.task_id,
        "param": body.username,
        "from_m": body.from_m,
    }


@router.post("/twitter_infos")
def r_twitter_infos(body: ModuleRequest):
    """Twitter comparison info (second account)."""
    logger.info(
        "Twitter_info second - Detected Username: %s %s",
        body.username,
        body.from_m,
    )
    res = celery.send_task(
        "modules.twitter_comparison.twitter_info_tasks.t_twitter_info",
        args=(body.username,),
    )
    logger.debug("Twitter_infos - Task: %s", res.task_id)
    return {
        "module": "twitter_infos",
        "task": res.task_id,
        "param": body.username,
        "from_m": body.from_m,
    }


@router.post("/twitter_comp")
def r_twitter_comp(body: TwitterCompRequest):
    """Twitter comparison (first period)."""
    module = body.module_name if body.module_name else "twitter_comp"
    logger.info(
        "Twitter_compf - Detected Username: %s %s %s %s %s",
        body.username,
        body.date_from,
        body.date_to,
        body.from_m,
        module,
    )
    res = celery.send_task(
        "modules.twitter_comparison.twitter_comp_tasks.t_twitter_comp",
        args=(body.username, body.date_from, body.date_to, body.from_m, module),
    )
    logger.debug("Twitter_compf - Task: %s", res.task_id)
    return {
        "module": module,
        "task": res.task_id,
        "param": body.username,
        "date_from": body.date_from,
        "date_to": body.date_to,
        "from_m": body.from_m,
    }


@router.post("/twitter_comps")
def r_twitter_comps(body: TwitterCompRequest):
    """Twitter comparison (second period)."""
    logger.info(
        "Twitter_comps - Detected Username: %s %s %s %s",
        body.username,
        body.date_from,
        body.date_to,
        body.from_m,
    )
    res = celery.send_task(
        "modules.twitter_comparison.twitter_comp_tasks.t_twitter_comp",
        args=(body.username, body.date_from, body.date_to, body.from_m),
    )
    logger.debug("Twitter_comps - Task: %s", res.task_id)
    return {
        "module": "twitter_comps",
        "task": res.task_id,
        "param": body.username,
        "date_from": body.date_from,
        "date_to": body.date_to,
        "from_m": body.from_m,
    }


# ------------------------------------------------------------------
# Dynamic handler — catches all standard modules from the registry
# ------------------------------------------------------------------


@router.post("/{module}")
def r_module(module: str, body: ModuleRequest):
    """Generic handler for standard OSINT modules."""
    entry = MODULE_REGISTRY.get(module)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Module '{module}' not found")

    task_path, pass_from = entry
    args = (body.username, body.from_m) if pass_from else (body.username,)

    logger.info(
        "%s - Detected Username: %s %s", module.title(), body.username, body.from_m
    )
    res = celery.send_task(task_path, args=args)
    logger.debug("%s - Task: %s", module.title(), res.task_id)

    return {
        "module": module,
        "task": res.task_id,
        "param": body.username,
        "from_m": body.from_m,
    }
