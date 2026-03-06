import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Enable debug mode for testing endpoint
os.environ["FASTAPI_DEBUG"] = "1"

from main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_celery_send():
    """Mock celery.send_task so no real tasks are dispatched.

    Patches ``celery_app.celery`` which is imported by the router
    modules.  We must patch at every lookup site so that the already-
    imported references in ``routers.modules`` and ``routers.utils``
    see the mock.
    """
    # -- send_task mock ------------------------------------------------
    mock_send_result = MagicMock()
    mock_send_result.task_id = "fake-task-id-1234"

    # -- AsyncResult mock ----------------------------------------------
    mock_async_result = MagicMock()
    mock_async_result.state = "SUCCESS"
    mock_async_result.get.return_value = {"raw": "result-data"}

    mock_celery = MagicMock()
    mock_celery.send_task.return_value = mock_send_result
    mock_celery.AsyncResult.return_value = mock_async_result

    with (
        patch("routers.modules.celery", mock_celery),
        patch("routers.utils.celery", mock_celery),
    ):
        yield mock_celery
