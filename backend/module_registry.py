"""Registry mapping module names to Celery task paths.

Each entry maps: route name -> (celery_task_path, pass_from)

``pass_from`` indicates whether the task accepts ``from_m`` as a second
argument.  Most modules only take ``(username,)``; a few take
``(username, from_m)``.
"""

# (celery_task_path, pass_from)
MODULE_REGISTRY: dict[str, tuple[str, bool]] = {
    "fullcontact": (
        "modules.fullcontact.fullcontact_tasks.t_fullcontact",
        False,
    ),
    "peopledatalabs": (
        "modules.peopledatalabs.peopledatalabs_tasks.t_peopledatalabs",
        False,
    ),
    "github": ("modules.github.github_tasks.t_github", True),
    "keybase": ("modules.keybase.keybase_tasks.t_keybase", True),
    "twitter": ("modules.twitter.twitter_tasks.t_twitter", False),
    "linkedin": ("modules.linkedin.linkedin_tasks.t_linkedin", True),
    "leaks": ("modules.leaks.leaks_tasks.t_leaks", False),
    "gitlab": ("modules.gitlab.gitlab_tasks.t_gitlab", False),
    "usersearch": (
        "modules.usersearch.usersearch_tasks.t_usersearch",
        False,
    ),
    "emailrep": ("modules.emailrep.emailrep_tasks.t_emailrep", False),
    "socialscan": (
        "modules.socialscan.socialscan_tasks.t_socialscan",
        False,
    ),
    "instagram": (
        "modules.instagram.instagram_tasks.t_instagram",
        False,
    ),
    "tiktok": ("modules.tiktok.tiktok_tasks.t_tiktok", False),
    "sherlock": ("modules.sherlock.sherlock_tasks.t_sherlock", False),
    "holehe": ("modules.holehe.holehe_tasks.t_holehe", False),
    "tinder": ("modules.tinder.tinder_tasks.t_tinder", False),
    "venmo": ("modules.venmo.venmo_tasks.t_venmo", False),
    "skype": ("modules.skype.skype_tasks.t_skype", False),
    "search": ("modules.search.search_tasks.t_search", False),
    "reddit": ("modules.reddit.reddit_tasks.t_reddit", False),
    "spotify": ("modules.spotify.spotify_tasks.t_spotify", False),
    "leaklookup": (
        "modules.leaklookup.leaklookup_tasks.t_leaklookup",
        False,
    ),
    "twitch": ("modules.twitch.twitch_tasks.t_twitch", False),
    "mastodon": ("modules.mastodon.mastodon_tasks.t_mastodon", False),
    "darkweb": ("modules.darkweb.darkweb_tasks.t_darkweb", False),
    "hudsonrock": (
        "modules.hudsonrock.hudsonrock_tasks.t_hudsonrock",
        False,
    ),
    "youtube": ("modules.youtube.youtube_tasks.t_youtube", False),
}
