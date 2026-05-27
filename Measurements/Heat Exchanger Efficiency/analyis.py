import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
file_name = "heat_exchanger_data.csv"
data = pd.read_csv(file_name)
data.columns = ["hot_out", "hot_in", "cold_out", "cold_in"]
data = data.apply(pd.to_numeric, errors="coerce").dropna()

# 1. Calculate Effectiveness
# data["efficiency"] = (data["cold_out"] - data["cold_in"]) / (data["hot_in"] - data["cold_in"])
data["efficiency"] = (data["hot_in"] - data["hot_out"]) / (data["hot_in"] - data["cold_in"])
time_minutes = np.linspace(0, 9, len(data))

# 2. Find the Maximum Efficiency Point
max_idx = data["efficiency"].idxmax()
t_max = time_minutes[data.index.get_loc(max_idx)]
eff_max = data["efficiency"].max()

# 3. Setup Plotting Style
plt.figure(figsize=(11, 7))
plt.rcParams['font.weight'] = 'bold' 
plt.rcParams['axes.labelweight'] = 'bold'

# Main line plot
plt.plot(time_minutes, data["efficiency"], linestyle='-', color='#2c3e50', linewidth=2.5, label='HE Effectiveness', zorder=1)

# --- HIGH VISIBILITY PEAK MARKER ---
plt.scatter(t_max, eff_max, color='red', marker='X', s=300, edgecolor='black', linewidth=1.5, zorder=5)

# --- DASHED CROSSHAIRS ---
plt.axvline(x=t_max, color='red', linestyle='--', linewidth=1.2, alpha=0.4, zorder=2)
plt.axhline(y=eff_max, color='red', linestyle='--', linewidth=1.2, alpha=0.4, zorder=2)

# --- BOLD ANNOTATION (NO BOX) ---
# xytext is positioned high and to the right to keep the arrow clear
plt.annotate(f'MAX EFFICIENCY\n{eff_max:.3f} at {t_max:.2f} min', 
             xy=(t_max, eff_max), 
             xytext=(t_max + 1.5, eff_max + 0.1), 
             fontsize=12,
             fontweight='bold',
             color='black',
             arrowprops=dict(arrowstyle="->", 
                             connectionstyle="arc3,rad=-0.2", # Curved to avoid the line
                             color='black', 
                             lw=2))

# Average line
avg_eff = data["efficiency"].mean()
plt.axhline(y=avg_eff, color='blue', linestyle=':', alpha=0.7, linewidth=2, label=f'AVERAGE: {avg_eff:.2f}')

# Labels and Title
plt.xlabel("TIME INTO DISCHARGE (MINUTES)", fontsize=12, fontweight='bold')
plt.ylabel("EFFECTIVENESS ($\epsilon$)", fontsize=12, fontweight='bold')
plt.title("HEAT EXCHANGER EFFICIENCY PROFILE", fontsize=15, fontweight='bold', pad=20)

plt.ylim(0, 1) 
plt.grid(True, linestyle='--', alpha=0.4)
plt.legend(loc='lower right', prop={'weight':'bold'})

plt.tight_layout()
plt.show()