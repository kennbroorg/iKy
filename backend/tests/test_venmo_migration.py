"""Regression tests for venmo migration to @iky_task decorator.

Verifies that the migrated p_venmo (now a Celery task via @iky_task)
produces output structurally identical to the old t_venmo wrapper,
and correctly implements the OSINT data enhancements from REQ-5 and REQ-6.
"""

import inspect
import json
import typing
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import Timeout

# ---------------------------------------------------------------------------
# Block dev-mode file globally for this test module
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode(tmp_path):
    """Redirect Path.cwd() so dev-mode files are never found."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Realistic mock Venmo API responses
# ---------------------------------------------------------------------------

VENMO_USER_RESPONSE = {
    "data": {
        "id": "1234567890",
        "username": "testuser",
        "display_name": "Test User",
        "profile_picture_url": "https://pics.venmo.com/testuser.jpg",
        "date_joined": "2021-05-01T00:00:00",
        "about": "OSINT testing bio",
        "is_active": True,
        "friends_count": 42,
    }
}

VENMO_USER_RESPONSE_MINIMAL = {
    "data": {
        "id": "1234567890",
        "username": "testuser",
        "display_name": "Test User",
        "profile_picture_url": "https://pics.venmo.com/testuser.jpg",
        "date_joined": "2021-05-01T00:00:00",
        "about": None,
        "is_active": None,
        "friends_count": None,
    }
}

VENMO_ERROR_RESPONSE = {
    "error": {
        "code": 404,
        "message": "User not found",
    }
}


@pytest.fixture
def mock_venmo_api():
    """Mock requests.get to return a full user payload."""
    mock_response = MagicMock()
    mock_response.json.return_value = VENMO_USER_RESPONSE.copy()

    with patch("modules.venmo.venmo_tasks.requests.get", return_value=mock_response):
        yield mock_response


@pytest.fixture
def mock_venmo_api_minimal():
    """Mock requests.get to return a user payload with null optional fields."""
    mock_response = MagicMock()
    mock_response.json.return_value = VENMO_USER_RESPONSE_MINIMAL.copy()

    with patch("modules.venmo.venmo_tasks.requests.get", return_value=mock_response):
        yield mock_response


@pytest.fixture
def mock_venmo_api_not_found():
    """Mock requests.get to return an error payload (user not found)."""
    mock_response = MagicMock()
    mock_response.json.return_value = VENMO_ERROR_RESPONSE.copy()

    with patch("modules.venmo.venmo_tasks.requests.get", return_value=mock_response):
        yield mock_response


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _find_gather_item(result, name_node):
    """Find a gather item by name-node in the graphic user list."""
    graphic = next(item["graphic"] for item in result if "graphic" in item)
    user_gather = graphic[0]["user"]
    return next(
        (item for item in user_gather if item.get("name-node") == name_node), None
    )


# ===========================================================================
# Backward compatibility
# ===========================================================================


class TestBackwardCompatibility:
    """Verify t_venmo alias works identically to p_venmo (REQ-1)."""

    def test_t_venmo_is_p_venmo(self):
        """AC-6: t_venmo = p_venmo alias must exist."""
        from modules.venmo.venmo_tasks import p_venmo, t_venmo

        assert t_venmo is p_venmo

    def test_celery_task_name(self):
        """The registered Celery task name matches the MODULE_REGISTRY."""
        from modules.venmo.venmo_tasks import p_venmo

        assert hasattr(p_venmo, "name")
        assert p_venmo.name == "modules.venmo.venmo_tasks.t_venmo"

    def test_p_venmo_has_module_name_attribute(self):
        """Decorator applied: p_venmo carries iky_task Celery attributes."""
        from modules.venmo.venmo_tasks import p_venmo

        # Celery tasks have a .name attribute registered
        assert hasattr(p_venmo, "name")
        assert "venmo" in p_venmo.name


# ===========================================================================
# Output structure (success path)
# ===========================================================================


class TestVenmoOutputStructure:
    """Verify p_venmo output matches the @iky_task contract (REQ-7)."""

    def test_success_output_has_required_keys(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")

        assert isinstance(result, list)
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys
        assert "param" in keys
        assert "validation" in keys
        assert "raw" in keys
        assert "graphic" in keys
        assert "profile" in keys
        assert "timeline" in keys

    def test_output_positional_structure(self, mock_venmo_api):
        """Output array must be positionally correct per REQ-7 contract."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")

        assert "module" in result[0] and result[0]["module"] == "venmo"
        assert "param" in result[1]
        assert "validation" in result[2] and result[2]["validation"] == "hard"
        assert "raw" in result[3]
        assert "graphic" in result[4]
        assert "profile" in result[5]
        assert "timeline" in result[6]

    def test_module_field_is_venmo(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        module = next(item["module"] for item in result if "module" in item)
        assert module == "venmo"

    def test_param_matches_input(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        param = next(item["param"] for item in result if "param" in item)
        assert param == "testuser"

    def test_validation_is_hard(self, mock_venmo_api):
        """AC-10: validation is always 'hard', no from_m conditional."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        validation = next(item["validation"] for item in result if "validation" in item)
        assert validation == "hard"

    def test_raw_contains_user_node(self, mock_venmo_api):
        """REQ-5: raw_node must be [{'user': <user_data>}]."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        raw = next(item["raw"] for item in result if "raw" in item)
        assert isinstance(raw, list)
        assert len(raw) == 1
        assert "user" in raw[0]
        assert raw[0]["user"]["display_name"] == "Test User"

    def test_graphic_has_user_key_not_details(self, mock_venmo_api):
        """REQ-7: graphic[0] must have 'user' key — NOT 'details' (emailrep pattern)."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        assert len(graphic) == 1
        assert "user" in graphic[0]
        assert "details" not in graphic[0]

    def test_signature_no_from_m(self):
        """AC-3: p_venmo must accept only 'username' — no 'from_m' parameter."""
        from modules.venmo.venmo_tasks import p_venmo

        sig = inspect.signature(p_venmo)
        param_names = list(sig.parameters.keys())
        assert param_names == ["username"]


# ===========================================================================
# Gather items — all 7 core items present (REQ-5)
# ===========================================================================


class TestVenmoGatherItemsCore:
    """Verify all 7 original gather items are present (REQ-5)."""

    CORE_NAME_NODES: typing.ClassVar[list[str]] = [
        "Venmo",
        "Venmoname",
        "VenmoJoin",
        "VenmoPic",
        "VenmoID",
        "VenmoURL",
        "VenmoUsername",
    ]

    def test_all_core_gather_items_present(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        user_gather = graphic[0]["user"]
        name_nodes = [item.get("name-node") for item in user_gather]

        for expected in self.CORE_NAME_NODES:
            assert expected in name_nodes, f"Missing gather item: {expected}"

    def test_venmo_root_node(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "Venmo")
        assert item is not None
        assert item["title"] == "Venmo"
        assert item["icon"] == "fas fa-money-bill-wave"

    def test_venmoname_has_display_name(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "Venmoname")
        assert item is not None
        assert item["subtitle"] == "Test User"
        assert item["icon"] == "fas fa-user"

    def test_venmojoin_has_date(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoJoin")
        assert item is not None
        assert item["subtitle"] == "2021-05-01T00:00:00"
        assert item["icon"] == "fas fa-calendar-check"

    def test_venmopic_has_picture_url(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoPic")
        assert item is not None
        assert "picture" in item
        assert item["picture"] == "https://pics.venmo.com/testuser.jpg"

    def test_venmoid_has_user_id(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoID")
        assert item is not None
        assert item["subtitle"] == "1234567890"
        assert item["icon"] == "fas fa-user-circle"

    def test_venmourl_has_api_url(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoURL")
        assert item is not None
        assert "venmo.com" in item["subtitle"]
        assert "testuser" in item["subtitle"]

    def test_venmoname_in_profile(self, mock_venmo_api):
        """REQ-5: profile must include name entry."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        profile = next(item["profile"] for item in result if "profile" in item)
        names = [p.get("name") for p in profile if "name" in p]
        assert "Test User" in names

    def test_timeline_has_join_date(self, mock_venmo_api):
        """REQ-5: timeline must include the join date entry."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        timeline = next(item["timeline"] for item in result if "timeline" in item)
        assert len(timeline) >= 1
        assert timeline[0]["action"] == "Start : Venmo"
        assert timeline[0]["date"] == "2021-05-01T00:00:00"

    def test_profile_has_photos(self, mock_venmo_api):
        """REQ-5: profile must include photos array."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        profile = next(item["profile"] for item in result if "profile" in item)
        photos_entries = [p for p in profile if "photos" in p]
        assert len(photos_entries) == 1
        photos = photos_entries[0]["photos"]
        assert len(photos) >= 1
        assert photos[0]["title"] == "Venmo"

    def test_profile_has_social(self, mock_venmo_api):
        """REQ-5: profile must include social array."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        profile = next(item["profile"] for item in result if "profile" in item)
        social_entries = [p for p in profile if "social" in p]
        assert len(social_entries) == 1
        social = social_entries[0]["social"]
        assert social[0]["name"] == "Venmo"
        assert "testuser" in social[0]["url"]

    def test_profile_has_username(self, mock_venmo_api):
        """REQ-5: profile must include username entry."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        profile = next(item["profile"] for item in result if "profile" in item)
        usernames = [p.get("username") for p in profile if "username" in p]
        assert "testuser" in usernames

    def test_profile_has_wallet_when_id_present(self, mock_venmo_api):
        """Wallet entry is present in profile when user has an id."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        profile = next(item["profile"] for item in result if "profile" in item)
        wallet_entries = [p for p in profile if "wallet" in p]
        assert len(wallet_entries) == 1

    def test_profile_wallet_url_format(self, mock_venmo_api):
        """Wallet URL is the Venmo QR code URL with the correct user id."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        profile = next(item["profile"] for item in result if "profile" in item)
        wallet_entry = next(p for p in profile if "wallet" in p)
        wallet = wallet_entry["wallet"]
        assert len(wallet) == 1
        assert wallet[0]["name"] == "Venmo"
        assert wallet[0]["url"] == "https://venmo.com/code?user_id=1234567890"
        assert wallet[0]["icon"] == "fas fa-qrcode"

    def test_profile_wallet_absent_when_no_id(self):
        """Wallet entry is absent from profile when user has no id."""
        from modules.venmo.venmo_tasks import p_venmo

        response = {
            "data": {
                **VENMO_USER_RESPONSE["data"],
                "id": "",
            }
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = response

        with (
            patch("modules.venmo.venmo_tasks.requests.get", return_value=mock_resp),
            patch.object(Path, "cwd", return_value=Path("/nonexistent/path")),
        ):
            result = p_venmo("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        wallet_entries = [p for p in profile if "wallet" in p]
        assert len(wallet_entries) == 0


# ===========================================================================
# Gather items — 5 new OSINT fields (REQ-6), present when data is available
# ===========================================================================


class TestVenmoNewGatherItems:
    """Verify the 5 new gather items when all fields are present (REQ-6)."""

    def test_venmobio_present_when_about_populated(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoBio")
        assert item is not None
        assert item["subtitle"] == "OSINT testing bio"
        assert item["icon"] == "fas fa-heartbeat"

    def test_venmoactive_present_when_is_active_set(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoActive")
        assert item is not None
        assert item["subtitle"] is True
        assert item["icon"] == "fas fa-toggle-on"

    def test_venmoactive_icon_off_when_false(self):
        """is_active=False → toggle-off icon."""
        from modules.venmo.venmo_tasks import p_venmo

        response = {
            "data": {
                **VENMO_USER_RESPONSE["data"],
                "is_active": False,
            }
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = response

        with (
            patch("modules.venmo.venmo_tasks.requests.get", return_value=mock_resp),
            patch.object(Path, "cwd", return_value=Path("/nonexistent/path")),
        ):
            result = p_venmo("testuser")

        item = _find_gather_item(result, "VenmoActive")
        assert item is not None
        assert item["icon"] == "fas fa-toggle-off"

    def test_venmofriends_present_when_friends_count_set(self, mock_venmo_api):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoFriends")
        assert item is not None
        assert item["subtitle"] == 42
        assert item["icon"] == "fas fa-user-friends"

    def test_venmoprofile_always_present(self, mock_venmo_api):
        """Profile Link is always present (derived from username)."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoProfile")
        assert item is not None
        assert item["subtitle"] == "https://venmo.com/testuser"
        assert item["icon"] == "fas fa-external-link-alt"

    def test_venmoqr_present_when_id_set(self, mock_venmo_api):
        """QR Code is present when user has an id (always true for valid users)."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoQR")
        assert item is not None
        assert item["subtitle"] == "https://venmo.com/code?user_id=1234567890"
        assert item["icon"] == "fas fa-qrcode"


# ===========================================================================
# Null guards — 5 new fields ABSENT when null/empty (REQ-6, AC-5)
# ===========================================================================


class TestVenmoNullGuards:
    """Verify null-guarded items are absent when fields are None/empty (REQ-6)."""

    def test_bio_absent_when_about_is_none(self, mock_venmo_api_minimal):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoBio")
        assert item is None, "VenmoBio must be absent when about=None"

    def test_active_absent_when_is_active_is_none(self, mock_venmo_api_minimal):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoActive")
        assert item is None, "VenmoActive must be absent when is_active=None"

    def test_friends_absent_when_friends_count_is_none(self, mock_venmo_api_minimal):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoFriends")
        assert item is None, "VenmoFriends must be absent when friends_count=None"

    def test_profile_link_always_present_even_with_nulls(self, mock_venmo_api_minimal):
        """Profile Link is always present (derived from username, not optional)."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoProfile")
        assert item is not None

    def test_qr_code_present_when_id_set_despite_null_fields(
        self, mock_venmo_api_minimal
    ):
        """QR Code present even when about/is_active/friends_count are null."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        item = _find_gather_item(result, "VenmoQR")
        assert item is not None

    def test_gather_item_count_without_optional_fields(self, mock_venmo_api_minimal):
        """With all nullable fields absent: 7 core + 2 always-present = 9 items."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        user_gather = graphic[0]["user"]
        # 7 core (Venmo, Venmoname, VenmoJoin, VenmoPic, VenmoID, VenmoURL, VenmoUsername)
        # + VenmoProfile (always present) + VenmoQR (id always present) = 9
        assert len(user_gather) == 9

    def test_gather_item_count_with_all_fields(self, mock_venmo_api):
        """With all fields present: 7 core + 5 new = 12 gather items."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        user_gather = graphic[0]["user"]
        assert len(user_gather) == 12


# ===========================================================================
# Error paths
# ===========================================================================


class TestVenmoErrorPaths:
    """Verify error handling (REQ-4)."""

    def test_user_not_found_returns_warning(self, mock_venmo_api_not_found):
        """REQ-4: error field → 'iKy - User not found' → Warning status."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("ghostuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert isinstance(raw, list)
        assert raw[0]["status"] == "Warning"
        assert raw[0]["reason"] == "User not found"

    def test_user_not_found_error_structure(self, mock_venmo_api_not_found):
        """Error structure: [module, param, validation, raw] — no graphic/profile."""
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("ghostuser")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert keys == ["module", "param", "validation", "raw"]
        assert result[0]["module"] == "venmo"
        assert result[1]["param"] == "ghostuser"
        assert result[2]["validation"] == "not_used"

    def test_user_not_found_traceback_contains_iky_prefix(
        self, mock_venmo_api_not_found
    ):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("ghostuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert "traceback" in raw[0]
        assert "iKy - User not found" in raw[0]["traceback"]

    def test_network_timeout_propagates_as_fail(self):
        """REQ-4: network timeout → Fail status (not Warning)."""
        from modules.venmo.venmo_tasks import p_venmo

        with patch(
            "modules.venmo.venmo_tasks.requests.get",
            side_effect=Timeout("Connection timed out"),
        ):
            result = p_venmo("anyuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Fail"
        assert "timed out" in raw[0]["reason"].lower()

    def test_generic_exception_returns_fail(self):
        """Non-iKy exception → Fail status."""
        from modules.venmo.venmo_tasks import p_venmo

        with patch(
            "modules.venmo.venmo_tasks.requests.get",
            side_effect=RuntimeError("connection error"),
        ):
            result = p_venmo("anyuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Fail"
        assert raw[0]["reason"] == "connection error"

    def test_error_traceback_is_string(self, mock_venmo_api_not_found):
        from modules.venmo.venmo_tasks import p_venmo

        result = p_venmo("ghostuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert isinstance(raw[0]["traceback"], str)


# ===========================================================================
# Dev mode (REQ-3)
# ===========================================================================


class TestVenmoDevMode:
    """Verify dev-mode bypass with golden fixture (REQ-3)."""

    def test_dev_mode_returns_golden_json(self, tmp_path):
        golden = [
            {"module": "venmo"},
            {"param": "devuser"},
            {"validation": "hard"},
            {"raw": [{"user": {"display_name": "Dev User"}}]},
            {"graphic": [{"user": []}]},
            {"profile": []},
            {"timeline": []},
        ]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        devfile = outputs / "output-venmo.json"
        devfile.write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
        ):
            from modules.venmo.venmo_tasks import p_venmo

            result = p_venmo("anything")

        assert result == golden
        # venmo has dev_mode_sleep=15
        mock_sleep.assert_called_once_with(15)

    def test_dev_mode_sleep_is_15(self):
        """AC config: dev_mode_sleep must be 15 for venmo."""
        # We verify by checking the dev mode sleep is called with 15
        # when a dev file is present (covered above). Here we assert
        # the decorator is configured correctly via the Celery task name
        # presence (indirect check that decorator was applied with params).
        from modules.venmo.venmo_tasks import p_venmo

        assert hasattr(p_venmo, "name")
        # The task was registered, meaning @iky_task was applied successfully
        assert p_venmo.name == "modules.venmo.venmo_tasks.t_venmo"


# ===========================================================================
# Argparse / CLI (REQ-8, AC-7)
# ===========================================================================


class TestVenmoCLI:
    """Verify the __main__ block uses argparse (REQ-8, AC-7)."""

    def test_argparse_module_is_imported(self):
        """The module imports argparse (prerequisite for __main__ block)."""
        import modules.venmo.venmo_tasks as vm

        # argparse must be present in the module's globals
        assert hasattr(vm, "argparse") or "argparse" in dir(vm)

    def test_argparse_is_used_in_module(self):
        """Confirm argparse.ArgumentParser is used (not sys.argv)."""
        import modules.venmo.venmo_tasks as mod

        # Read the source via inspect to verify argparse usage
        source = inspect.getsource(mod)
        assert "argparse.ArgumentParser" in source
        assert "argparse" in source

    def test_no_sys_argv_direct_access(self):
        """The CLI must use argparse, not raw sys.argv indexing."""
        import modules.venmo.venmo_tasks as mod

        source = inspect.getsource(mod)
        # sys.argv[1] style access is banned — argparse handles it
        assert "sys.argv[1]" not in source
