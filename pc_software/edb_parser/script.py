import serial
import serial.tools.list_ports
import requests
import time
import csv
import os
from datetime import datetime,date


HTTP_ENDPOINT = "http://eu.thingsboard.cloud/api/v1/at15js0ffn43ctlaciff/telemetry"  
HTTP_TIMEOUT = 2  # seconds

# Arduino Nano USB identifiers
TARGET_VID = 0x0403
TARGET_PID = 0x6001


def find_serial_port(TARGET_VID, TARGET_PID):
    """
    Iterate over all serial ports and return the one that matches
    the target VID/PID.
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid == TARGET_VID and port.pid == TARGET_PID:
            print("VID and PID match found on port:", port.device)
            temporary_serial_object = serial.Serial(
                port = port.device,
                baudrate=115200,
                timeout=2
            )
            # wait until we receive data. The first word will identify
            # if this is the correct Arduino
            while temporary_serial_object.in_waiting > 0:
                temporary_serial_object.read(temporary_serial_object.in_waiting)
            first_line = b''
            while(first_line == b''):
                first_line = temporary_serial_object.readline()
            print(first_line)
            if b"edb" in first_line:
                print("The received line is a match")
                temporary_serial_object.close()
                print("Closed the temporary port")
                return port.device
            temporary_serial_object.close()
            # return port.device
    print("Could not find Arduino")
    return None



def parse_line(line: str):
    """
    Parse a line of serial data that looks like:
    "edb edbDrain 1|0 edbEffluent 1|0 tankLevel 0-1023 flowRate 0.0-1023.0 "
    """
    parts = line.strip().split()

    if len(parts) != 9:
        raise ValueError(f"Expected 9 values, got {len(parts)}: {line}")

    edb_drain_state = int(parts[2])
    edb_effluent_state = int(parts[4])
    tank_level = int(parts[6])
    flow_rate = float(parts[8])

    return edb_drain_state, edb_effluent_state, tank_level, flow_rate


def send_http(data: dict):
    response = requests.post(
        HTTP_ENDPOINT,
        json=data,
        timeout=HTTP_TIMEOUT
    )
    response.raise_for_status()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_HEADER = [
    "timestamp",
    "edb_drain_state",
    "edb_effluent_state",
    "tank_level",
    "flow_rate"
]

current_csv_date = None
current_csv_file = None
current_csv_writer = None


def open_daily_csv():
    """Open (or reopen) today's CSV file."""
    global current_csv_date, current_csv_file, current_csv_writer

    today = date.today()

    if current_csv_date != today:
        # Close old file if open
        if current_csv_file:
            current_csv_file.close()

        current_csv_date = today
        filename = f"edb_data_{today.isoformat()}.csv"
        filepath = os.path.join(SCRIPT_DIR, filename)

        file_exists = os.path.isfile(filepath)
        current_csv_file = open(filepath, mode="a", newline="")
        current_csv_writer = csv.writer(current_csv_file)

        # Write header only once
        if not file_exists:
            current_csv_writer.writerow(CSV_HEADER)

        print(f"Logging to {filepath}")


def log_to_csv(edb_drain_state, edb_effluent_state, tank_level, flow_rate):
    open_daily_csv()
    timestamp = datetime.now().isoformat()
    current_csv_writer.writerow([
        timestamp,
        edb_drain_state,
        edb_effluent_state,
        tank_level,
        flow_rate
    ])
    current_csv_file.flush()

arduino_port = find_serial_port(TARGET_VID, TARGET_PID)

time.sleep(1)

while (1):
    arduino_serial_object = serial.Serial(
        port=arduino_port,
        baudrate=115200,
        timeout=2)
    if (arduino_serial_object == None):
        time.sleep(0.1)
        continue
    break

HTTP_SEND_INTERVAL = 300
last_http_send_time = 0

integrated_flow = 0.0

while True:
    try:
        #raw = arduino_serial_object.readline().decode('utf-8', errors='ignore')
        
        raw = arduino_serial_object.read(52).decode('utf-8', errors='ignore')
        if not raw:
            continue

        edb_drain_state, edb_effluent_state, tank_level, flow_rate = parse_line(raw)
        
        # convert ticks to flow rate in L/min
        flow_rate = flow_rate * 0.0076 + 0.0044

        print(f"EDB Drain pump state: {edb_drain_state}, EDB Effluent pump state: {edb_effluent_state}, Tank Level: {tank_level}, Flow Rate: {flow_rate} L/min")

        log_to_csv(edb_drain_state, edb_effluent_state, tank_level, flow_rate)

        integrated_flow += flow_rate

        now = time.time()

        if now - last_http_send_time >= HTTP_SEND_INTERVAL:
            integrated_flow /= HTTP_SEND_INTERVAL
            payload = {
                "edb_drain_state": edb_drain_state,
                "edb_effluent_state": edb_effluent_state,
                "tank_level": tank_level,
                "flow_rate": integrated_flow
            }
            integrated_flow = 0.0

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
