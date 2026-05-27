import matplotlib.pyplot as plt
import numpy as np

# Given data
temps = np.array([60, 64, 68, 72, 76, 80])
d_values = np.array([12360, 7973, 4530, 2718, 1652, 1044])

# Fit log10(D) = a*T + b
log_d = np.log10(d_values)
coeffs = np.polyfit(temps, log_d, 1)
a, b = coeffs

# Generate smooth curve
temps_fit = np.linspace(60, 80, 200)
d_fit = 10**(a * temps_fit + b)

# Point of interest
x_point = 66
y_point = 10**(a * x_point + b)

# Plot
plt.figure()
plt.plot(temps_fit, d_fit, label="Log-linear fit (exponential)")
plt.scatter(temps, d_values, label="Data points")
plt.scatter([x_point], [y_point], label="66°C point")

# Dashed lines
plt.axvline(x=x_point, linestyle='--')
plt.axhline(y=y_point, linestyle='--')

# Ticks
xticks = np.sort(np.append(temps, x_point))
yticks = np.sort(np.append(d_values, y_point))

plt.xticks(xticks)
plt.yticks(yticks)

# Labels
plt.xlabel("Temperature (°C)")
plt.ylabel("D-value (for 10^3 reduction)")
plt.title("Exponential Fit of D-value vs Temperature")

plt.legend()
plt.show()

# Print model
print(f"log10(D) = {a:.4f} * T + {b:.2f}")