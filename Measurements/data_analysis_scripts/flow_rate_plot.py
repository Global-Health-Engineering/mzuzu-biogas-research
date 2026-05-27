"""
This script plots the flow rates seen on a day. Mind that the sensor is noisy,
so we had to do some cleaning, most importantly, disregarding below the noise floor
and disregarding when the solar heater was not working.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def analyze_strict_flow(date_str, threshold=2.0):
    # 1. Load data
    df_edb = pd.read_csv(f"edb_data_{date_str}.csv")
    df_nuc = pd.read_csv(f"nucleo_data_{date_str}.csv")
    
    # ISO8601 formatting
    df_edb['timestamp'] = pd.to_datetime(df_edb['timestamp'], format='ISO8601')
    df_nuc['timestamp'] = pd.to_datetime(df_nuc['timestamp'], format='ISO8601')
    
    # 2. APPLY STRICT CONDITION: abs(start - end) > threshold
    df_nuc['temp_diff'] = (df_nuc['tank_temp_start_c'] - df_nuc['tank_temp_end_c']).abs()
    df_nuc['valve_active'] = df_nuc['temp_diff'] > threshold
    active_times = df_nuc[df_nuc['valve_active']]['timestamp'].sort_values().tolist()
    
    # 3. Create active zones for EDB timestamps (5-minute buffer)
    df_edb['is_active_zone'] = False
    buffer = pd.Timedelta(minutes=5)
    
    for t in active_times:
        df_edb.loc[(df_edb['timestamp'] >= t - buffer) & 
                   (df_edb['timestamp'] <= t + buffer), 'is_active_zone'] = True
        
    # 4. CLEAN DATA: Zero out flow outside active zones
    df_edb['cleaned_flow_rate'] = df_edb['flow_rate'].where(df_edb['is_active_zone'], 0)
    df_edb['cleaned_flow_rate'] = df_edb['cleaned_flow_rate'].where(df_edb['cleaned_flow_rate'] >= 0.8, 0)
    df_edb['cleaned_flow_rate'] -= 0.5
    df_edb['cleaned_flow_rate'] = df_edb['cleaned_flow_rate'].clip(lower=0)  # Ensure no negative flow rates after cleaning
    # 5. CALCULATE TOTAL ACCUMULATED FLOW (Liters)
    df_edb['dt_sec'] = df_edb['timestamp'].diff().dt.total_seconds().fillna(1.0)
    df_edb['incremental_liters'] = (df_edb['cleaned_flow_rate'] * df_edb['dt_sec']) / 60.0
    total_liters = df_edb['incremental_liters'].sum()
    
    # 6. Plotting
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df_edb['timestamp'], df_edb['cleaned_flow_rate'], color='blue', label=f'Flow (Threshold > {threshold}°C)')
    ax.fill_between(df_edb['timestamp'], 0, df_edb['cleaned_flow_rate'], color='blue', alpha=0.1)
    
    # Annotation
    textstr = f"Accumulated Flow: {total_liters:.2f} L)"
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=11, fontweight='bold',
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='blue'))
    
    ax.set_title(f"Effluent Throughput: {date_str}", fontsize=14)
    ax.set_ylabel("Flow Rate (L/min)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.grid(True, linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"strict_flow_{date_str}.png", dpi=300)
    plt.show()
    
    return total_liters

# Execute for March 29th
analyze_strict_flow("2026-03-29", threshold=2.0)
