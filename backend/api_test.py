#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import requests

r = requests.post('http://127.0.0.1:5000/github', data = {'1username':'usuario'})

print r.content
