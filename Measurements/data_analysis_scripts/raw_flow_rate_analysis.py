"""
This script analyzes the raw flow rate data from the digester system on March 28, 2026. 
It identifies periods of valve activity based on temperature mismatches in the Nucleo 
sensor data and visualizes the flow rate trends from the EDB data. 
The plot highlights active valve zones with red shading, allowing for a clear comparison 
between flow rates and valve operation throughout the day.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1. Load data for March 28
# Replace with your filenames if they are different
df_edb = pd.read_csv("edb_data_2026-03-26.csv")
df_nucleo = pd.read_csv("nucleo_data_2026-03-26.csv")

# 2. Pre-process timestamps
df_edb['timestamp'] = pd.to_datetime(df_edb['timestamp'])
df_nucleo['timestamp'] = pd.to_datetime(df_nucleo['timestamp'])

# 3. Identify valve activity zones (based on Nucleo sensor mismatch)
# We define a mismatch when the start and end temperature readings differ
df_nucleo['mismatch'] = df_nucleo['tank_temp_start_c'] != df_nucleo['tank_temp_end_c']
mismatch_times = df_nucleo[df_nucleo['mismatch']]['timestamp'].sort_values().tolist()

# 4. Create the Flow Rate plot
fig, ax1 = plt.subplots(figsize=(12, 6))

# Plot the flow rate from EDB data
ax1.plot(df_edb['timestamp'], df_edb['flow_rate'], color='teal', label='Effluent Flow Rate', linewidth=1.0)
ax1.set_ylabel('Flow Rate ($L/min$)', color='teal', fontsize=12)
ax1.set_xlabel('Time of Day', fontsize=12)
ax1.set_title('Digester Flow Rate and Valve Operation (2026-03-28)', fontsize=14)

# 5. Highlight the valve "active" zones
# This logic groups consecutive mismatch points into continuous red bands
if mismatch_times:
    start_time = mismatch_times[0]
    for i in range(1, len(mismatch_times)):
        # If the gap between records is > 10 mins (600s), treat it as a new sequence
        if (mismatch_times[i] - mismatch_times[i-1]).total_seconds() > 600:
            ax1.axvspan(start_time, mismatch_times[i-1], color='red', alpha=0.3)
            start_time = mismatch_times[i]
    # Highlight the final interval
    ax1.axvspan(start_time, mismatch_times[-1], color='red', alpha=0.3, label='Valve Active (Mismatch)')

# 6. Formatting the chart
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.xticks(rotation=45)
ax1.grid(True, linestyle='--', alpha=0.4)
ax1.legend(loc='upper right')

plt.tight_layout()
plt.savefig("flow_rate_valve_analysis_2026-03-28.png", dpi=300)
plt.show()

# Optional: Print summary of findings
max_flow = df_edb['flow_rate'].max()
print(f"Max Flow Rate: {max_flow:.4f} L/min")
print(f"Total mismatch instances (valve activity): {len(mismatch_times)}")