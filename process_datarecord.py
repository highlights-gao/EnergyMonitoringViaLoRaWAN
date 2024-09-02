

hex_data = "0F31484C5930323030393233368534501002613902958E822125"

# 1. 消息头
message_header = hex_data[:2]

# 2. ID (14字节, ASCII)
id_hex = hex_data[2:30]
id_ascii = bytearray.fromhex(id_hex).decode('latin1')

# 3. 固件版本号 (3字节)
firmware_version_hex = hex_data[30:36]

# 4. 校验和 (2字节)
checksum_hex = hex_data[36:40]

# 5. 模块版本号 (4字节)
module_version_hex = hex_data[40:48]

# 6. 模块版本号的校验和 (2字节)
module_checksum_hex = hex_data[48:52]

# 打印结果
print("消息头:", message_header)
print("ID:", id_ascii)
print("固件版本号 (hex):", firmware_version_hex)
print("校验和 (hex):", checksum_hex)
print("模块版本号 (hex):", module_version_hex)
print("模块版本号的校验和 (hex):", module_checksum_hex)

def process_data_record1(hex_data):

    # 1. 消息头
    message_header = hex_data[:2]
    # 2. ID (14字节, ASCII)
    id_hex = hex_data[2:30]
    id_ascii = bytearray.fromhex(id_hex).decode('latin1')
    # 3. 固件版本号 (3字节)
    firmware_version_hex = hex_data[30:36]

    # 4. 校验和 (2字节)
    checksum_hex = hex_data[36:40]

    # 5. 模块版本号 (4字节)
    module_version_hex = hex_data[40:48]

    # 6. 模块版本号的校验和 (2字节)
    module_checksum_hex = hex_data[48:52]
    return message_header, id_ascii, firmware_version_hex, checksum_hex, module_version_hex, module_checksum_hex
def hex_to_signed_decimal(hex_value):
    # 将十六进制字符串转换为整数
    num = int(hex_value, 16)
    
    # 检查符号位 (最高位为1表示负数)
    if num >= 2**23:
        num -= 2**24
    
    return num

hex_data2 = "1100000623CD00000623CD00000000000000000000000000000000000000000000610000000000610000000008010400483A68"
def process_data_record2(hex_data):

    # 1. 消息头
    message_header = hex_data[:2]

    # 2. 总正向电量 (5字节)
    total_forward_energy = hex_data[2:12]
    total_forward_energy_int = int(total_forward_energy, 16)*0.0001
    # 3. 正向电量1 (5字节)
    forward_energy_1 = hex_data[12:22]
    forward_energy_1_int = int(forward_energy_1, 16)*0.0001
    # 4. 正向电量2 (5字节)
    forward_energy_2 = hex_data[22:32]
    forward_energy_2_int = int(forward_energy_2, 16)*0.0001
    # 5. 总反向电量 (5字节)
    total_reverse_energy = hex_data[32:42]
    total_reverse_energy_int = int(total_reverse_energy, 16)*0.0001  
    # 6. 反向电量1 (5字节)
    reverse_energy_1 = hex_data[42:52]
    reverse_energy_1_int = int(reverse_energy_1, 16)*0.0001     
    # 7. 反向电量2 (5字节)
    reverse_energy_2 = hex_data[52:62]
    reverse_energy_2_int = int(reverse_energy_2, 16)*0.0001 
    # 8. 总功率 (3字节)
    total_power = hex_data[62:68]
    total_power_signed = hex_to_signed_decimal(total_power)*0.1 
    # 9. 相位1功率 (3字节)
    phase_1_power = hex_data[68:74]
    phase_1_power_signed = hex_to_signed_decimal(phase_1_power)*0.1 
          
    # 10. 相位2功率 (3字节)
    phase_2_power = hex_data[74:80]
    phase_2_power_signed = hex_to_signed_decimal(phase_2_power)*0.1      
    # 11. 相位3功率 (3字节)
    phase_3_power = hex_data[80:86]
    phase_3_power_signed = hex_to_signed_decimal(phase_3_power)*0.1    
    # 12. 状态字 (4字节)
    status_word = hex_data[86:94]

    # 13. 秒指针 (4字节)
    second_pointer = hex_data[94:102]
    second_pointer_int = int(second_pointer, 16)    

    return total_power_signed

total = process_data_record2(hex_data2)
print(total)