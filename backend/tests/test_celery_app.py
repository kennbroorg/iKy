"""Celery worker registration guard (Strict TDD).

``routers/modules.py`` dispatches Hudson Rock through
``celery.send_task("modules.hudsonrock.hudsonrock_tasks.t_hudsonrock")``.
If that module is missing from the worker's ``imports`` tuple the task is
never registered and the send fails at runtime (5xx) even though the
module is present in ``MODULE_REGISTRY`` and fully implemented.

These tests lock the Hudson Rock task module into ``celery.conf.imports``
and tie the assertion to the real registry task path so a wrong task name
or a dropped import is caught here.
"""

from celery_app import celery
from module_registry import MODULE_REGISTRY


def _task_module(task_path: str) -> str:
    """``modules.x.x_tasks.t_x`` -> ``modules.x.x_tasks``."""
    return task_path.rsplit(".", 1)[0]


def test_hudsonrock_task_module_registered_in_celery_imports():
    assert "modules.hudsonrock.hudsonrock_tasks" in celery.conf.imports


def test_registered_hudsonrock_task_path_is_importable_by_worker():
    # The exact path routers/modules.py dispatches via ``send_task``.
    task_path, _pass_from = MODULE_REGISTRY["hudsonrock"]
    assert task_path == "modules.hudsonrock.hudsonrock_tasks.t_hudsonrock"
    assert _task_module(task_path) in celery.conf.imports
