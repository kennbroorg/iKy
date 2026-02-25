from unittest.mock import MagicMock, patch

import pytest
from factories.application import create_application


@pytest.fixture
def app():
    application = create_application()
    application.config["TESTING"] = True
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_celery_send(app):
    """Mock celery.send_task so no real tasks are dispatched.

    Also wires up ``celery.AsyncResult(task_id)`` so that
    ``/state/<id>/<app>`` and ``/result/<id>`` work without a
    running broker.
    """
    # -- send_task mock ------------------------------------------------
    mock_send_result = MagicMock()
    mock_send_result.task_id = "fake-task-id-1234"

    # -- AsyncResult mock ----------------------------------------------
    # api.py calls ``celery.AsyncResult(task_id).state`` and
    # ``celery.AsyncResult(task_id).get(timeout=...)``.
    # We pre-configure sensible defaults; individual tests can
    # override via ``mock_celery_send.AsyncResult.return_value``.
    mock_async_result = MagicMock()
    mock_async_result.state = "SUCCESS"
    mock_async_result.get.return_value = {"raw": "result-data"}

    # -- Patch path explanation ----------------------------------------
    # api.py does ``from factories._celery import create_celery``,
    # which binds the name ``create_celery`` in the *api* module's
    # namespace.  Per unittest.mock docs we must patch where the
    # name is LOOKED UP, i.e. ``"api.create_celery"``, NOT the
    # definition site ``"factories._celery.create_celery"``.
    with patch("api.create_celery") as mock_create:
        mock_celery = MagicMock()
        mock_celery.send_task.return_value = mock_send_result
        mock_celery.AsyncResult.return_value = mock_async_result
        mock_create.return_value = mock_celery
        yield mock_celery
