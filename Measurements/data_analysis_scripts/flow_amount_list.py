"""
Calculates daily flow totals from the solar heater system by:
1. Identifying active valve periods using a strict absolute temperature mismatch (> 2°C).
2. Applying a noise floor filter to remove low flow readings (< 0.8 L/min).
3. Subtracting a bias offset (0.5 L/min) from active flow rates to correct for sensor drift.
4. Integrating the cleaned flow rates over time to get daily totals in liters.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def compute_daily_flows(start_str, end_str, temp_threshold=2.0, noise_floor=0.3, rate_offset=0.5):
    """
    Calculates daily throughput with:
    1. Looking at where the solar heater was active.
    2. Noise floor filter (removes readings < 0.3 L/min).
    3. Bias correction (subtracts 0.5 L/min from active flow).
    """
    start_date = datetime.strptime(start_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_str, "%Y-%m-%d")
    
    daily_totals = []
    current = start_date
    
    while current <= end_date:
        ds = current.strftime("%Y-%m-%d")
        edb_f, nuc_f = f"edb_data_{ds}.csv", f"nucleo_data_{ds}.csv"
        
        if os.path.exists(edb_f) and os.path.exists(nuc_f):
            try:
                # Load and parse
                df_edb = pd.read_csv(edb_f)
                df_nuc = pd.read_csv(nuc_f)
                df_edb['timestamp'] = pd.to_datetime(df_edb['timestamp'], format='ISO8601')
                df_nuc['timestamp'] = pd.to_datetime(df_nuc['timestamp'], format='ISO8601')
                
                # 1. Identify active valve windows (Strict Absolute mismatch)
                df_nuc['mismatch'] = (df_nuc['tank_temp_start_c'] - df_nuc['tank_temp_end_c']).abs() > temp_threshold
                active_times = df_nuc[df_nuc['mismatch']]['timestamp']
                
                # 2. Define Active Zones (5-min buffer)
                df_edb['is_active'] = False
                buffer = pd.Timedelta(minutes=5)
                for t in active_times:
                    df_edb.loc[(df_edb['timestamp'] >= t - buffer) & 
                               (df_edb['timestamp'] <= t + buffer), 'is_active'] = True
                
                # 3. Apply Noise Floor Filter (< 0.3 L/min = 0)
                # 4. Apply Valve Mask & Subtract Offset (-0.5 L/min)
                df_edb['cleaned_rate'] = df_edb['flow_rate'].where(df_edb['flow_rate'] >= noise_floor, 0)
                df_edb['cleaned_rate'] = df_edb['cleaned_rate'].where(df_edb['is_active'], 0)
                df_edb['cleaned_rate'] = (df_edb['cleaned_rate'] - rate_offset).clip(lower=0)
                
                # 5. Integrate Volume
                df_edb['dt_sec'] = df_edb['timestamp'].diff().dt.total_seconds().fillna(1.0)
                vol = (df_edb['cleaned_rate'] * df_edb['dt_sec'] / 60.0).sum()
                
                daily_totals.append({"Date": ds, "Flow_Liters": round(vol, 2)})
            except Exception as e:
                daily_totals.append({"Date": ds, "Flow_Liters": f"Processing Error: {e}"})
        else:
            daily_totals.append({"Date": ds, "Flow_Liters": "No Data"})
            
        current += timedelta(days=1)
        
    return daily_totals

# Execution for the specific date range
flow_list = compute_daily_flows("2026-03-22", "2026-04-08", noise_floor = 0.8, rate_offset=0.5)

# Print the results
print(f"{'Date':<12} | {'Daily Flow (L)':<15}")
print("-" * 30)
for entry in flow_list:
    print(f"{entry['Date']:<12} | {entry['Flow_Liters']:<15}")
