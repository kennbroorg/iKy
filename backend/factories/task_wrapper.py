"""Reusable ``@iky_task`` decorator that replaces hand-written ``t_*`` wrappers.

Each iKy OSINT module defines a ``p_{module}`` function that does the real
work.  Historically, every module *also* contained a boilerplate ``t_{module}``
Celery task that wrapped ``p_{module}`` with dev-mode bypass, timing, and
error handling — ~30 lines of copy-pasted code per module.

``@iky_task`` absorbs all of that into a single decorator so modules only
need to define the processing function.
"""

from __future__ import annotations

import json
import time
import traceback
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from celery.utils.log import get_task_logger
from celery_app import celery

logger = get_task_logger(__name__)


def iky_task(
    *,
    module_name: str,
    api_keys: list[str] | None = None,
    dev_mode_sleep: float = 0,
) -> Callable:
    """Decorator that registers a ``p_*`` function as a Celery task.

    Parameters
    ----------
    module_name:
        Module identifier (e.g. ``"emailrep"``).  Used for the Celery task
        name, dev-mode file lookup, error output, and log messages.
    api_keys:
        Reserved for Phase 2 — list of API key names to pre-load.
    dev_mode_sleep:
        Seconds to sleep after loading dev-mode JSON (default 0).
    """
    if api_keys is None:
        api_keys = []

    # Celery task name must match the existing MODULE_REGISTRY paths:
    #   modules.{name}.{name}_tasks.t_{name}
    task_name = f"modules.{module_name}.{module_name}_tasks.t_{module_name}"

    def decorator(func: Callable[..., list[dict[str, Any]]]) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
            tic = time.perf_counter()
            total: list[dict[str, Any]] = []

            # dev_mode kwarg is consumed here — it MUST NOT be passed to
            # the inner processing function (which doesn't accept it).
            dev_mode = kwargs.pop("dev_mode", True)

            try:
                # --- Dev-mode bypass ---
                file_path = Path.cwd() / "outputs" / f"output-{module_name}.json"
                if dev_mode and file_path.exists():
                    logger.warning(f"Developer frontend mode - {file_path}")
                    try:
                        with file_path.open() as f:
                            data = json.load(f)
                        if dev_mode_sleep > 0:
                            time.sleep(dev_mode_sleep)
                        return data
                    except json.JSONDecodeError:
                        logger.error("Developer mode ERROR")
                elif not dev_mode and file_path.exists():
                    logger.info(f"dev_mode=False — bypassing golden file {file_path}")

                # --- Call the real processing function ---
                total = func(*args, **kwargs)

            except Exception as exc:
                exc_str = str(exc)
                if exc_str.startswith("iKy - "):
                    reason = exc_str[len("iKy - ") :]
                    status = "Warning"
                else:
                    reason = exc_str
                    status = "Fail"

                traceback.print_exc()
                traceback_text = traceback.format_exc()

                # First positional arg is the query param (username/email)
                param = args[0] if args else kwargs.get("username", "")

                total = [
                    {"module": module_name},
                    {"param": param},
                    {"validation": "not_used"},
                    {
                        "raw": [
                            {
                                "status": status,
                                "reason": reason,
                                "traceback": traceback_text,
                            }
                        ]
                    },
                ]

            finally:
                toc = time.perf_counter()
                logger.info(
                    f"{module_name.capitalize()} - Response in {toc - tic:0.4f} seconds"
                )

            return total

        # Register the wrapper as a Celery task with the canonical name
        celery_task = celery.task(name=task_name)(wrapper)

        # Expose the Celery task object as an attribute of the original
        # function so callers can do ``p_emailrep.task.delay(...)``
        func.task = celery_task  # type: ignore[attr-defined]

        return celery_task

    return decorator
