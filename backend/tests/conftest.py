import pytest
from unittest.mock import MagicMock, patch
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
    """Mock celery.send_task so no real tasks are dispatched."""
    mock_result = MagicMock()
    mock_result.task_id = "fake-task-id-1234"

    with patch("api.create_celery") as mock_create:
        mock_celery = MagicMock()
        mock_celery.send_task.return_value = mock_result
        mock_create.return_value = mock_celery
        yield mock_celery
