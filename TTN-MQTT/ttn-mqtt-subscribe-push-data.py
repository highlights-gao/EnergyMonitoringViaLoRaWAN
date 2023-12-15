#!/usr/bin/python3
# Connect to TTS MQTT Server and send downlink messages using the Paho MQTT Python client library
#
# Instructions to use Eclipse Paho MQTT Python client library:
# https://www.thethingsindustries.com/docs/integrations/mqtt/mqtt-clients/eclipse-paho/)
#
import sys
import logging
import paho.mqtt.client as mqtt
import random
from base64 import b64encode
import json

# Procedure to get the USER, PASSWORD, PUBLIC_TLS_ADDRESS and PUBLIC_TLS_ADDRESS_PORT:
# 1. Login to The Things Stack Community Edition console
#    https://console.cloud.thethings.network/
# 2. Select Go to applications
# 3. Select your application
# 4. On the left hand side menu, select Integrations | MQTT
# 5. See Connection credentials
# 6. For the password press button: Generate new API key
#    Each time you press this button a new password is generated!
#    The password looks like:
#    NNSXS.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#

User = "diinno@ttn"
Password = "NNSXS.Q2COWXN4ASTUMXF7BFSWOYWNVUN7CQWJ36JPP5I.IIO255Q7NTQ2ZTN237BSKJYFZUSVNC5D4JBJGBSOPLLKBVHADDUQ"
PUBLIC_TLS_ADDRESS = "eu1.cloud.thethings.network"
PUBLIC_TLS_ADDRESS_PORT = 8883
DEVICE_ID = "heltec-wireless-stick"

# Meaning Quality of Service (QoS)
# QoS = 0 - at most once
# The client publishes the message, and there is no acknowledgement by the broker.
# QoS = 1 - at least once
# The broker sends an acknowledgement back to the client.
# The client will re-send until it gets the broker's acknowledgement.
# QoS = 2 - exactly once
# Both sender and receiver are sure that the message was sent exactly once, using a kind of handshake
QOS = 0

def stop(client):
    client.disconnect()
    print("\nExit")
    sys.exit(0)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("\nConnected successfully to MQTT broker")
    else:
        print("\nFailed to connect, return code = " + str(rc))


# mid = message ID
# It is an integer that is a unique message identifier assigned by the client.
# If you use QoS levels 1 or 2 then the client loop will use the mid to identify messages that have not been sent.
def on_subscribe(client, userdata, mid, granted_qos):
    print("\nSubscribed with message id (mid) = " + str(mid) + " and QoS = " + str(granted_qos))


def on_disconnect(client, userdata, rc):
    print("\nDisconnected with result code = " + str(rc))

def on_message(mqttc, obj, msg):
    print("\nMessage: " + msg.topic + " " + str(msg.qos)) # + " " + str(msg.payload))
    parsedJSON = json.loads(msg.payload)
    #print(json.dumps(parsedJSON, indent=4))	# Uncomment this to fill your terminal screen with JSON
    end_device_ids = parsedJSON["end_device_ids"]
    device_id = end_device_ids["device_id"]
    application_id = end_device_ids["application_ids"]["application_id"]
	
    received_time = parsedJSON["received_at"]
	
    uplink_message = parsedJSON["uplink_message"]
    f_port = uplink_message["f_port"]
    f_cnt = uplink_message["f_cnt"]
    frm_payload = uplink_message["frm_payload"]
    #payload = base64_to_hex(frm_payload)
    rssi = uplink_message["rx_metadata"][0]["rssi"]
    snr = uplink_message["rx_metadata"][0]["snr"]
    data_rate_index = uplink_message["settings"]["data_rate"]
    consumed_airtime = uplink_message["consumed_airtime"]


def on_log(client, userdata, level, buf):
    print("\nLog: " + buf)
    logging_level = client.LOGGING_LEVEL[level]
    logging.log(logging_level, buf)


# Generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'

print("Create new mqtt client instance")
mqttc = mqtt.Client(client_id)

print("Assign callback functions")
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_disconnect = on_disconnect

mqttc.on_message = on_message
# mqttc.on_log = on_log  # Logging for debugging OK, waste

# Setup authentication from settings above
mqttc.username_pw_set(User, Password)

# IMPORTANT - this enables the encryption of messages
mqttc.tls_set()  # default certification authority of the system

# mqttc.tls_set(ca_certs="mqtt-ca.pem") # Use this if you get security errors
# It loads the TTI security certificate. Download it from their website from this page:
# https://www.thethingsnetwork.org/docs/applications/mqtt/api/index.html
# This is normally required if you are running the script on Windows

print("Connecting to broker: " + PUBLIC_TLS_ADDRESS + ":" + str(PUBLIC_TLS_ADDRESS_PORT))
mqttc.connect(PUBLIC_TLS_ADDRESS, PUBLIC_TLS_ADDRESS_PORT, 60)

if len(DEVICE_ID) != 0:

    topic = "v3/" + USER + "/devices/" + DEVICE_ID + "/down/push"

    print("Subscribe to topic " + topic + " with QoS = " + str(QOS))
    mqttc.subscribe(topic, QOS)

    print("Publishing message to topic " + topic + " with QoS = " + str(QOS))

    hexadecimal_payload = '6666'
    fport = 1

    # Convert hexadecimal payload to base64
    b64 = b64encode(bytes.fromhex(hexadecimal_payload)).decode()
    print('Convert hexadecimal_payload: ' + hexadecimal_payload + ' to base64: ' + b64)

    msg = '{"downlinks":[{"f_port":' + str(fport) + ',"frm_payload":"' + b64 + '","priority": "NORMAL"}]}'
    result = mqttc.publish(topic, msg, QOS)

    # result: [0, 2]
    status = result[0]
    if status == 0:
        print("Send " + msg + " to topic " + topic)
    else:
        print("Failed to send message to topic " + topic)

else:
    print("Can not subscribe or publish to topic")
    stop(mqttc)