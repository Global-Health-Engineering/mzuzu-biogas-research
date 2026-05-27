"""
Analyzes the heat loss seen during a night by looking at solar
heater data and solcast temperature data.
"""

import pandas as pd
import numpy as np
import glob
import os

# ==========================================
# 1. CONFIGURATION & CONSTANTS
# ==========================================
SURFACE_AREA = 1.866  # m^2
WATER_MASS = 150.0    # kg
SPECIFIC_HEAT = 4187  # J/kg.K
SOLCAST_FILE = "solcast_february_march.csv"

# Pattern to find your data files (e.g., "nucleo_data_*.csv")
NUCLEO_FILE_PATTERN = "nucleo_data_2026-*.csv"

def analyze_heat_loss():
    # ==========================================
    # 2. LOAD AND CLEAN DATA
    # ==========================================
    # Load all tank data files
    tank_files = glob.glob(NUCLEO_FILE_PATTERN)
    if not tank_files:
        print("No tank data files found matching pattern.")
        return

    all_tank_dfs = []
    for f in tank_files:
        df = pd.read_csv(f)
        # Ensure timestamp is datetime and strip timezone for easy matching
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        all_tank_dfs.append(df)
    
    df_tank = pd.concat(all_tank_dfs).sort_values('timestamp').drop_duplicates().reset_index(drop=True)

    # Load weather data
    if not os.path.exists(SOLCAST_FILE):
        print(f"Weather file {SOLCAST_FILE} not found.")
        return
        
    df_weather = pd.read_csv(SOLCAST_FILE)
    df_weather['period_end'] = pd.to_datetime(df_weather['period_end']).dt.tz_localize(None)

    # ==========================================
    # 3. NOCTURNAL ANALYSIS LOOP
    # ==========================================
    results = []
    unique_dates = sorted(df_tank['timestamp'].dt.date.unique())

    for i in range(len(unique_dates)):
        d1 = unique_dates[i]
        d2 = d1 + pd.Timedelta(days=1)
        
        # We only analyze if we have data for the start and the following morning
        if d2 in unique_dates:
            # Define window: 18:00 (Sunset) to 06:00 (Sunrise next day)
            s_night = pd.Timestamp(f"{d1} 18:00:00")
            e_night = pd.Timestamp(f"{d2} 06:00:00")
            
            # Filter data for this specific night
            t_n = df_tank[(df_tank['timestamp'] >= s_night) & (df_tank['timestamp'] <= e_night)]
            w_n = df_weather[(df_weather['period_end'] >= s_night) & (df_weather['period_end'] <= e_night)]
            
            # Require at least 10 hours of data to be valid
            if not t_n.empty and not w_n.empty:
                dt_sec = (t_n.iloc[-1]['timestamp'] - t_n.iloc[0]['timestamp']).total_seconds()
                
                if dt_sec > 36000: # 10 hours
                    # Temperatures
                    t_start = t_n.iloc[0]['tank_temp_start_c']
                    t_end = t_n.iloc[-1]['tank_temp_start_c']
                    t_drop = t_start - t_end
                    
                    # Calculate Heat Loss Rate (q in Watts)
                    # Q = m * Cp * dT
                    # q = Q / time_in_seconds
                    q = (WATER_MASS * SPECIFIC_HEAT * t_drop) / dt_sec
                    
                    # Thermal Driving Force (Ts - Tf)
                    ts_avg = t_n['tank_temp_start_c'].mean()
                    tf_avg = w_n['air_temp'].mean()
                    delta_t = ts_avg - tf_avg
                    
                    if delta_t > 0:
                        # h = q / (A * delta_T)
                        h = q / (SURFACE_AREA * delta_t)
                        
                        results.append({
                            'Night_Start': d1,
                            'T_sunset': round(t_start, 2),
                            'T_sunrise': round(t_end, 2),
                            'dT_drop': round(t_drop, 2),
                            'Avg_Power_Loss_W': round(q, 2),
                            'Avg_Tank_C': round(ts_avg, 2),
                            'Avg_Ambient_C': round(tf_avg, 2),
                            'h_Value': round(h, 4)
                        })

    # ==========================================
    # 4. OUTPUT RESULTS
    # ==========================================
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        print("\n--- Nocturnal Heat Loss Results ---")
        print(df_results.to_string(index=False))
        df_results.to_csv("nocturnal_analysis_output.csv", index=False)
        print("\nResults saved to 'nocturnal_analysis_output.csv'")
    else:
        print("No valid nocturnal windows found with sufficient data.")

if __name__ == "__main__":
    analyze_heat_loss()
