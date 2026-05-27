import numpy as np
import matplotlib.pyplot as plt

# Your actual data points
temps = np.array([60, 64, 68, 72, 76, 80])
d_values = np.array([12360, 7973, 4530, 2718, 1652, 1044])

# Create a high-resolution temperature range for comparison
temps_fine = np.linspace(60, 80, 1000)

# 1. Linear Interpolation (Current STM32 Logic)
d_linear = np.interp(temps_fine, temps, d_values)

# 2. Log-Linear Interpolation (Bigelow/Standard Microbiology Logic)
# We interpolate in the log domain and then transform back
d_log = 10**(np.interp(temps_fine, temps, np.log10(d_values)))

# 3. Calculate Disagreement (Absolute Difference)
difference = np.abs(d_linear - d_log)

# Find the point of maximum disagreement
idx_max = np.argmax(difference)
t_max = temps_fine[idx_max]
d_lin_val = d_linear[idx_max]
d_log_val = d_log[idx_max]
max_diff = difference[idx_max]
percent_err = (max_diff / d_log_val) * 100

print(f"--- Analysis of Interpolation Disagreement ---")
print(f"Max disagreement occurs at: {t_max:.2f} °C")
print(f"Linear D-value: {d_lin_val:.2f}")
print(f"Log-Linear D-value: {d_log_val:.2f}")
print(f"Absolute Difference: {max_diff:.2f} seconds")
print(f"Percentage Error: {percent_err:.2f}%")

# Visualization
plt.figure(figsize=(10, 6))
plt.plot(temps_fine, d_linear, 'r--', label='Linear Interpolation (Current Code)')
plt.plot(temps_fine, d_log, 'b-', label='Log-Linear Interpolation (Bigelow)')
plt.scatter(temps, d_values, color='black', zorder=5, label='Data Points')

# Mark the highest disagreement
plt.axvline(t_max, color='green', linestyle=':', alpha=0.7)
plt.annotate(f'Max Error @ {t_max:.1f}°C\n({percent_err:.1f}% error)', 
             xy=(t_max, d_lin_val), xytext=(t_max+1, d_lin_val+1000),
             arrowprops=dict(facecolor='black', shrink=0.05))

plt.title("Disagreement: Linear vs. Log-Linear Interpolation of D-Values")
plt.xlabel("Temperature (°C)")
plt.ylabel("D-Value (seconds)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()