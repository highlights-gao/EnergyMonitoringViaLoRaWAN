""" import os
import time
import sys
import paho.mqtt.client as mqtt
import json
import csv
import random
from datetime import datetime
import logging
import base64


###
#User = "lorawan-reklamation@ttn"
#Password = "NNSXS.Y7HN3T6DDDLKCVPCEKTXXWP3M5UKWZJPI2U3MAY.SV4ZAYABRRYGBP3SFJRFU4HJNDYWLUE3JTQFFY75THQJCM7ETYLQ"

# application settings
APP_ID = "test-new-lorawan-meter@ttn"
ACCESS_KEY = "NNSXS.INRWPGNRQD4QJUS54BQA2ZTBUU5I7T5LIMRSA5Q.H3C5QN3IRRSUEHXJCJ4VEJFGEQAM3BB4RCYVRNKNJLIOAR2KRM5Q"
PUBLIC_TLS_ADDRESS = "eu1.cloud.thethings.network"
PUBLIC_TLS_ADDRESS_PORT = 1883 # this must be int. otherwise Unexpected error occurred: '<=' not supported between instances of 'str' and 'int'
REGION = "EU1"

import contextlib
import paho.mqtt.publish as publish

publish.single(f"v3/{APP_ID}/devices/meter-id-1hly0324031629/down/push", '{"downlinks":[{"f_port": 15,"frm_payload":"CAAAAAUAAAAAAw==","priority": "NORMAL"}]}', hostname=PUBLIC_TLS_ADDRESS, port=1883, auth={'username':APP_ID,'password':ACCESS_KEY})

 """


def time_to_holley_downlink_hex(unconfirmed_interval,confirmed_interval=0,max_retry=3):
    try:
        # check if input is between 5-55
        if not isinstance(unconfirmed_interval, int) or not (5 <= unconfirmed_interval <= 55):
            unconfirmed_interval = 15
        if not isinstance(max_retry, int) or not (0 <= max_retry <= 255):

            return None
        hex_bytes_unconfirmed_interval = unconfirmed_interval.to_bytes(4, 'big')
        prefix = 0x08.to_bytes(1,'big')
        hex_bytes_confirmed_interval = confirmed_interval.to_bytes(4,'big')
        hex_bytes_max_try = max_retry.to_bytes(1,'big')
        return prefix + hex_bytes_unconfirmed_interval + hex_bytes_confirmed_interval + hex_bytes_max_try
    except Exception as e:
        print(e)
        return None
    

print(time_to_holley_downlink_hex(10,15))