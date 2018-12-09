# -*- encoding: utf-8 -*-
from flask import Blueprint, current_app, request, jsonify
from factories._celery import create_celery
from factories.configuration import api_keys_read, api_keys_write
home = Blueprint('home_views', __name__)


################################################
# Testing
################################################
@home.route("/testing", methods=["POST"])
def r_testing():
    result = request.get_json()
    print("JSON : ", result)
    return jsonify(result)


################################################
# Task List
################################################
# @home.route("/tasklist", methods=["POST"])
@home.route('/tasklist', methods=['GET'])
def r_tasklist():
    module_list = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint != 'static':
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
    res = celery.AsyncResult(task_id).get()
    return jsonify(result=res)


################################################
# API Keys
################################################
@home.route("/apikey", methods=["POST"])
def r_apikey():
    if request.json:
        api_keys = request.get_json()
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
    json_result = request.get_json()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    print("Fullcontact - Detected Username : ", username, from_m)
    res = celery.send_task('modules.fullcontact.fullcontact_tasks.' +
                           't_fullcontact', args=(username, ))
    print("Task : ", res.task_id)
    return jsonify(module="fullcontact", task=res.task_id, param=username)


################################################
# Github
################################################
@home.route("/github", methods=["POST"])
def r_github():
    celery = create_celery(current_app)
    json_result = request.get_json()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    print("Github - Detected Username : ", username, from_m)
    res = celery.send_task('modules.github.github_tasks.t_github',
                           args=(username, from_m))
    print("Task : ", res.task_id)
    return jsonify(module="github", task=res.task_id, param=username)


################################################
# GhostProject
################################################
@home.route("/ghostproject", methods=["POST"])
def r_ghostproject():
    celery = create_celery(current_app)
    json_result = request.get_json()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    print("GhostProject - Detected Username : ", username, from_m)
    res = celery.send_task(
        'modules.ghostproject.ghostproject_tasks.t_ghostproject',
                           args=(username, ))
    print("Task : ", res.task_id)
    return jsonify(module="ghostproject", task=res.task_id, param=username)


################################################
# Keybase
################################################
@home.route("/keybase", methods=["POST"])
def r_keybase():
    celery = create_celery(current_app)
    json_result = request.get_json()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    print("Keybase - Detected Username : ", username, from_m)
    res = celery.send_task('modules.keybase.keybase_tasks.t_keybase',
                           args=(username, from_m))
    print("Task : ", res.task_id)
    return jsonify(module="keybase", task=res.task_id, param=username)


################################################
# Twitter
################################################
@home.route("/twitter", methods=["POST"])
def r_twitter():
    celery = create_celery(current_app)
    json_result = request.get_json()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    print("Twitter - Detected Username : ", username, from_m)
    res = celery.send_task('modules.twitter.twitter_tasks.t_twitter',
                           args=(username, from_m))
    print("Task : ", res.task_id)
    return jsonify(module="twitter", task=res.task_id, param=username)


################################################
# Linkedin
################################################
@home.route("/linkedin", methods=["POST"])
def r_linkedin():
    celery = create_celery(current_app)
    json_result = request.get_json()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    print("Linkedin - Detected Username : ", username, from_m)
    res = celery.send_task('modules.linkedin.linkedin_tasks.t_linkedin',
                           args=(username, from_m))
    print("Task : ", res.task_id)
    return jsonify(module="linkedin", task=res.task_id, param=username)


################################################
# Leaks
################################################
@home.route("/leaks", methods=["POST"])
def r_leaks():
    celery = create_celery(current_app)
    json_result = request.get_json()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    print("Leaks - Detected Username : ", username, from_m)
    res = celery.send_task('modules.leaks.leaks_tasks.t_leaks',
                           args=(username, ))
    print("Task : ", res.task_id)
    return jsonify(module="leaks", task=res.task_id, param=username)


################################################
# Gitlab
################################################
@home.route("/gitlab", methods=["POST"])
def r_gitlab(username=None):
    celery = create_celery(current_app)
    json_result = request.get_json()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    print("Gitlab - Detected Username : ", username, from_m)
    res = celery.send_task('modules.gitlab.gitlab_tasks.t_gitlab',
                           args=(username, ))
    print("Task : ", res.task_id)
    return jsonify(module="gitlab", task=res.task_id, param=username)


################################################
# Usersearch
################################################
@home.route("/usersearch", methods=["POST"])
def r_usersearch(username=None):
    celery = create_celery(current_app)
    json_result = request.get_json()
    username = json_result.get("username", "")
    from_m = json_result.get("from", "")
    print("Usersearch - Detected Username : ", username, from_m)
    res = celery.send_task('modules.usersearch.usersearch_tasks.t_usersearch',
                           args=(username, ))
    print("Task : ", res.task_id)
    return jsonify(module="usersearch", task=res.task_id, param=username)
