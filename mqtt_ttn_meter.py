import os
import time
import json
import csv
import logging
import base64
import paho.mqtt.client as mqtt
from datetime import datetime

# application settings
APP_ID = "dtz541-zdcl-tester@ttn"
ACCESS_KEY = "NNSXS.7DT2IDW3JDRAFZXUAWU6KIHX2A3SQNVVBAC2VCI.VL2CI4IMBFL47C6YKFHHXDHU276EHZTAC2J5JP4OJYWUFQ6H362A"
PUBLIC_TLS_ADDRESS = "eu1.cloud.thethings.network"
PUBLIC_TLS_ADDRESS_PORT = 1883 # this must be int. otherwise Unexpected error occurred: '<=' not supported between instances of 'str' and 'int'
REGION = "EU1"

# global settings
# global settings
LOG_FILE = "mqtt_client_" + APP_ID + ".log"
CSV_DIR = "payloads"
RECONNECT_MAX_ATTEMPTS = 12
RECONNECT_DELAY = 1

"""Task1: change uplink interval"""
# here define the expected uplink interval
# for old lora module firmware version, e.g. 2125, this uplink interval is suggested to 5-55 mins
EXPECTATION_UPLINK_INTERVAL_DATA_RECORD2 = None # unit: minute
list_uplink_interval_datarecord2_changed = []
"""Task2: """
# here define if you want to correct the RTC(real time constant)
RTC_TO_RESET = True
RTC_changed_successfully_list = []
#Note：
# Considering the communication capacity, the above two tasks are best performed separately.

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

def time_to_holley_downlink_hex(decimal_number,max_retry=3):
    try:
        # check if input is between 5-55
        if not isinstance(decimal_number, int) or not (5 <= decimal_number <= 55):
            logging.error(f"Invalid input: {decimal_number}. Must be an integer between 5 and 55.")
            return None
        if not isinstance(max_retry, int) or not (0 <= max_retry <= 255):
            logging.error(f"Invalid max_retry: {max_retry}. Must be an integer between 0 and 255.")
            return None
        hex_part = f"{decimal_number:08X}"
        
        downlink_hex = f"08{hex_part}00000000{max_retry}"
        
        return bytes.fromhex(downlink_hex)
    except Exception as e:
        logging.error(f"Error converting decimal to custom hex: {e}")
        return None

# create CSV DIR
os.makedirs(CSV_DIR, exist_ok=True)

# log file setting
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8')])


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
            self.client.subscribe('#',0) # all device uplink
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

    def send_downlink_msg(self,device_id,downlink_cmd_base64,f_port=2):
        try:
            # this works only for ttn. See below website for more topics
            # https://www.thethingsindustries.com/docs/integrations/mqtt/#subscribing-to-upstream-traffic
            topic_down = f'v3/{self.app_id}/devices/{device_id}/down/replace'
            context_downlink = '{"downlinks":[{"f_port": {f_port},"frm_payload":{downlink_cmd_base64},"priority": "NORMAL"}]}'
            self.client.publish(topic_down, context_downlink)
            logging.info(f"Downlink cmd{downlink_cmd_base64} sent to {device_id}")
        except Exception as e:
            logging.error(f"Error sending downlink message to device {device_id}: {e}")

    def on_message(self, client, userdata, msg):
        try:
            msg_json = json.loads(msg.payload)
            data = self.parse_payload_from_msg(msg_json)
            if data:
                received_at, application_id, device_id, payload, f_cnt, rssi, snr, consumed_airtime = data
                
                #Here to save all the paylaod to a csv file.
                self.save_payload(application_id, [received_at, device_id, payload, f_cnt, rssi, snr, consumed_airtime])
                
                if RTC_TO_RESET:
                    self.send_rtc_cmd(self,payload,device_id)
                    logging.debug('The RTC of {RTC_changed_successfully_list[-1]} was successfully changed!' )
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
    
    def send_rtc_cmd(self,payload,device_id):

        # commands set in hex code
        commands = {
            "cmd1": '040800401D017F00FF00E8',
            "cmd2": '010401401D0164',
            "cmd3": '040404401084E0'  # This will make LoRaWAN module reboot
        }

        # change hex cmd to Base64 cmd
        commands_base64 = {key: hex_to_base64(value) for key, value in commands.items()}

        if device_id not in RTC_changed_successfully_list:
            if payload == 0x840500401D0101E8:
                # cmd1 was successfully received by meter, send cmd2
                logging.info(f"Device {device_id}: cmd1 successfully received. Sending cmd2: {commands_base64['cmd2']}")
                # send cmd2
                self.send_downlink_msg(self,device_id,commands_base64['cmd2'])
            elif payload == 0xC40400401D0126:
                # cmd1 failed, send cmd1 again
                logging.warning(f"Device {device_id}: cmd1 failed. Retrying sending cmd1:{commands_base64['cmd1']}")
                self.send_downlink_msg(self,device_id,commands_base64['cmd1'])
            elif payload == 0x810801401D017F00FF0066:
                # cmd2 was successfully received, send cmd3 to reboot module
                logging.info(f"Device {device_id}: cmd2 successfully received. Sending cmd3 (reboot): {commands_base64['cmd3']}")
                self.send_downlink_msg(self,device_id,commands_base64["cmd3"])
                RTC_changed_successfully_list.append(device_id)
                logging.info(f"RTC changed successfully for devices: {RTC_changed_successfully_list[-1]}")
            elif payload == 0xC10401401D0124:
                # cmd2 failed, retry cmd2
                logging.warning(f"Device {device_id}: cmd2 failed. Retrying cmd2: {commands_base64['cmd2']}")
                self.send_downlink_msg(self,device_id,commands_base64['cmd2'])
            else:
                #send cmd1
                logging.warning(f"Device {device_id}: Received normal payload: {payload}, try to send cmd1:{commands_base64['cmd1']}")
                self.send_downlink_msg(self,device_id,commands_base64["cmd1"])

    
# run MQTT client
if __name__ == "__main__":

    mqtt_client_handler = MqttClientHandler(APP_ID, ACCESS_KEY, PUBLIC_TLS_ADDRESS, PUBLIC_TLS_ADDRESS_PORT, REGION,RTC_changed_successfully_list)
    mqtt_client_handler.start()
