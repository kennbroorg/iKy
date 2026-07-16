"""Standalone Celery application — no Flask dependency.

This module replaces the old ``factories._celery.create_celery`` pattern
which unnecessarily coupled every Celery worker to a full Flask app.
Configuration is read directly from environment variables.
"""

import os

from celery import Celery

celery = Celery(
    "iKy",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

celery.conf.update(
    accept_content=["json", "yaml"],
    task_serializer="json",
    result_serializer="json",
    imports=(
        "modules.keybase.keybase_tasks",
        "modules.gitlab.gitlab_tasks",
        "modules.leaks.leaks_tasks",
        "modules.twitter.twitter_tasks",
        "modules.linkedin.linkedin_tasks",
        "modules.github.github_tasks",
        "modules.usersearch.usersearch_tasks",
        "modules.socialscan.socialscan_tasks",
        "modules.instagram.instagram_tasks",
        "modules.tiktok.tiktok_tasks",
        "modules.sherlock.sherlock_tasks",
        "modules.holehe.holehe_tasks",
        "modules.search.search_tasks",
        "modules.venmo.venmo_tasks",
        "modules.darkweb.darkweb_tasks",
        "modules.tweetiment.tweetiment_tasks",
        "modules.reddit.reddit_tasks",
        "modules.peopledatalabs.peopledatalabs_tasks",
        "modules.emailrep.emailrep_tasks",
        "modules.leaklookup.leaklookup_tasks",
        "modules.spotify.spotify_tasks",
        "modules.twitch.twitch_tasks",
        "modules.mastodon.mastodon_tasks",
        "modules.dorks.dorks_tasks",
        "modules.twitter_comparison.twitter_info_tasks",
        "modules.twitter_comparison.twitter_comp_tasks",
        "modules.youtube.youtube_tasks",
    ),
)
