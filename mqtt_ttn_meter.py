import os
import time
import json
import csv
import logging
import base64
import paho.mqtt.client as mqtt
from datetime import datetime

# application settings
APP_ID = os.getenv("APP_ID", "solhusene@ttn")
ACCESS_KEY = os.getenv("ACCESS_KEY", "NNSXS.LMAIX5XT2RKDPWJ7YQ2LZHQISXNOWLHD3GLZZZQ.HL445QIQV3QTA23R5JXBUREBC2WUDZ5FJMNWJX2S53WTOYBPOWWQ")
PUBLIC_TLS_ADDRESS = os.getenv("PUBLIC_TLS_ADDRESS", "eu1.cloud.thethings.network")
PUBLIC_TLS_ADDRESS_PORT = int(os.getenv("PUBLIC_TLS_ADDRESS_PORT", "8883"))
REGION = os.getenv("REGION", "EU1")

downlink_sent_meter_list = ['lora-el-solh8-st-tv']
#downlink commando for changing interval of data record 2 to 60min
DATA2_INTERVAL = 0x080000


# global settings
LOG_FILE = "mqtt_client.log"
CSV_DIR = "payloads"
RECONNECT_MAX_ATTEMPTS = 12
RECONNECT_DELAY = 1

EXPECTATION_UPLINK_INTERVAL_DATA_RECORD2 = 60 # unit: minute


# tool function：Base64 to Hex
def base64_to_hex(base64_data):
    try:
        binary_data = base64.b64decode(base64_data)
        hex_data = binary_data.hex()
        return hex_data
    except Exception as e:
        logging.error(f"Error converting Base64 to Hex: {e}")
        return None

# tool function：Hex to Base64
def hex_to_base64(hex_in):
    try:
        bytes_data = bytes.fromhex(hex_in)
        base64_data = base64.b64encode(bytes_data).decode('utf-8')
        return base64_data
    except Exception as e:
        logging.error(f"Error converting Hex to Base64: {e}")
        return None

def time_to_holley_downlink_hex(decimal_number,max_retry):
    try:
        # check if input is between 5-500
        if not isinstance(decimal_number, int) or not (5 <= decimal_number <= 500):
            logging.error(f"Invalid input: {decimal_number}. Must be an integer between 5 and 500.")
            return None
        
        hex_part = f"{decimal_number:08X}"
        
        downlink_hex = f"08{hex_part}00000000{max_retry}"
        
        return downlink_hex
    except Exception as e:
        logging.error(f"Error converting decimal to custom hex: {e}")
        return None
reset_RTC_cmd1 = '040800401D017F00FF00E8'
reset_RTC_cmd2 = '010401401D0164'
reset_RTC_cmd3 = '040404401084E0' #this will make lorawann module reboot

reset_RTC_cmd1_base64 = hex_to_base64(reset_RTC_cmd1)
reset_RTC_cmd2_base64 = hex_to_base64(reset_RTC_cmd2)
reset_RTC_cmd3_base64 = hex_to_base64(reset_RTC_cmd3)

# create CSV DIR
os.makedirs(CSV_DIR, exist_ok=True)

# log file setting
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])


class MqttClientHandler:
    def __init__(self, app_id, access_key, address, port, region,downlink_sent_list):
        self.app_id = app_id
        self.access_key = access_key
        self.address = address
        self.port = port
        self.region = region
        self.client = mqtt.Client()
        self.downlink_sent_list = downlink_sent_list
        self.setup_client()
        
    def setup_client(self):
        self.client.username_pw_set(username=f"{self.app_id}@{self.region}", password=self.access_key)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def start(self):
        try:
            self.client.connect(self.address, self.port, 60)
            self.client.loop_forever()
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info(f"Connected to broker with result code {rc}")

            # this works only for ttn. See below website for more topics
            # https://www.thethingsindustries.com/docs/integrations/mqtt/#subscribing-to-upstream-traffic
            self.client.subscribe(f"v3/{self.app_id}@{self.region}/devices/+/up")
        else:
            logging.error(f"Failed to connect, return code {rc}")

    def send_downlink_msg(self,device_id,downlink_cmd_base64):
        try:
            # this works only for ttn. See below website for more topics
            # https://www.thethingsindustries.com/docs/integrations/mqtt/#subscribing-to-upstream-traffic
            topic_down = f'v3/{APP_ID}/devices/{device_id}/down/replace'
            context_downlink_changeInterval = '{"downlinks":[{"f_port": 2,"frm_payload":{downlink_cmd_base64},"priority": "NORMAL"}]}'
            logging.info(f"Reset cmd{downlink_cmd_base64} sent to {device_id}")
        except Exception as e:
            logging.error(f"Error sending downlink message to device {device_id}: {e}")

    def on_message(self, client, userdata, msg):
        try:
            msg_json = json.loads(msg.payload)
            data = self.parse_payload_from_msg(msg_json)
            if data:
                received_at, application_id, device_id, payload, f_cnt, rssi, snr, consumed_airtime = data
                self.save_payload(application_id, [received_at, device_id, payload, f_cnt, rssi, snr, consumed_airtime])
                if device_id not in self.downlink_sent_list:
                    self.send_downlink_msg(self,device_id,reset_RTC_cmd1_base64)
                    time.sleep(0.2)
                    self.send_downlink_msg(self,device_id,reset_RTC_cmd2_base64)
                    time.sleep(0.2)
                    self.send_downlink_msg(self,device_id,reset_RTC_cmd3_base64)

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
        except Exception as e:
            logging.error(f"Error processing message: {e}")

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
                csv_writer = csv.writer(f)
                csv_writer.writerow(data)
            logging.info(f"Data saved for device {data[1]}")
        except Exception as e:
            logging.error(f"Failed to save data for device {data[1]}: {e}")



# run MQTT client
if __name__ == "__main__":

    mqtt_client_handler = MqttClientHandler(APP_ID, ACCESS_KEY, PUBLIC_TLS_ADDRESS, PUBLIC_TLS_ADDRESS_PORT, REGION,downlink_sent_meter_list)
    mqtt_client_handler.start()
