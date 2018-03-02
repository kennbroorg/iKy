# -*- encoding: utf-8 -*-
from flask import Blueprint, current_app, request, jsonify
from factories._celery import create_celery
home = Blueprint('home_views', __name__)


@home.route('/')
def index():
    celery = create_celery(current_app)
    res = celery.send_task('tasks.simple_task', args=('-=-= TEST FROM VIEW =-=-',))
    print(res)
    return """
<!DOCTYPE html>
<html lang="en">
  <head><meta charset="utf-8">
    <title>Minimal Celery </title>
  </head>
  <body>'TASK {0} HAS BEEN RUN'</body>
</html>
""".format(res)


################################################
# Result 
################################################
#@app.route("/github_example/result/<task_id>", methods=["POST"])
@home.route("/result/<task_id>")
def github_result(task_id):
    celery = create_celery(current_app)
    result = celery.AsyncResult(task_id).get(timeout=10.0)
    # Do something with the timeout
    return repr(result)


################################################
# Github 
################################################
@home.route("/github/<username>")
def r_github(username=None):
    celery = create_celery(current_app)
    username = request.args.get("username", username)
    print "Github - Detected Username : ", username
    res = celery.send_task('github_tasks.t_github', args=(username, )) # ESTA ES LA PAPA, tiene que ser una TUPLA
    context = {"id": res.task_id, "param" : username}
    print "Task : ", res.task_id
    result = "github({})".format(context['param'])
    goto = "{}".format(context['id'])

    return jsonify(result=result, goto=goto)


################################################
# Keybase
################################################
@home.route("/keybase/<username>")
def r_keybase(username=None):
    celery = create_celery(current_app)
    username = request.args.get("username", username)
    print "Keybase - Detected Username : ", username
    res = celery.send_task('modules.keybase.keybase_tasks.t_keybase', args=(username, )) # ESTA ES LA PAPA, tiene que ser una TUPLA
    context = {"id": res.task_id, "param" : username}
    print "Task : ", res.task_id
    result = "keybase({})".format(context['param'])
    goto = "{}".format(context['id'])

    return jsonify(result=result, goto=goto)


################################################
# Gitlab
################################################
@home.route("/gitlab/<username>")
def r_gitlab(username=None):
    celery = create_celery(current_app)
    username = request.args.get("username", username)
    print "Gitlab - Detected Username : ", username
    res = celery.send_task('modules.gitlab.gitlab_tasks.t_gitlab', args=(username, )) # ESTA ES LA PAPA, tiene que ser una TUPLA
    context = {"id": res.task_id, "param" : username}
    print "Task : ", res.task_id
    result = "keybase({})".format(context['param'])
    goto = "{}".format(context['id'])

    return jsonify(result=result, goto=goto)


################################################
# Usersearch 
################################################
@home.route("/usersearch/<username>")
def r_usersearch(username=None):
    celery = create_celery(current_app)
    username = request.args.get("username", username)
    print "Usersearch - Detected Username : ", username
    res = celery.send_task('modules.usersearch.usersearch_tasks.t_usersearch', args=(username, )) # ESTA ES LA PAPA, tiene que ser una TUPLA
    context = {"id": res.task_id, "param" : username}
    print "Task : ", res.task_id
    result = "keybase({})".format(context['param'])
    goto = "{}".format(context['id'])

    return jsonify(result=result, goto=goto)

