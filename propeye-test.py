import os
import time
import sys
import paho.mqtt.client as mqtt
import json
import csv
import random
from datetime import datetime
import logging
import base64
import contextlib
import paho.mqtt.publish as publish

APP_ID = "hly-multiple-batch-test@ttn"
ACCESS_KEY  = "NNSXS.DZTEOFEW7YRVBWJVZWS7L6HA654PNPT7AEJZMSQ.MXK6EFUSGE6F6TOZJQ2EERBUTTJ6GUV42OBV7GANTSWKH7C663NQ"
PUBLIC_TLS_ADDRESS = "eu1.cloud.thethings.network"
PUBLIC_TLS_ADDRESS_PORT = "8883"
REGION = "EU1"

NUM_DEVICE = 2

def base64_to_hex(base64_data):
    # decode Base64 data
    binary_data = base64.b64decode(base64_data)  
    # 
    hex_data = binary_data.hex()
    return hex_data

def parse_payload_from_msg(msg_json):
    end_device_ids = msg_json["end_device_ids"]
    device_id = end_device_ids["device_id"]
    application_id = end_device_ids["application_ids"]["application_id"]
    received_at = msg_json["received_at"]
    uplink_message = msg_json["uplink_message"]
    f_port = uplink_message["f_port"]
    f_cnt = uplink_message["f_cnt"]
    frm_payload = uplink_message["frm_payload"]
    payload = base64_to_hex(frm_payload)
    rssi = uplink_message["rx_metadata"][0]["rssi"]
    snr = uplink_message["rx_metadata"][0]["snr"]
    data_rate_index = uplink_message["settings"]["data_rate"]
    consumed_airtime = uplink_message["consumed_airtime"]

    return received_at,application_id,device_id,payload,f_cnt,rssi,snr,consumed_airtime


## 
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(f"v3/{APP_ID}@{REGION}/devices/+/up")

# 
def on_message(client, userdata, msg):
    #print(f"Topic: {msg.topic}\nPayload: {msg.payload.decode()}")
    interval_changed_list = []
    msg_json = json.loads(msg.payload)
    received_at,application_id,device_id,payload,f_cnt,rssi,snr,consumed_airtime = parse_payload_from_msg(msg_json)
    #Here you can save these data as you need
    with open('payload.csv','a') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([received_at,application_id,device_id,payload,f_cnt,rssi,snr,consumed_airtime])


    frm_paylaod_hex_5min = 0x08000000050000000003
    frm_payload_base64_6min = "CAAAAAYAAAAAAw=="
    frm_paylaod_hex_reboot = 0x040404401084E0
    frm_paylaod_base64_reboot = "BAQEQBCE4A=="

    if device_id not in interval_changed_list:

        topic_down = f'v3/{APP_ID}/devices/{device_id}/down/replace'
        context_downlink_changeInterval = '{"downlinks":[{"f_port": 2,"frm_payload": "CAAAAAYAAAAAAw==","priority": "NORMAL"}]}'
        hostname= PUBLIC_TLS_ADDRESS
        port=1883
        auth={'username':APP_ID,'password':ACCESS_KEY}

        publish.single(topic_down,context_downlink_changeInterval,hostname=hostname,port=port,auth=auth)
        interval_changed_list.append(device_id)


# set up mqttt client
client = mqtt.Client()
client.username_pw_set(username=f"{APP_ID}@{REGION}", password=ACCESS_KEY)

client.on_connect = on_connect
client.on_message = on_message

client.connect(PUBLIC_TLS_ADDRESS, 1883, 60)
client.subscribe('#',0) # all device uplink



FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

def on_disconnect(client, userdata, rc):
    logging.info("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logging.info("Reconnected successfully!")
            return
        except Exception as err:
            logging.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)


try:
   client.loop_forever()
except Exception as e:
    print("Soomething happened:",e)
finally:
    client.on_disconnect = on_disconnect