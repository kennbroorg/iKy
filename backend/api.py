#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
import time

from flask import Flask
from flask import jsonify
from flask import request

# Import our modules
from modules.github.github_tasks import t_github
from modules.gitlab.gitlab_tasks import t_gitlab
from modules.username.username_tasks import t_username
from modules.keybase.keybase_tasks import t_keybase


f_app = Flask(__name__)


# KKK : I think the api should handle the task times until obtain the result

@f_app.route('/github', methods=["POST"])
def github():
    try:
        username = request.form['username']
        print "Detected Username : ", username
        task_r = t_github.delay(username)
        print "Task : ", task_r.id
        while (task_r.state != 'SUCCESS'):
            print "State : ", task_r.state
            time.sleep(1)
        print "Data : ", task_r.result
    except:
        return "{'state' : 'FAILURE'}"

    return jsonify(task_r.result)
		

@f_app.route('/github-redis', methods=["POST"])
def github_redis():
    try:
        username = request.form['username']
        print "Detected Username : ", username
        task_r = t_github.delay(username)
        print "Task : ", r.id
    except:
       return "{'state' : 'FAILURE'}"

    return jsonify(task_r.result)


if __name__ == '__main__':
    f_app.run(debug=True)
