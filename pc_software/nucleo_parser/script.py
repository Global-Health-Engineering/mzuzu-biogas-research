import serial
import serial.tools.list_ports
import requests
import time
import csv
import os
from datetime import datetime, date


# ================= CONFIG =================

# Nucleo board USB identifiers
NUCLEO_VID = 0x0483
NUCLEO_PID = 0x374b

# HTTP config
HTTP_ENDPOINT = "http://eu.thingsboard.cloud/api/v1/at15js0ffn43ctlaciff/telemetry"
HTTP_TIMEOUT = 2  # seconds


# ================= CSV LOGGING =================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_HEADER = [
    "timestamp",
    "battery_mv",
    "die_temp_c",
    "tank_top_c",
    "tank_temp_start_c",
    "tank_temp_bottom_c",
    "tank_temp_end_c",
    
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
        filename = f"nucleo_data_{today.isoformat()}.csv"
        filepath = os.path.join(SCRIPT_DIR, filename)

        file_exists = os.path.isfile(filepath)
        current_csv_file = open(filepath, mode="a", newline="")
        current_csv_writer = csv.writer(current_csv_file)

        if not file_exists:
            current_csv_writer.writerow(CSV_HEADER)

        print(f"Logging to {filepath}")


def log_to_csv(battery_mv, die_temp_c, tank_top_c, tank_start_c, tank_bottom_c, tank_end_c):
    open_daily_csv()
    current_csv_writer.writerow([
        datetime.now().isoformat(),
        battery_mv,
        die_temp_c,
        tank_top_c,
        tank_start_c,
        tank_bottom_c,
        tank_end_c,
    ])
    current_csv_file.flush()


# ================= SERIAL =================

def find_serial_port(TARGET_VID, TARGET_PID):
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid == TARGET_VID and port.pid == TARGET_PID:
            return port.device
    return None


def parse_line(line: str):
    """
    Expected format:
    "13026 75000 68625 40000 68625 24235"
    which corresponds to:
    battery_mv, tank_temp_top_mc, tank_temp_start_mc, tank_temp_bottom_mc, tank_temp_end_mc, die_temp_mc
    """
    parts = line.strip().split()

    if len(parts) != 6:
        raise ValueError(f"Expected 6 values, got {len(parts)}: {line}")

    battery_mv = int(parts[0])
    tank_temp_top_mc = int(parts[1])  
    tank_temp_start_mc = int(parts[2])
    tank_temp_bottom_mc = int(parts[3])
    tank_temp_end_mc = int(parts[4])
    die_temp_mc = int(parts[5])

    return battery_mv, die_temp_mc, tank_temp_top_mc, tank_temp_start_mc, tank_temp_bottom_mc, tank_temp_end_mc

def send_http(data: dict):
    response = requests.post(
        HTTP_ENDPOINT,
        json=data,
        timeout=HTTP_TIMEOUT
    )
    response.raise_for_status()


# ================= MAIN =================

nucleo_port = find_serial_port(NUCLEO_VID, NUCLEO_PID)
if not nucleo_port:
    raise SystemExit("ERROR: Could not find the ST-LINK/V2.1 device.")

nucleo_serial_object = serial.Serial(
    port=nucleo_port,
    baudrate=115200,
    timeout=1
)

while True:
    try:
        raw = nucleo_serial_object.readline().decode("utf-8", errors="ignore")
        if not raw:
            continue

        battery_mv, die_temp_mc, tank_top_mc, tank_start_mc, tank_temp_bottom_mc, tank_end_mc = parse_line(raw)

        die_temp_c = die_temp_mc / 1000.0
        tank_top_c = tank_top_mc / 1000.0
        tank_start_c = tank_start_mc / 1000.0
        tank_end_c = tank_end_mc / 1000.0
        tank_temp_bottom_c = tank_temp_bottom_mc / 1000.0

        print(f"Battery: {battery_mv} mV")
        print(f"Die Temp: {die_temp_c} °C")
        print(f"Tank Top Temp: {tank_top_c} °C")
        print(f"Tank Start Temp: {tank_start_c} °C")
        print(f"Tank End Temp: {tank_end_c} °C")
        print(f"Tank Bottom Temp: {tank_temp_bottom_c} °C")
        print("----------------------------")

        # Always log to CSV
        log_to_csv(
            battery_mv,
            die_temp_c,
            tank_top_c,
            tank_start_c,
            tank_temp_bottom_c,
            tank_end_c
        )

        payload = {
            "battery_mv": battery_mv,
            "die_temp_c": die_temp_c,
            "tank_temp_top_c": tank_top_c,
            "tank_temp_start_c": tank_start_c,
            "tank_temp_bottom_c": tank_temp_bottom_c,
            "tank_temp_end_c": tank_end_c,
            "tank_temp_delta": tank_end_c - tank_start_c
        }

        send_http(payload)
        print("HTTP sent:", payload)

    except ValueError as e:
        print(f"Parse error: {e}")
        break

    except KeyboardInterrupt:
        print("Exiting...")
        break


nucleo_serial_object.close()
if current_csv_file:
    current_csv_file.close()
