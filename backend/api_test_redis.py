#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import requests
import redis

r = requests.post('http://127.0.0.1:5000/github-redis', data = {'username':'usuario'})

task_id = r.content
print "La tarea es : ", task_id

# Redis connection
conn = redis.StrictRedis(host='localhost', port=6379)

data = conn.get('celery-task-meta-' + task_id)

print data
