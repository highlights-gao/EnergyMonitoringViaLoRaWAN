import logging
import base64



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

RTC_changed_successfully_list = []

device_id = 'demo1'
payload = ''
if device_id not in RTC_changed_successfully_list:

    if payload == 0x840500401D0101E8 :
        #cmd1 was successfully received by meter
        #send cmd2
        pass
    elif payload == 0xC40400401D0126 :
        #cmd1 was failed received by meter
 
        pass

    elif payload == 0x810801401D017F00FF0066 :
        #cmd2 was successfully received by meter
        #send cmd3, this will reboot module. No response is expected.
        RTC_changed_successfully_list.append(device_id)
    elif payload == 0xC10401401D0124:
        #cmd2 was failed received by mete
        #send cmd2 again
        pass
    