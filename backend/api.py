import logging

from factories._celery import create_celery
from factories.configuration import api_keys_read, api_keys_write
from flask import Blueprint, abort, current_app, jsonify, request

logger = logging.getLogger(__name__)

home = Blueprint("home_views", __name__)


def _get_json_or_400() -> dict:
    """Return parsed JSON body or abort with 400."""
    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="Request body must be valid JSON")
    return data


################################################
# Testing
################################################
@home.route("/testing", methods=["POST"])
def r_testing():
    if not current_app.debug:
        abort(404)
    result = _get_json_or_400()
    logger.debug("Testing endpoint received: %s", result)
    return jsonify(result)


################################################
# Task List
################################################
# @home.route("/tasklist", methods=["POST"])
@home.route("/tasklist", methods=["GET"])
def r_tasklist():
    module_list = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint != "static":
            module_list.append(rule.rule[1:])
    return jsonify(modules=module_list)


################################################
# State
################################################
@home.route("/state/<task_id>/<task_app>")
def r_state(task_id, task_app):
    celery = create_celery(current_app)
    res = celery.AsyncResult(task_id).state
    return jsonify(state=res, task_id=task_id, task_app=task_app)


################################################
# Result
################################################
@home.route("/result/<task_id>")
def r_result(task_id):
    celery = create_celery(current_app)
    try:
        res = celery.AsyncResult(task_id).get(timeout=120)
    except Exception:
        return jsonify(error="Task timed out or failed"), 504
    return jsonify(result=res)


################################################
# API Keys
################################################
@home.route("/apikey", methods=["POST"])
def r_apikey():
    if request.json:
        api_keys = _get_json_or_400()
        if not isinstance(api_keys, list) or not all(
            isinstance(k, dict) and set(k.keys()) <= {"id", "name", "key"}
            for k in api_keys
        ):
            return jsonify(error="Invalid API key format"), 400
        keys = api_keys_write(api_keys)
    else:
        keys = api_keys_read()
    return jsonify(keys=keys)


################################################
# Fullcontact
################################################
@home.route("/fullcontact", methods=["POST"])
def r_fullcontact():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Fullcontact - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.fullcontact.fullcontact_tasks." + "t_fullcontact", args=(username,)
    )
    logger.debug("Fullcontact - Task: %s", res.task_id)
    return jsonify(
        module="fullcontact", task=res.task_id, param=username, from_m=from_m
    )


################################################
# Peopledatalabs
################################################
@home.route("/peopledatalabs", methods=["POST"])
def r_peopledatalabs():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Peopledatalabs - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.peopledatalabs.peopledatalabs_tasks." + "t_peopledatalabs",
        args=(username,),
    )
    logger.debug("Peopledatalabs - Task: %s", res.task_id)
    return jsonify(
        module="peopledatalabs", task=res.task_id, param=username, from_m=from_m
    )


################################################
# Github
################################################
@home.route("/github", methods=["POST"])
def r_github():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Github - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.github.github_tasks.t_github", args=(username, from_m)
    )
    logger.debug("Github - Task: %s", res.task_id)
    return jsonify(module="github", task=res.task_id, param=username, from_m=from_m)


################################################
# GhostProject
################################################
@home.route("/ghostproject", methods=["POST"])
def r_ghostproject():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("GhostProject - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.ghostproject.ghostproject_tasks.t_ghostproject", args=(username,)
    )
    logger.debug("GhostProject - Task: %s", res.task_id)
    return jsonify(
        module="ghostproject", task=res.task_id, param=username, from_m=from_m
    )


################################################
# Keybase
################################################
@home.route("/keybase", methods=["POST"])
def r_keybase():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Keybase - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.keybase.keybase_tasks.t_keybase", args=(username, from_m)
    )
    logger.debug("Keybase - Task: %s", res.task_id)
    return jsonify(module="keybase", task=res.task_id, param=username, from_m=from_m)


################################################
# Twitter
################################################
@home.route("/twitter", methods=["POST"])
def r_twitter():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Twitter - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.twitter.twitter_tasks.t_twitter", args=(username, from_m)
    )
    logger.debug("Twitter - Task: %s", res.task_id)
    return jsonify(module="twitter", task=res.task_id, param=username, from_m=from_m)


# ################################################
# # Twint
# ################################################
# @home.route("/twint", methods=["POST"])
# def r_twint():
#     celery = create_celery(current_app)
#     json_result = _get_json_or_400()
#     username = json_result.get("username", "")
#     from_m = json_result.get("from", "")
#     print("Twint - Detected Username : ", username, from_m)
#     res = celery.send_task('modules.twint.twint_tasks.t_twint',
#                            args=(username, from_m))
#     print("Twint - Task : ", res.task_id)
#     return jsonify(module="twint", task=res.task_id,
#                    param=username, from_m=from_m)


################################################
# Linkedin
################################################
@home.route("/linkedin", methods=["POST"])
def r_linkedin():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Linkedin - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.linkedin.linkedin_tasks.t_linkedin", args=(username, from_m)
    )
    logger.debug("Linkedin - Task: %s", res.task_id)
    return jsonify(module="linkedin", task=res.task_id, param=username, from_m=from_m)


################################################
# Leaks
################################################
@home.route("/leaks", methods=["POST"])
def r_leaks():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Leaks - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.leaks.leaks_tasks.t_leaks", args=(username,))
    logger.debug("Leaks - Task: %s", res.task_id)
    return jsonify(module="leaks", task=res.task_id, param=username, from_m=from_m)


################################################
# Darkpass
################################################
@home.route("/darkpass", methods=["POST"])
def r_darkpass():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Darkpass - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.darkpass.darkpass_tasks.t_darkpass", args=(username,)
    )
    logger.debug("Darkpass - Task: %s", res.task_id)
    return jsonify(
        module="darkpass",
        task=res.task_id,
        param=username,
        from_m=from_m,
    )


################################################
# Gitlab
################################################
@home.route("/gitlab", methods=["POST"])
def r_gitlab():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Gitlab - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.gitlab.gitlab_tasks.t_gitlab", args=(username,))
    logger.debug("Gitlab - Task: %s", res.task_id)
    return jsonify(module="gitlab", task=res.task_id, param=username, from_m=from_m)


################################################
# Usersearch
################################################
@home.route("/usersearch", methods=["POST"])
def r_usersearch():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Usersearch - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.usersearch.usersearch_tasks.t_usersearch", args=(username,)
    )
    logger.debug("Usersearch - Task: %s", res.task_id)
    return jsonify(module="usersearch", task=res.task_id, param=username, from_m=from_m)


################################################
# EmailRepIO
################################################
@home.route("/emailrep", methods=["POST"])
def r_emailrep():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("EmailRep - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.emailrep.emailrep_tasks.t_emailrep", args=(username,)
    )
    logger.debug("EmailRep - Task: %s", res.task_id)
    return jsonify(module="emailrep", task=res.task_id, param=username, from_m=from_m)


################################################
# SocialScan
################################################
@home.route("/socialscan", methods=["POST"])
def r_socialscan():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("SocialScan - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.socialscan.socialscan_tasks.t_socialscan", args=(username,)
    )
    logger.debug("SocialScan - Task: %s", res.task_id)
    return jsonify(module="socialscan", task=res.task_id, param=username, from_m=from_m)


################################################
# Instagram
################################################
@home.route("/instagram", methods=["POST"])
def r_instagram():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Instagram - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.instagram.instagram_tasks.t_instagram", args=(username,)
    )
    logger.debug("Instagram - Task: %s", res.task_id)
    return jsonify(module="instagram", task=res.task_id, param=username, from_m=from_m)


################################################
# Tiktok
################################################
@home.route("/tiktok", methods=["POST"])
def r_tiktok():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Tiktok - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.tiktok.tiktok_tasks.t_tiktok", args=(username,))
    logger.debug("Tiktok - Task: %s", res.task_id)
    return jsonify(module="tiktok", task=res.task_id, param=username, from_m=from_m)


################################################
# Sherlock
################################################
@home.route("/sherlock", methods=["POST"])
def r_sherlock():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Sherlock - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.sherlock.sherlock_tasks.t_sherlock", args=(username,)
    )
    logger.debug("Sherlock - Task: %s", res.task_id)
    return jsonify(module="sherlock", task=res.task_id, param=username, from_m=from_m)


################################################
# Holehe
################################################
@home.route("/holehe", methods=["POST"])
def r_holehe():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Holehe - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.holehe.holehe_tasks.t_holehe", args=(username,))
    logger.debug("Holehe - Task: %s", res.task_id)
    return jsonify(module="holehe", task=res.task_id, param=username, from_m=from_m)


################################################
# Spotify
################################################
@home.route("/spotify", methods=["POST"])
def r_spotify():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "initial")
    proc = json_result.get("proc", 1)
    logger.info("Spotify - Detected Username: %s %s %s", username, from_m, proc)
    res = celery.send_task(
        "modules.spotify.spotify_tasks.t_spotify", args=(username, from_m, proc)
    )
    logger.debug("Spotify - Task: %s", res.task_id)
    return jsonify(
        module="spotify", task=res.task_id, param=username, from_m=from_m, proc=proc
    )


################################################
# Tinder
################################################
@home.route("/tinder", methods=["POST"])
def r_tinder():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Tinder - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.tinder.tinder_tasks.t_tinder", args=(username,))
    logger.debug("Tinder - Task: %s", res.task_id)
    return jsonify(module="tinder", task=res.task_id, param=username, from_m=from_m)


################################################
# Venmo
################################################
@home.route("/venmo", methods=["POST"])
def r_venmo():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Venmo - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.venmo.venmo_tasks.t_venmo", args=(username,))
    logger.debug("Venmo - Task: %s", res.task_id)
    return jsonify(module="venmo", task=res.task_id, param=username, from_m=from_m)


################################################
# Skype
################################################
@home.route("/skype", methods=["POST"])
def r_skype():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Skype - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.skype.skype_tasks.t_skype", args=(username,))
    logger.debug("Skype - Task: %s", res.task_id)
    return jsonify(module="skype", task=res.task_id, param=username, from_m=from_m)


################################################
# Searches
################################################
@home.route("/search", methods=["POST"])
def r_search():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Search - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.search.search_tasks.t_search", args=(username,))
    logger.debug("Search - Task: %s", res.task_id)
    return jsonify(module="search", task=res.task_id, param=username, from_m=from_m)


################################################
# Tweetiment
################################################
@home.route("/tweetiment", methods=["POST"])
def r_tweetiment():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    task_id = json_result.get("task_id", "")
    logger.info(
        "Tweetiment - Detected Username: %s %s %s",
        username,
        from_m,
        task_id,
    )
    res = celery.send_task(
        "modules.tweetiment.tweetiment_tasks.t_tweetiment",
        args=(username, task_id, from_m),
    )
    logger.debug("Tweetiment - Task: %s", res.task_id)
    return jsonify(module="tweetiment", task=res.task_id, param=username, from_m=from_m)


################################################
# Reddit
################################################
@home.route("/reddit", methods=["POST"])
def r_reddit():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Reddit - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.reddit.reddit_tasks.t_reddit", args=(username,))
    logger.debug("Reddit - Task: %s", res.task_id)
    return jsonify(module="reddit", task=res.task_id, param=username, from_m=from_m)


################################################
# Leaklookup
################################################
@home.route("/leaklookup", methods=["POST"])
def r_leaklookup():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Leaklookup - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.leaklookup.leaklookup_tasks.t_leaklookup", args=(username,)
    )
    logger.debug("Leaklookup - Task: %s", res.task_id)
    return jsonify(module="leaklookup", task=res.task_id, param=username, from_m=from_m)


################################################
# Twitch
################################################
@home.route("/twitch", methods=["POST"])
def r_twitch():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Twitch - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.twitch.twitch_tasks.t_twitch", args=(username,))
    logger.debug("Twitch - Task: %s", res.task_id)
    return jsonify(module="twitch", task=res.task_id, param=username, from_m=from_m)


################################################
# Mastodon
################################################
@home.route("/mastodon", methods=["POST"])
def r_mastodon():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("Mastodon - Detected Username: %s %s", username, from_m)
    res = celery.send_task(
        "modules.mastodon.mastodon_tasks.t_mastodon", args=(username,)
    )
    logger.debug("Mastodon - Task: %s", res.task_id)
    return jsonify(module="mastodon", task=res.task_id, param=username, from_m=from_m)


################################################
# Dorks
################################################
@home.route("/dorks", methods=["POST"])
def r_dorks():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    dorks = json_result.get("dorks", "")
    from_m = json_result.get("from", "")
    logger.info("Dorks - Detected Username: %s %s %s", username, dorks, from_m)
    res = celery.send_task("modules.dorks.dorks_tasks.t_dorks", args=(username, dorks))
    logger.debug("Dorks - Task: %s", res.task_id)
    return jsonify(module="dorks", task=res.task_id, param=username, from_m=from_m)


################################################
# PsbDmp
################################################
@home.route("/psbdmp", methods=["POST"])
def r_psbdmp():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info("PsbDmp - Detected Username: %s %s", username, from_m)
    res = celery.send_task("modules.psbdmp.psbdmp_tasks.t_psbdmp", args=(username,))
    logger.debug("PsbDmp - Task: %s", res.task_id)
    return jsonify(module="psbdmp", task=res.task_id, param=username, from_m=from_m)


################################################
# Twitter info for comparison (first account)
################################################
@home.route("/twitter_info", methods=["POST"])
def r_twitter_infof():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    if json_result.get("module_name", "") == "":
        module = "twitter_info"
    else:
        module = json_result.get("module_name", "")
    logger.info(
        "Twitter_info first - Detected Username: %s %s %s",
        username,
        from_m,
        module,
    )
    res = celery.send_task(
        "modules.twitter_comparison.twitter_info_tasks.t_twitter_info",
        args=(username, from_m, module),
    )
    logger.debug("Twitter_infof - Task: %s", res.task_id)
    return jsonify(module=module, task=res.task_id, param=username, from_m=from_m)


################################################
# Twitter info for comparison (second account)
################################################
@home.route("/twitter_infos", methods=["POST"])
def r_twitter_infos():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    logger.info(
        "Twitter_info second - Detected Username: %s %s",
        username,
        from_m,
    )
    res = celery.send_task(
        "modules.twitter_comparison.twitter_info_tasks.t_twitter_info", args=(username,)
    )
    logger.debug("Twitter_infos - Task: %s", res.task_id)
    return jsonify(
        module="twitter_infos", task=res.task_id, param=username, from_m=from_m
    )


################################################
# Twitter comp for comparison (first period)
################################################
@home.route("/twitter_comp", methods=["POST"])
def r_twitter_compf():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    date_from = json_result.get("date_from", "")
    date_to = json_result.get("date_to", "")
    from_m = json_result.get("from", "")
    if json_result.get("module_name", "") == "":
        module = "twitter_comp"
    else:
        module = json_result.get("module_name", "")
    logger.info(
        "Twitter_compf - Detected Username: %s %s %s %s %s",
        username,
        date_from,
        date_to,
        from_m,
        module,
    )
    res = celery.send_task(
        "modules.twitter_comparison.twitter_comp_tasks.t_twitter_comp",
        args=(username, date_from, date_to, from_m, module),
    )
    logger.debug("Twitter_compf - Task: %s", res.task_id)
    return jsonify(
        module=module,
        task=res.task_id,
        param=username,
        date_from=date_from,
        date_to=date_to,
        from_m=from_m,
    )


################################################
# Twitter comp for comparison (second period)
################################################
@home.route("/twitter_comps", methods=["POST"])
def r_twitter_comps():
    celery = create_celery(current_app)
    json_result = _get_json_or_400()
    username = json_result.get("username", "")
    date_from = json_result.get("date_from", "")
    date_to = json_result.get("date_to", "")
    from_m = json_result.get("from", "")
    logger.info(
        "Twitter_comps - Detected Username: %s %s %s %s",
        username,
        date_from,
        date_to,
        from_m,
    )
    res = celery.send_task(
        "modules.twitter_comparison.twitter_comp_tasks.t_twitter_comp",
        args=(username, date_from, date_to, from_m),
    )
    logger.debug("Twitter_comps - Task: %s", res.task_id)
    return jsonify(
        module="twitter_comps",
        task=res.task_id,
        param=username,
        date_from=date_from,
        date_to=date_to,
        from_m=from_m,
    )
