"""
Author: Jianguang Gao
Date: 2024/09/25
Contact: jianguang.gao@diinno.de

This is an example python script for change uplink interval or reset RTC parameter of holley meters via MQTT.

MQTT topics may work only for ttn. See below website for more topics
https://www.thethingsindustries.com/docs/integrations/mqtt/#subscribing-to-upstream-traffic  

Also, the json payload parser may only be for ttn format usable
"""

import os
import time
import json
import csv
import logging
import base64
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import contextlib

# application settings
APP_ID = "test-new-lorawan-meter@ttn"
ACCESS_KEY = "NNSXS.QGXFCGLMZ5Q3DTBGPJ4IBUKALQCHYWWTSWRZUEQ.TDTJY52P5SG6DJN2LD3WATQTWPWMVRZRX2WGUT5RNOUOYWKYNEFQ"
PUBLIC_TLS_ADDRESS = "eu1.cloud.thethings.network"
PUBLIC_TLS_ADDRESS_PORT = 1883
REGION = "EU1"

# global settings
LOG_DIR = 'mqtt_client_log'
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'log_{APP_ID}.log')
CSV_DIR = "payloads"
os.makedirs(CSV_DIR, exist_ok=True)

RECONNECT_MAX_ATTEMPTS = 12
RECONNECT_DELAY = 1 

# Uplink interval configurations
EXPECTATION_UPLINK_INTERVAL_DATA_RECORD2 = 5  # unit: minute; when RTC_TO_RESET = False
RTC_TO_RESET = False
list_uplink_interval_datarecord2_changed = []
RTC_changed_successfully_list = []

# Log file setting
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8')])

def base64_to_hex(base64_data):
    try:
        return base64.b64decode(base64_data).hex()
    except Exception:
        logging.error("Error converting Base64 to Hex")
        return None

def hex_to_base64(hex_in):
    try:
        return base64.b64encode(bytes.fromhex(hex_in)).decode('utf-8')
    except Exception:
        logging.error("Error converting Hex to Base64")
        return None

def time_to_holley_downlink_hex(unconfirmed_interval, confirmed_interval=0, max_retry=3):
    if not (5 <= unconfirmed_interval <= 55):
        logging.error(f"Invalid input: {unconfirmed_interval}. Must be an integer between 5 and 55.")
        unconfirmed_interval = 15
    
    if not (0 <= max_retry <= 255):
        logging.error(f"Invalid max_retry: {max_retry}. Must be an integer between 0 and 255.")
        return None

    hex_bytes_unconfirmed_interval = unconfirmed_interval.to_bytes(4, 'big').hex()
    hex_bytes_confirmed_interval = confirmed_interval.to_bytes(4, 'big').hex()
    hex_bytes_max_try = max_retry.to_bytes(1, 'big').hex()
    return '08' + hex_bytes_unconfirmed_interval + hex_bytes_confirmed_interval + hex_bytes_max_try

class MqttClientHandler:
    def __init__(self, app_id, access_key, address, port, region):
        self.app_id = app_id
        self.access_key = access_key
        self.address = address
        self.port = port
        self.region = region
        self.client = mqtt.Client()
        self.setup_client()
        
    def setup_client(self):
        self.client.username_pw_set(username=f"{self.app_id}@{self.region}", password=self.access_key)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def start(self):
        try:
            self.client.connect(self.address, self.port, 60)
            self.client.subscribe('#', 0)
            self.client.loop_forever()
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to broker")
            self.client.subscribe(f"v3/{self.app_id}@{self.region}/devices/+/up")
        else:
            logging.error(f"Failed to connect, return code {rc}")

    def send_downlink_msg(self, device_id, downlink_cmd_base64, f_port=2):
        topic_down = f'v3/{self.app_id}/devices/{device_id}/down/replace'
        context_downlink = json.dumps({"downlinks": [{"f_port": f_port, "frm_payload": downlink_cmd_base64, "priority": "NORMAL"}]})
        try:
            publish.single(topic_down, context_downlink, hostname=self.address, port=1883,
                           auth={'username': self.app_id, 'password': self.access_key})
            logging.info(f"Downlink cmd sent to {device_id}")
        except Exception as e:
            logging.error(f"Error sending downlink message to device {device_id}: {e}")

    def on_message(self, client, userdata, msg):
        try:
            msg_json = json.loads(msg.payload)
            data = self.parse_payload_from_msg(msg_json)
            if data:
                self.handle_received_data(data)

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
        except Exception as e:
            logging.error(f"Error processing message: {e}")

    def handle_received_data(self, data):
        received_at, application_id, device_id, payload, f_cnt, rssi, snr, consumed_airtime = data
        self.save_payload(application_id, [received_at, device_id, payload, f_cnt, rssi, snr, consumed_airtime])

        if isinstance(EXPECTATION_UPLINK_INTERVAL_DATA_RECORD2, int) and device_id not in list_uplink_interval_datarecord2_changed:
            downlink_interval_hex = time_to_holley_downlink_hex(EXPECTATION_UPLINK_INTERVAL_DATA_RECORD2)
            if downlink_interval_hex:
                downlink_interval_base64 = hex_to_base64(downlink_interval_hex)
                self.send_downlink_msg(device_id, downlink_interval_base64)
                list_uplink_interval_datarecord2_changed.append(device_id)
                logging.debug(f"The uplink interval for {device_id} was changed to {EXPECTATION_UPLINK_INTERVAL_DATA_RECORD2} mins!")

        if RTC_TO_RESET:
            self.send_rtc_cmd(payload, device_id)

    def on_disconnect(self, client, userdata, rc):
        logging.warning(f"Disconnected with result code: {rc}")
        self.reconnect_with_backoff()

    def reconnect_with_backoff(self):
        attempt, delay = 0, RECONNECT_DELAY
        while attempt < RECONNECT_MAX_ATTEMPTS:
            logging.info(f"Attempting to reconnect in {delay} seconds...")
            time.sleep(delay)
            try:
                self.client.reconnect()
                logging.info("Reconnected successfully!")
                return
            except Exception as e:
                logging.error(f"Reconnect attempt {attempt + 1} failed: {e}")
            attempt += 1
            delay = min(delay * 2, 60)
        logging.error(f"Failed to reconnect after {RECONNECT_MAX_ATTEMPTS} attempts, giving up.")

    @staticmethod
    def parse_payload_from_msg(msg_json):
        try:
            end_device_ids = msg_json["end_device_ids"]
            device_id = end_device_ids["device_id"]
            application_id = end_device_ids["application_ids"]["application_id"]
            received_at = msg_json["received_at"]
            uplink_message = msg_json["uplink_message"]
            f_cnt = uplink_message["f_cnt"]
            frm_payload = uplink_message["frm_payload"]
            payload = base64_to_hex(frm_payload)
            rssi = uplink_message["rx_metadata"][0]["rssi"]
            snr = uplink_message["rx_metadata"][0]["snr"]
            consumed_airtime = uplink_message["consumed_airtime"]

            return received_at, application_id, device_id, payload, f_cnt, rssi, snr, consumed_airtime
        except KeyError as e:
            logging.error(f"Missing key in message JSON: {e}")
        except Exception as e:
            logging.error(f"Error parsing payload from message: {e}")
        return None

    @staticmethod
    def save_payload(application_id, data):
        file_path = os.path.join(CSV_DIR, f'payload_{application_id}.csv')
        try:
            with open(file_path, 'a', newline='') as f:
                csv.writer(f).writerow(data)
            logging.info(f"Data saved for device {data[1]}")
        except Exception as e:
            logging.error(f"Failed to save data for device {data[1]}: {e}")

    def send_rtc_cmd(self, payload, device_id):
        commands = {
            "cmd1": '040800401D017F00FF00E8',
            "cmd2": '010401401D0164',
            "cmd3": '040404401084E0'  # This will make LoRaWAN module reboot
        }

        commands_base64 = {key: hex_to_base64(value) for key, value in commands.items()}

        if device_id not in RTC_changed_successfully_list:
            if payload == 0x840500401D0101E8:
                self.send_downlink_msg(device_id, commands_base64['cmd2'])
            elif payload == 0xC40400401D0126:
                self.send_downlink_msg(device_id, commands_base64['cmd1'])
            elif payload == 0x810801401D017F00FF0066:
                self.send_downlink_msg(device_id, commands_base64['cmd3'])
                RTC_changed_successfully_list.append(device_id)
                logging.info(f"RTC changed successfully for device: {device_id}")
            elif payload == 0xC10401401D0124:
                self.send_downlink_msg(device_id, commands_base64['cmd2'])
            else:
                self.send_downlink_msg(device_id, commands_base64['cmd1'])

# run MQTT client
if __name__ == "__main__":
    mqtt_client_handler = MqttClientHandler(APP_ID, ACCESS_KEY, PUBLIC_TLS_ADDRESS, PUBLIC_TLS_ADDRESS_PORT, REGION)
    mqtt_client_handler.start()
