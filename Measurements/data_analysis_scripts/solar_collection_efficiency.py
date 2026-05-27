"""
This script calculates the realistic solar collection efficiency of the solar heater system by:
1. Loading weather data and calculating the Plane of Array (POA) irradiance based on the system's tilt and location.
2. Loading tank temperature data and calculating an average tank temperature to account for stratification effects.
3. Calculating the thermal energy gained by the water in the tank and the total solar energy incident on the collector.
4. Computing the efficiency as the ratio of thermal energy gained to solar energy incident, and flagging any days with 
suspiciously high efficiencies that may indicate

In the end, trying to calculate this way yielded absurd results. The solcast data seems to be of low quality
in such an application.
"""

import pandas as pd
import numpy as np
import glob
import os

# ==========================================
# 1. CONFIGURATION & CONSTANTS
# ==========================================
APERTURE_AREA = 1.395  # m^2
WATER_MASS = 150.0      # kg
SPECIFIC_HEAT = 4187    # J/kg.K
LATITUDE = -11.465      # Mzuzu, Malawi
TILT_ANGLE = 27.0       
AZIMUTH = 0.0           # Facing North

SOLCAST_FILE = "solcast_february_march.csv"
NUCLEO_FILE_PATTERN = "nucleo_data_2026-*.csv"

def calculate_realistic_efficiency():
    # --- 1. Load and Process Weather Data (POA Calculation) ---
    if not os.path.exists(SOLCAST_FILE):
        print(f"Error: {SOLCAST_FILE} not found.")
        return
        
    df_w = pd.read_csv(SOLCAST_FILE)
    df_w['period_end'] = pd.to_datetime(df_w['period_end']).dt.tz_localize(None)
    
    lat_r = np.radians(LATITUDE)
    tilt_r = np.radians(TILT_ANGLE)
    azm_r = np.radians(AZIMUTH)
    
    df_w['doy'] = df_w['period_end'].dt.dayofyear
    df_w['hr'] = df_w['period_end'].dt.hour + df_w['period_end'].dt.minute / 60.0
    
    # Solar Declination & Hour Angle
    decl = np.radians(23.45 * np.sin(np.radians(360/365 * (284 + df_w['doy']))))
    omega = np.radians(15 * (df_w['hr'] - 12))
    
    # Incidence Angle on Tilted Surface (cos_ti)
    cos_ti = (np.sin(decl) * np.sin(lat_r) * np.cos(tilt_r) - 
              np.sin(decl) * np.cos(lat_r) * np.sin(tilt_r) * np.cos(azm_r) + 
              np.cos(decl) * np.cos(lat_r) * np.cos(tilt_r) * np.cos(omega) + 
              np.cos(decl) * np.sin(lat_r) * np.sin(tilt_r) * np.cos(azm_r) * np.cos(omega))
    cos_ti = np.clip(cos_ti, 0, 1)
    
    # Zenith Angle for Diffuse calculation
    cos_tz = np.clip(np.sin(lat_r)*np.sin(decl) + np.cos(lat_r)*np.cos(decl)*np.cos(omega), 0.01, 1)
    dhi = np.clip(df_w['ghi'] - df_w['dni'] * cos_tz, 0, None)
    
    # Create the 'poa' column that was missing
    df_w['poa'] = (df_w['dni'] * cos_ti) + (dhi * (1 + np.cos(tilt_r)) / 2)

    # --- 2. Load and Process Tank Data (Average Temperature) ---
    tank_files = glob.glob(NUCLEO_FILE_PATTERN)
    processed_dfs = []
    
    for f in tank_files:
        temp_df = pd.read_csv(f)
        temp_df['timestamp'] = pd.to_datetime(temp_df['timestamp'], errors='coerce')
        temp_df = temp_df.dropna(subset=['timestamp'])
        
        # Calculate Average Tank Temp to handle stratification
        # This prevents "fake" high efficiency from only looking at the hot top layer
        temp_cols = ['tank_top_c', 'tank_temp_start_c', 'tank_temp_bottom_c']
        existing = [c for c in temp_cols if c in temp_df.columns]
        temp_df['tank_avg'] = temp_df[existing].mean(axis=1)
        
        temp_df['timestamp'] = temp_df['timestamp'].dt.tz_localize(None)
        processed_dfs.append(temp_df[['timestamp', 'tank_avg']])

    df_t = pd.concat(processed_dfs).sort_values('timestamp').reset_index(drop=True)

    # --- 3. Efficiency Calculation Loop ---
    results = []
    dates = df_t['timestamp'].dt.date.unique()

    print(f"{'Date':<12} | {'Avg T Rise':<10} | {'Efficiency %':<12} | {'Status'}")
    print("-" * 60)

    for d in dates:
        s_time, e_time = pd.Timestamp(f"{d} 08:30:00"), pd.Timestamp(f"{d} 16:30:00")
        t_day = df_t[(df_t['timestamp'] >= s_time) & (df_t['timestamp'] <= e_time)]
        w_day = df_w[(df_w['period_end'] >= s_time) & (df_w['period_end'] <= e_time)]
        
        if len(t_day) > 10 and not w_day.empty:
            delta_t = t_day.iloc[-1]['tank_avg'] - t_day.iloc[0]['tank_avg']
            
            if delta_t > 0:
                q_gain = WATER_MASS * SPECIFIC_HEAT * delta_t
                e_solar = (w_day['poa'] * APERTURE_AREA * 300).sum()
                
                if e_solar > 0:
                    eff = (q_gain / e_solar) * 100
                    status = "OK" if eff < 85 else "SUSPECT (Weather Mismatch)"
                    
                    results.append({
                        'Date': d,
                        'Avg_T_Rise': round(delta_t, 2),
                        'Efficiency_%': round(eff, 2),
                        'Status': status
                    })
                    print(f"{str(d):<12} | {delta_t:<10.2f} | {eff:<12.2f} | {status}")

    pd.DataFrame(results).to_csv("realistic_solar_efficiency.csv", index=False)

if __name__ == "__main__":
    calculate_realistic_efficiency()