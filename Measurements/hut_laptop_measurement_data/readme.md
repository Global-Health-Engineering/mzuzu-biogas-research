# Research Hut Data Logs

The research computer in the Mzuzu Research Hut records data from two independent microcontroller systems:

1. **Solar heater telemetry** (received over LoRa)
2. **Infrastructure / EDB monitoring data** (received directly over USB)

Each system produces a separate daily log file.

---

## Solar Heater Telemetry Logs

**Filename format:**  
`nucleo_data_YYYY-MM-DD`

Example:  
`nucleo_data_2026-03-25`

### Overview

The research hut computer is connected to a **LoRa receiver microcontroller**. This receiver collects telemetry packets transmitted by the **solar heater microcontroller**.

When a packet is received:

1. The LoRa receiver parses the telemetry data.
2. The parsed data is sent to the research hut computer via USB.
3. The research hut computer timestamps and stores the data in the daily log file.

### Data fields

| Field | Description |
|---|---|
| `timestamp` | Time the packet was received by the research hut computer |
| `battery_mv` | Battery voltage (mV) measured when the solar heater microcontroller woke up |
| `die_temp_c` | Internal microcontroller temperature (°C) at wake-up |
| `tank_top_c` | Water temperature at the top of the tank (°C) at wake-up |
| `tank_temp_start_c` | Water temperature in the middle of the tank (°C) at wake-up |
| `tank_temp_bottom_c` | Water temperature at the bottom of the tank (°C) at wake-up |
| `tank_temp_end_c` | Water temperature in the middle of the tank (°C) measured before sleep |

---

## Infrastructure / EDB Logs

**Filename format:**  
`edb_data_YYYY-MM-DD`

Example:  
`edb_data_2026-03-14`

### Overview

The research hut computer is connected directly to the **infrastructure electronics microcontroller**.

This controller automates site infrastructure and gathers measurements from connected sensors. Measurements are transmitted to the research hut computer over USB, where they are parsed, timestamped, and saved.

### Data fields

| Field | Description |
|---|---|
| `timestamp` | Time the measurement packet was received by the research hut computer |
| `edb_drain_state` | EDB drain pump state (`0` = off, `1` = on) |
| `edb_effluent_state` | EDB effluent pump state (`0` = off, `1` = on) |
| `tank_level` | Effluent tank fill level, ranging from `0` to `1023` |
| `flow_rate` | Flow sensor output. Until **2026-03-10**, this value represented raw pulse counts. From **2026-03-10 onward**, it represents flow rate in **L/min** |

---

## Notes

- All timestamps correspond to **when data was received and recorded by the research hut computer**, not necessarily when the measurement was taken.
- Each file contains one day's worth of logged data.
- Field names are preserved exactly as written in the data logs.
