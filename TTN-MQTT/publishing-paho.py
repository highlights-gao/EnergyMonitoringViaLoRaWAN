import contextlib
import paho.mqtt.publish as publish

APP_ID = "hly-multiple-batch-test@ttn"
ACCESS_KEY  = "NNSXS.DZTEOFEW7YRVBWJVZWS7L6HA654PNPT7AEJZMSQ.MXK6EFUSGE6F6TOZJQ2EERBUTTJ6GUV42OBV7GANTSWKH7C663NQ"
PUBLIC_TLS_ADDRESS = "eu1.cloud.thethings.network"
PUBLIC_TLS_ADDRESS_PORT = "8883"
REGION = "EU1"

device_id = 'eui-847d500000003dd4-00923263'

frm_paylaod_hex_5min = 0x08000000050000000003
frm_payload_base64_5min = "CAAAAAUAAAAAAw=="
frm_paylaod_hex_reboot = 0x040404401084E0
frm_paylaod_base64_reboot = "BAQEQBCE4A=="


topic_down = f'v3/{APP_ID}/devices/{device_id}/down/push'
context_downlink_changeInterval = '{"downlinks":[{"f_port": 2,"frm_payload": "BAQEQBCE4A==","priority": "NORMAL"}]}'
hostname= PUBLIC_TLS_ADDRESS
port=1883
auth={'username':APP_ID,'password':ACCESS_KEY}

publish.single(topic_down,context_downlink_changeInterval,hostname=hostname,port=port,auth=auth)
