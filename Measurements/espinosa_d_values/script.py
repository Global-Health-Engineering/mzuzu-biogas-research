import matplotlib.pyplot as plt
import numpy as np

# Given data
temps = np.array([60, 64, 68, 72, 76, 80])
d_values = np.array([12360, 7973, 4530, 2718, 1652, 1044])

# Create interpolated curve
temps_interp = np.linspace(60, 80, 200)
d_interp = np.interp(temps_interp, temps, d_values)

# Point to evaluate
x_point = 66
y_point = np.interp(x_point, temps, d_values)

# Plot
plt.figure()
plt.plot(temps_interp, d_interp, label="Linear interpolation")
plt.scatter(temps, d_values, label="Data points")
plt.scatter([x_point], [y_point], label="Interpolated point")

# Dashed projection lines
plt.axvline(x=x_point, linestyle='--')
plt.axhline(y=y_point, linestyle='--')

# Set ticks to include original values + interpolated point
xticks = np.sort(np.append(temps, x_point))
yticks = np.sort(np.append(d_values, y_point))

plt.xticks(xticks)
plt.yticks(yticks)

# Labels and title
plt.xlabel("Temperature (°C)")
plt.ylabel("D-value (for 10^3 reduction)")
plt.title("D-value vs Temperature with Interpolated Point")

# Optional: show legend
plt.legend()

plt.show()