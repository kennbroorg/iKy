#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys

from flask import Flask
from flask import jsonify
from flask import request

# Import our modules
from modules.github.github_tasks import t_github
from modules.gitlab.gitlab_tasks import t_gitlab
from modules.username.username_tasks import t_username
from modules.keybase.keybase_tasks import t_keybase

import time # KKK

f_app = Flask(__name__)


@f_app.route('/github', methods=["POST"])
def github():
    if request.method == "POST":
        username = request.form['username']
        print "Username detectado : ", username
        r = t_github.delay(username)
        print "Tarea lanzada a celery"
        print "Tarea : ", r
        while (r.state != 'SUCCESS'):
            print "Estado : ", r.state
            time.sleep(2)

        print "Resultado : ", r.result

#        r_github = r
    else:
        r_github = "MAL"

    # print r
    return jsonify(r.result)
		

if __name__ == '__main__':
    f_app.run(debug=True)
