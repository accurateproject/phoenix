import sys
import random
import requests
from gluon.contrib.appconfig import AppConfig


myconf = AppConfig(reload=False)

def call(method, *args):
    method = 'ApierV2.' + method if '.' not in method else method
    try:
        r = requests.post(myconf.get('accurate.server'),
            json = {'id':random.randint(1, sys.maxint), 'method': method, 'params':args})
    except requests.exceptions.ConnectionError as e:
        return e
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return e
    try:
        response = r.json()
    except ValueError as e:
        return e
    return response
