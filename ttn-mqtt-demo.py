#
import os 
import sys
import paho.mqtt.client as mqtt
import json
import logging
import base64
import csv
###
User = "lorawan-reklamation@ttn"
Password = "NNSXS.Y7HN3T6DDDLKCVPCEKTXXWP3M5UKWZJPI2U3MAY.SV4ZAYABRRYGBP3SFJRFU4HJNDYWLUE3JTQFFY75THQJCM7ETYLQ"
PUBLIC_TLS_ADDRESS = "eu1.cloud.thethings.network"
PUBLIC_TLS_ADDRESS_PORT = "8883"
theRegion = "EU1"

def base64_to_hex(base64_data):
    # decode Base64 data
    binary_data = base64.b64decode(base64_data)  
    # 
    hex_data = binary_data.hex()
    return hex_data
    
# MQTT event functions
def on_connect(mqttc, obj, flags, rc):
    print("\nConnect: rc = " + str(rc))

def on_message(mqttc, obj, msg):
    print("\nMessage: " + msg.topic + " " + str(msg.qos)) # + " " + str(msg.payload))
    parsedJSON = json.loads(msg.payload)
    device_id = parsedJSON['end_device_ids']['device_id']
    application_id = parsedJSON['end_device_ids']['application_ids']['application_id']
    received_time = parsedJSON['received_at']
    frm_payload = parsedJSON['uplink_message']['frm_payload']
    payload = base64_to_hex(frm_payload)
    
    #application log
    path_file_app = application_id + '.txt'
    if (not os.path.isfile(path_file_app)):
        with open(path_file_app,'a',newline='') as f:
            fw = csv.writer(f,dialect='excel-tab')
            fw.writerow([device_id,payload,received_time])
    
def on_subscribe(mqttc, obj, mid, granted_qos):
    print("\nSubscribe: " + str(mid) + " " + str(granted_qos))

def on_log(mqttc, obj, level, string):
    print("\nLog: "+ string)
    logging_level = mqtt.LOGGING_LEVEL[level]
    logging.log(logging_level, string)

print("Init mqtt client")
mqttc = mqtt.Client()

print("Assign callbacks")
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_message = on_message
#mqttc.on_log = on_log		# Logging for debugging OK, waste

print("Connect")
# Setup authentication from settings above
mqttc.username_pw_set(User, Password)


# IMPORTANT - this enables the encryption of messages
mqttc.tls_set()	# default certification authority of the system

#mqttc.tls_set(ca_certs="mqtt-ca.pem") # Use this if you get security errors
# It loads the TTI security certificate. Download it from their website from this page: 
# https://www.thethingsnetwork.org/docs/applications/mqtt/api/index.html
# This is normally required if you are running the script on Windows


mqttc.connect(theRegion.lower() + ".cloud.thethings.network", 8883, 60)


print("Subscribe")
mqttc.subscribe("#", 0)	# all device uplinks

print("And run forever")
try:    
	isRunning = True
	while isRunning:
		mqttc.loop(10) 	# seconds timeout / blocking time
		print(".", end="", flush=True)	# feedback that something is actually happening
		
except KeyboardInterrupt:
    print("Exit")
    sys.exit(0)