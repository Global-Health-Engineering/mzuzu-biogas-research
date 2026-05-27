import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# List of consecutive files
files = [
    "nucleo_data_2026-03-22.csv",
    "nucleo_data_2026-03-23.csv",
    "nucleo_data_2026-03-24.csv",
    "nucleo_data_2026-03-25.csv"
]

# 1. Load and concatenate all dataframes
all_dfs = []
for f in files:
    df = pd.read_csv(f)
    all_dfs.append(df)

combined_df = pd.concat(all_dfs, ignore_index=True)

# 2. Parse timestamps and sort to ensure continuity
combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
combined_df = combined_df.sort_values('timestamp')

# 3. Initialize the plot
plt.figure(figsize=(15, 8))

# Plot the three temperature points
# Note: tank_temp_start_c is assigned to the middle position as requested
plt.plot(combined_df['timestamp'], combined_df['tank_top_c'], 
         label='Tank Top ($T_{top}$)', color='#e74c3c', linewidth=1.5)

plt.plot(combined_df['timestamp'], combined_df['tank_temp_start_c'], 
         label='Tank Middle ($T_{mid}$)', color='#f39c12', linewidth=1.5)

plt.plot(combined_df['timestamp'], combined_df['tank_temp_bottom_c'], 
         label='Tank Bottom ($T_{bottom}$)', color='#3498db', linewidth=1.5)

# 4. Formatting and Labels
plt.title('CONSECUTIVE TANK TEMPERATURE PROFILE (4 DAYS)', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('DATE AND TIME', fontsize=12, fontweight='bold')
plt.ylabel('TEMPERATURE ($^\circ$C)', fontsize=12, fontweight='bold')

# Configure x-axis formatting for time-series
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
plt.gca().xaxis.set_major_locator(mdates.DayLocator())
plt.gca().xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18]))
plt.xticks(rotation=45)

# Add grid and legend
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.legend(loc='upper right', frameon=True, shadow=True, prop={'weight':'bold'})

plt.tight_layout()
plt.savefig('consecutive_days_temp_plot.png', dpi=300)
plt.show()



# Load and combine all data
all_dfs = [pd.read_csv(f) for f in files]
df = pd.concat(all_dfs, ignore_index=True)

# Calculate the difference: Top - Middle (tank_temp_start_c)
df['temp_diff_top_mid'] = df['tank_top_c'] - df['tank_temp_start_c']
df['temp_diff_mid_bottom'] = df['tank_temp_start_c'] - df['tank_temp_bottom_c']

# Calculate statistical values
avg_diff = df['temp_diff_mid_bottom'].mean()
max_diff = df['temp_diff_mid_bottom'].max()
min_diff = df['temp_diff_mid_bottom'].min()

print(f"Average Temperature Difference: {avg_diff:.2f} °C")
print(f"Maximum Temperature Difference: {max_diff:.2f} °C")
print(f"Minimum Temperature Difference: {min_diff:.2f} °C")