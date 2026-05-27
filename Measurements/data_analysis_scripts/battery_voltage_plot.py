"""
By extracting data from the solar heater raw data, 
plots battery voltage and tank temperatures
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1. Load the data
filename = "nucleo_data_2026-03-31.csv"
df = pd.read_csv(filename)

# 2. Pre-process timestamps and calculate mismatch mask using ABSOLUTE difference > 2
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['mismatch'] = (df['tank_temp_start_c'] - df['tank_temp_end_c']).abs() > 2

# 3. Create the dual Y-axis plot
fig, ax1 = plt.subplots(figsize=(12, 7))

# --- Battery Voltage (Left Axis) ---
color_bat = '#2c3e50'
ax1.set_xlabel('Time of Day', fontsize=12)
ax1.set_ylabel('Battery Voltage (mV)', color=color_bat, fontsize=12)
line1 = ax1.plot(df['timestamp'], df['battery_mv'], color=color_bat, label='Battery Voltage', linewidth=1.5)
ax1.tick_params(axis='y', labelcolor=color_bat)

# --- Temperatures (Right Axis) ---
ax2 = ax1.twinx()
ax2.set_ylabel('Temperature (°C)', color='#e67e22', fontsize=12)

# Tank Temperature
line2 = ax2.plot(df['timestamp'], df['tank_temp_start_c'], color='#e67e22', label='Tank Temp Middle', linewidth=1.5, linestyle='--')

# Die Temperature (MCU Internal)
line3 = ax2.plot(df['timestamp'], df['die_temp_c'], color='#9b59b6', label='MCU Die Temp', linewidth=1.5, alpha=0.8)

ax2.tick_params(axis='y', labelcolor='#e67e22')

# 4. Highlight Mismatch Zones
# We create a proxy for the legend since fill_between doesn't always play nice with automated legends
v_act = ax1.fill_between(df['timestamp'], 
                df['battery_mv'].min() - 200, 
                df['battery_mv'].max() + 200,
                where=df['mismatch'], 
                color='red', 
                alpha=0.15, 
                label='Valve Activity (Strict)')

# 5. Formatting
plt.title('System Dynamics: Battery, Tank, and MCU Temperature (2026-03-29)', fontsize=14)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.xticks(rotation=45)
ax1.grid(True, linestyle='--', alpha=0.4)

# --- CORRECTED LEGEND LOGIC ---
# Collect all handles and labels from both axes properly
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()

# Combine them: handles go in the first list, labels in the second
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

plt.tight_layout()
plt.savefig("mcu_system_dynamics_fixed.png", dpi=300)
plt.show()
