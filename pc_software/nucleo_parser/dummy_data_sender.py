import serial
import serial.tools.list_ports
import requests
import time



# Nucleo board USB identifiers
NUCLEO_VID = 0x0483
NUCLEO_PID = 0x374b

# HTTP config
HTTP_ENDPOINT = "http://eu.thingsboard.cloud/api/v1/at15js0ffn43ctlaciff/telemetry"  
HTTP_TIMEOUT = 2  # seconds



def send_http(data: dict):
    response = requests.post(
        HTTP_ENDPOINT,
        json=data,
        timeout=HTTP_TIMEOUT
    )
    response.raise_for_status()



payload = {
    "battery_mv": 13000,
    "die_temp_c": 30,
    "tank_temp_start_c": 75,
    "loops": 1,
    "tank_temp_delta": -1
    }

send_http(payload)
print("Sent:", payload)







