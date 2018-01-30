#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
import time

from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS

# Import our modules
from modules.github.github_tasks import t_github
from modules.gitlab.gitlab_tasks import t_gitlab
from modules.username.username_tasks import t_username
from modules.keybase.keybase_tasks import t_keybase


f_app = Flask(__name__)
CORS(f_app)


# KKK : I think the api should handle the task times until obtain the result

################################################
# Github 
################################################
@f_app.route('/github', methods=["POST"])
def github():
    try:
        username = request.form['username']
        print "Github - Detected Username : ", username
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


################################################
# Gitlab 
################################################
@f_app.route('/gitlab', methods=["POST"])
def gitlab():
    try:
        username = request.form['username']
        print "Gitlab - Detected Username : ", username
        task_r = t_gitlab.delay(username)
        print "Task : ", task_r.id
        while (task_r.state != 'SUCCESS'):
            print "State : ", task_r.state
            time.sleep(1)
        print "Data : ", task_r.result
    except:
        return "{'state' : 'FAILURE'}"

    return jsonify(task_r.result)
		

################################################
# Username 
################################################
@f_app.route('/username', methods=["POST"])
def username():
    try:
        username = request.form['username']
        print "Username - Detected Username : ", username
        task_r = t_username.delay(username)
        print "Task : ", task_r.id
        while (task_r.state != 'SUCCESS'):
            print "State : ", task_r.state
            time.sleep(1)
        print "Data : ", task_r.result
    except:
        return "{'state' : 'FAILURE'}"

    return jsonify(task_r.result)
		

################################################
# Keybase 
################################################
@f_app.route('/keybase', methods=["POST"])
def keybase():
    try:
        username = request.form['username']
        print "Keybase - Detected Username : ", username
        task_r = t_keybase.delay(username)
        print "Task : ", task_r.id
        while (task_r.state != 'SUCCESS'):
            print "State : ", task_r.state
            time.sleep(1)
        print "Data : ", task_r.result
    except:
        return "{'state' : 'FAILURE'}"

    return jsonify(task_r.result)
		

if __name__ == '__main__':
    f_app.run(debug=True)
