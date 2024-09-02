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


###
#User = "lorawan-reklamation@ttn"
#Password = "NNSXS.Y7HN3T6DDDLKCVPCEKTXXWP3M5UKWZJPI2U3MAY.SV4ZAYABRRYGBP3SFJRFU4HJNDYWLUE3JTQFFY75THQJCM7ETYLQ"

APP_ID = "test-new-lorawan-meter@ttn"
ACCESS_KEY  = "NNSXS.EZU3DMV7RUYRTARJDCCSBQBMO5NR4BW7BGWKHSA.3BOTSIMIWAB3RT2QZR47P43PYEFPCGCTXR3GDBDZPTCCMT64NY5A"
PUBLIC_TLS_ADDRESS = "eu1.cloud.thethings.network"
PUBLIC_TLS_ADDRESS_PORT = "8883"
REGION = "EU1"

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

    return received_at,application_id,device_id,payload,f_cnt,f_port

class OnlineAnomalyDetector:
    def __init__(self, threshold):
        self.previous_value = None
        self.threshold = threshold
        self.anomalies = []

    def process(self, timestamp, current_value):
        # at first time there is no previous value
        if self.previous_value is None:
            self.previous_value = current_value
            return

        # 检测电量消耗递减
        if current_value < self.previous_value:
            self.anomalies.append((timestamp, 'Consumption Decrease'))

        # 检测电量消耗差距过大
        if abs(current_value - self.previous_value) > self.threshold:
            self.anomalies.append((timestamp, 'Excessive Consumption Difference'))

        # 更新前一个值
        self.previous_value = current_value

    def get_anomalies(self):
        return self.anomalies

class PayloadDecoder:
    def __init__(self,payload) -> None:
        self.payload = payload

    def process_data_record1(self):
        pass


    def process_data_record2(self):
        pass

# 实例化检测器，假设阈值为10
detector = OnlineAnomalyDetector(threshold=10)

# 构造MQTT客户端连接TTN
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # 订阅应用的主题以获取所有设备的数据
    client.subscribe(f"v3/{APP_ID}@{REGION}/devices/+/up")

# 当消息到达时的回调函数
def on_message(client, userdata, msg):
    #print(f"Topic: {msg.topic}\nPayload: {msg.payload.decode()}")
    msg_json = json.loads(msg.payload)
    received_at,application_id,device_id,payload,f_cnt,f_port = parse_payload_from_msg(msg_json)
    with open('payload.csv','a') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([received_at,application_id,device_id,payload,f_cnt,f_port])
# 配置MQTT客户端
client = mqtt.Client()
client.username_pw_set(username=f"{APP_ID}@{REGION}", password=ACCESS_KEY)

client.on_connect = on_connect
client.on_message = on_message

# 连接到TTN的MQTT代理
client.connect(f"{REGION}.cloud.thethings.network", 1883, 60)
client.subscribe('#',0) # all decice uplink

try:
    running = True
    while running:
        client.loop(10)
        print('.',end="",flush=True)

except KeyboardInterrupt:
    print("Program exit.")
    sys.exit(0)
