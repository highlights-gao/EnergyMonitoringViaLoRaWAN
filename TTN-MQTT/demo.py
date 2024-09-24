def decimal_to_custom_hex(decimal_number,max_retry=3):
    try:
        # 将十进制数转换为4字节的十六进制字符串，不足8位补零
        hex_part = f"{decimal_number:08X}"
        
        # 拼接成目标格式：08 + 4字节十六进制 + 4字节0 + 03
        custom_hex = f"08{hex_part}00000000{max_retry}"
        
        return custom_hex
    except Exception as e:

        return None

# 测试示例
print(decimal_to_custom_hex(15))  # 输出: 08000030390000000003
print(decimal_to_custom_hex(255))    # 输出: 08000000FF0000000003
