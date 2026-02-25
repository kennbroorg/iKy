import json
import os
from pathlib import Path
from typing import ClassVar

_FACTORIES_DIR = Path(__file__).resolve().parent


def get_config():
    class Config:
        CELERY_BROKER_URL = os.environ.get(
            "CELERY_BROKER_URL", "redis://localhost:6379/0"
        )
        CELERY_RESULT_BACKEND = os.environ.get(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
        )
        CELERY_ACCEPT_CONTENT: ClassVar[list] = ["json", "yaml"]
        CELERY_TASK_SERIALIZER = "json"
        CELERY_RESULT_SERIALIZER = "json"
        CELERY_IMPORTS = (
            "modules.keybase.keybase_tasks",
            "modules.gitlab.gitlab_tasks",
            "modules.leaks.leaks_tasks",
            "modules.twitter.twitter_tasks",
            # 'modules.twint.twint_tasks',
            "modules.linkedin.linkedin_tasks",
            # 'modules.ghostproject.ghostproject_tasks',
            "modules.github.github_tasks",
            # 'modules.fullcontact.fullcontact_tasks',
            "modules.usersearch.usersearch_tasks",
            "modules.socialscan.socialscan_tasks",
            "modules.instagram.instagram_tasks",
            "modules.tiktok.tiktok_tasks",
            "modules.sherlock.sherlock_tasks",
            "modules.holehe.holehe_tasks",
            "modules.search.search_tasks",
            # 'modules.tinder.tinder_tasks',
            # 'modules.skype.skype_tasks',
            "modules.venmo.venmo_tasks",
            "modules.darkpass.darkpass_tasks",
            "modules.tweetiment.tweetiment_tasks",
            "modules.reddit.reddit_tasks",
            "modules.peopledatalabs.peopledatalabs_tasks",
            "modules.emailrep.emailrep_tasks",
            "modules.leaklookup.leaklookup_tasks",
            "modules.spotify.spotify_tasks",
            "modules.twitch.twitch_tasks",
            "modules.mastodon.mastodon_tasks",
            "modules.dorks.dorks_tasks",
            "modules.psbdmp.psbdmp_tasks",
            "modules.twitter_comparison.twitter_info_tasks",
            "modules.twitter_comparison.twitter_comp_tasks",
        )

    return Config


def _api_keys_path() -> Path:
    """Return the absolute path to apikeys.json."""
    return _FACTORIES_DIR / "apikeys.json"


def api_keys_read():
    with _api_keys_path().open() as f:
        return json.load(f)


def api_keys_write(api_keys):
    with _api_keys_path().open("w") as f:
        json.dump(api_keys, f)
    return api_keys


def api_keys_search(api_name):
    with _api_keys_path().open() as f:
        items = json.load(f)
    for item in items:
        if item["name"] == api_name:
            return item["key"]
    return False
