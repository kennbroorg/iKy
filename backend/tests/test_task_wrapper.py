"""Tests for backend/factories/task_wrapper.py — @iky_task decorator."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# We must mock the celery_app module *before* importing task_wrapper,
# because task_wrapper does ``from celery_app import celery`` at module level.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_celery(monkeypatch):
    """Replace the celery instance with a fake that records registrations.

    ``celery.task(name=...)`` must return a decorator that simply returns
    the function it wraps (or a thin wrapper), so the wrapper logic inside
    ``iky_task`` still runs during tests.
    """
    mock_celery = MagicMock()

    # celery.task(name=...) should act as a pass-through decorator
    def fake_task(*, name: str):
        def decorator(fn):
            fn.name = name  # stash for assertions
            fn.delay = MagicMock()
            fn.apply_async = MagicMock()
            return fn

        return decorator

    mock_celery.task = MagicMock(side_effect=fake_task)

    # Also mock get_task_logger so it returns a real-ish logger
    import celery_app

    monkeypatch.setattr(celery_app, "celery", mock_celery)

    yield mock_celery


# ---------------------------------------------------------------------------
# Import after mocking
# ---------------------------------------------------------------------------


@pytest.fixture
def iky_task():
    """Import iky_task fresh so it picks up the mocked celery."""
    # Force reimport to get the mock
    import importlib

    import factories.task_wrapper as tw

    importlib.reload(tw)
    return tw.iky_task


# ===========================================================================
# Test: Celery task name
# ===========================================================================


class TestCeleryRegistration:
    """Verify the decorator produces the correct Celery task name."""

    def test_task_name_matches_registry_convention(self, iky_task):
        @iky_task(module_name="emailrep")
        def p_emailrep(username, from_m="Initial"):
            return [{"module": "emailrep"}]

        assert hasattr(p_emailrep, "name")
        assert p_emailrep.name == "modules.emailrep.emailrep_tasks.t_emailrep"

    def test_task_name_for_different_module(self, iky_task):
        @iky_task(module_name="github")
        def p_github(username, from_m="Initial"):
            return [{"module": "github"}]

        assert p_github.name == "modules.github.github_tasks.t_github"


# ===========================================================================
# Test: Dev-mode bypass
# ===========================================================================


class TestDevModeBypass:
    """Verify that dev-mode JSON file loading works correctly."""

    def test_returns_json_file_when_present(self, iky_task, tmp_path):
        canned = [{"module": "test"}, {"canned": True}]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        devfile = outputs / "output-testmod.json"
        devfile.write_text(json.dumps(canned))

        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="testmod")
            def p_testmod(param, from_m="Initial"):
                raise AssertionError("Should not be called")

            result = p_testmod("anything")

        assert result == canned

    def test_dev_mode_with_sleep(self, iky_task, tmp_path):
        canned = [{"module": "sleepy"}]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        devfile = outputs / "output-sleepy.json"
        devfile.write_text(json.dumps(canned))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
        ):

            @iky_task(module_name="sleepy", dev_mode_sleep=15)
            def p_sleepy(param, from_m="Initial"):
                raise AssertionError("Should not be called")

            result = p_sleepy("anything")

        mock_sleep.assert_called_once_with(15)
        assert result == canned

    def test_dev_mode_no_sleep_when_zero(self, iky_task, tmp_path):
        canned = [{"module": "nosleep"}]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        devfile = outputs / "output-nosleep.json"
        devfile.write_text(json.dumps(canned))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
        ):

            @iky_task(module_name="nosleep", dev_mode_sleep=0)
            def p_nosleep(param, from_m="Initial"):
                raise AssertionError("Should not be called")

            result = p_nosleep("anything")

        mock_sleep.assert_not_called()
        assert result == canned

    def test_invalid_json_falls_through(self, iky_task, tmp_path):
        """If dev-mode file has invalid JSON, fall through to real logic."""
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        devfile = outputs / "output-badjson.json"
        devfile.write_text("NOT VALID JSON {{{")

        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="badjson")
            def p_badjson(param, from_m="Initial"):
                return [{"module": "badjson"}, {"param": param}]

            result = p_badjson("test_input")

        # Should fall through and call the real function
        assert result == [{"module": "badjson"}, {"param": "test_input"}]

    def test_no_dev_file_calls_real_function(self, iky_task, tmp_path):
        """Without a dev-mode file, the real function is called."""
        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="nofile")
            def p_nofile(param, from_m="Initial"):
                return [{"module": "nofile"}, {"param": param}]

            result = p_nofile("realinput")

        assert result == [{"module": "nofile"}, {"param": "realinput"}]


# ===========================================================================
# Test: Error handling
# ===========================================================================


class TestErrorHandling:
    """Verify error handling matches the original t_* pattern exactly."""

    def test_iky_prefix_exception_returns_warning(self, iky_task, tmp_path):
        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="errmod")
            def p_errmod(param, from_m="Initial"):
                raise Exception("iKy - Missing or invalid Key")

            result = p_errmod("test@test.com")

        assert result == [
            {"module": "errmod"},
            {"param": "test@test.com"},
            {"validation": "not_used"},
            {
                "raw": [
                    {
                        "status": "Warning",
                        "reason": "Missing or invalid Key",
                        "traceback": result[3]["raw"][0]["traceback"],
                    }
                ]
            },
        ]
        raw = result[3]["raw"][0]
        assert raw["status"] == "Warning"
        assert raw["reason"] == "Missing or invalid Key"
        assert "iKy - Missing or invalid Key" in raw["traceback"]

    def test_generic_exception_returns_fail(self, iky_task, tmp_path):
        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="failmod")
            def p_failmod(param, from_m="Initial"):
                raise RuntimeError("connection timeout")

            result = p_failmod("user@example.com")

        raw = result[3]["raw"][0]
        assert raw["status"] == "Fail"
        assert raw["reason"] == "connection timeout"
        assert "RuntimeError" in raw["traceback"]

    def test_error_output_structure(self, iky_task, tmp_path):
        """Error output must have exactly: module, param, validation, raw."""
        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="structmod")
            def p_structmod(param, from_m="Initial"):
                raise Exception("boom")

            result = p_structmod("victim@test.com")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert keys == ["module", "param", "validation", "raw"]

        assert result[0]["module"] == "structmod"
        assert result[1]["param"] == "victim@test.com"
        assert result[2]["validation"] == "not_used"

    def test_error_traceback_is_string(self, iky_task, tmp_path):
        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="tbmod")
            def p_tbmod(param, from_m="Initial"):
                raise ValueError("test traceback")

            result = p_tbmod("someone")

        raw = result[3]["raw"][0]
        assert isinstance(raw["traceback"], str)
        assert "ValueError: test traceback" in raw["traceback"]


# ===========================================================================
# Test: Timing / logging
# ===========================================================================


class TestTiming:
    """Verify that elapsed time is logged."""

    def test_timing_logged_on_success(self, iky_task, tmp_path, caplog):
        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            caplog.at_level(logging.INFO),
        ):

            @iky_task(module_name="timingmod")
            def p_timingmod(param, from_m="Initial"):
                return [{"module": "timingmod"}]

            # The logger used inside task_wrapper is celery's get_task_logger,
            # which is hard to capture with caplog. Instead, we patch it.
            with patch("factories.task_wrapper.logger") as mock_logger:
                p_timingmod("test")
                mock_logger.info.assert_called_once()
                log_msg = mock_logger.info.call_args[0][0]
                assert "Timingmod" in log_msg
                assert "Response in" in log_msg
                assert "seconds" in log_msg

    def test_timing_logged_on_error(self, iky_task, tmp_path):
        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="errtiming")
            def p_errtiming(param, from_m="Initial"):
                raise Exception("fail")

            with patch("factories.task_wrapper.logger") as mock_logger:
                p_errtiming("test")
                mock_logger.info.assert_called_once()
                log_msg = mock_logger.info.call_args[0][0]
                assert "Errtiming" in log_msg
                assert "Response in" in log_msg


# ===========================================================================
# Test: Argument preservation
# ===========================================================================


class TestArgumentPreservation:
    """Verify the wrapper passes all args/kwargs to the wrapped function."""

    def test_positional_args(self, iky_task, tmp_path):
        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="argsmod")
            def p_argsmod(param, from_m="Initial"):
                return [
                    {"module": "argsmod"},
                    {"param": param},
                    {"from": from_m},
                ]

            result = p_argsmod("user@test.com", "github")

        assert result[1]["param"] == "user@test.com"
        assert result[2]["from"] == "github"

    def test_keyword_args(self, iky_task, tmp_path):
        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="kwargsmod")
            def p_kwargsmod(param, from_m="Initial"):
                return [
                    {"module": "kwargsmod"},
                    {"from": from_m},
                ]

            result = p_kwargsmod("user", from_m="twitter")

        assert result[1]["from"] == "twitter"

    def test_default_args(self, iky_task, tmp_path):
        with patch.object(Path, "cwd", return_value=tmp_path):

            @iky_task(module_name="defmod")
            def p_defmod(param, from_m="Initial"):
                return [{"from": from_m}]

            result = p_defmod("user")

        assert result[0]["from"] == "Initial"
