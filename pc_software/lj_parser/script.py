import serial
import serial.tools.list_ports
import requests
import time
import csv
import os
from datetime import datetime, date


HTTP_ENDPOINT = "http://eu.thingsboard.cloud/api/v1/at15js0ffn43ctlaciff/telemetry"
HTTP_TIMEOUT = 2  # seconds

HTTP_SEND_INTERVAL = 300  # 5 minutes
last_http_send_time = 0

# Arduino Nano USB identifiers
TARGET_VID = 0x0403
TARGET_PID = 0x6001


# ================= CSV LOGGING =================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_HEADER = [
    "timestamp",
    "lj_valve_state",
    "lj_pump_state",
    "temp0",
    "temp1"
]

current_csv_date = None
current_csv_file = None
current_csv_writer = None


def open_daily_csv():
    global current_csv_date, current_csv_file, current_csv_writer

    today = date.today()

    if current_csv_date != today:
        if current_csv_file:
            current_csv_file.close()

        current_csv_date = today
        filename = f"lj_data_{today.isoformat()}.csv"
        filepath = os.path.join(SCRIPT_DIR, filename)

        file_exists = os.path.isfile(filepath)
        current_csv_file = open(filepath, mode="a", newline="")
        current_csv_writer = csv.writer(current_csv_file)

        if not file_exists:
            current_csv_writer.writerow(CSV_HEADER)

        print(f"Logging to {filepath}")


def log_to_csv(lj_valve_state, lj_pump_state, temp0, temp1):
    open_daily_csv()
    current_csv_writer.writerow([
        datetime.now().isoformat(),
        lj_valve_state,
        lj_pump_state,
        temp0,
        temp1
    ])
    current_csv_file.flush()


# ================= SERIAL =================

def find_serial_port(TARGET_VID, TARGET_PID):
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid == TARGET_VID and port.pid == TARGET_PID:
            print("VID and PID match found on port:", port.device)
            temporary_serial_object = serial.Serial(
                port=port.device,
                baudrate=115200,
                timeout=6
            )
            while temporary_serial_object.in_waiting > 0:
                temporary_serial_object.read(temporary_serial_object.in_waiting)

            first_line = temporary_serial_object.readline()
            if b"lj" in first_line:
                temporary_serial_object.close()
                return port.device

            temporary_serial_object.close()

    print("Could not find Arduino")
    return None


def parse_line(line: str):
    parts = line.strip().split()

    if len(parts) != 8:
        raise ValueError(f"Expected 8 values, got {len(parts)}: {line}")

    lj_valve_state = int(parts[2])
    lj_pump_state = int(parts[4])
    temp0 = float(parts[6])
    temp1 = float(parts[7])

    return lj_valve_state, lj_pump_state, temp0, temp1


def send_http(data: dict):
    response = requests.post(
        HTTP_ENDPOINT,
        json=data,
        timeout=HTTP_TIMEOUT
    )
    response.raise_for_status()


# ================= MAIN =================

arduino_port = find_serial_port(TARGET_VID, TARGET_PID)
time.sleep(1)

while True:
    arduino_serial_object = serial.Serial(
        port=arduino_port,
        baudrate=115200,
        timeout=2
    )
    if arduino_serial_object:
        break
    time.sleep(0.1)


while True:
    try:
        raw = arduino_serial_object.readline().decode("utf-8", errors="ignore")
        if not raw:
            time.sleep(0.2)
            continue

        lj_valve_state, lj_pump_state, temp0, temp1 = parse_line(raw)

        print(
            f"LJ Valve State: {lj_valve_state}, "
            f"LJ Pump State: {lj_pump_state}, "
            f"Temp 0: {temp0}, "
            f"Temp 1: {temp1}"
        )

        # Always log to CSV
        log_to_csv(lj_valve_state, lj_pump_state, temp0, temp1)

        now = time.time()

        # Send HTTP only every 5 minutes
        if now - last_http_send_time >= HTTP_SEND_INTERVAL:
            payload = {
                "lj_valve_state": lj_valve_state,
                "lj_pump_state": lj_pump_state,
                "lj_temp0": temp0,
                "lj_temp1": temp1
            }

            send_http(payload)
            last_http_send_time = now
            print("HTTP sent:", payload)

    except ValueError as e:
        print(f"Parse error: {e}")
        break

    except KeyboardInterrupt:
        print("Exiting...")
        break


arduino_serial_object.close()
if current_csv_file:
    current_csv_file.close()