"""
This script plots the average number of sunshine hours seen in Mzuzu, based
on the NOAA data.
"""


import matplotlib.pyplot as plt

# Data extracted from the WMO Mzuzu station normals (1965-1990)
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
sunshine_hours_daily = [4.7, 4.9, 5.3, 5.7, 7.0, 7.3, 7.7, 8.9, 9.6, 9.7, 8.4, 5.7]

# Create the plot
plt.figure(figsize=(10, 6))

# Add bar chart for the primary data
bars = plt.bar(months, sunshine_hours_daily, color='skyblue', edgecolor='navy', alpha=0.8)

# Add a trend line to highlight seasonality
plt.plot(months, sunshine_hours_daily, color='orange', marker='o', linewidth=2, label='Trend Line')

# Formatting the visual elements
plt.title('Mean Daily Sunshine Hours - Mzuzu, Malawi (WMO Station 67489)', fontsize=14, pad=15)
plt.xlabel('Month', fontsize=12)
plt.ylabel('Daily Sunshine Hours', fontsize=12)
plt.ylim(0, 12)  # Setting limit slightly higher than max data for clarity
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.legend()

# Adding data labels on top of each bar
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.2, yval, ha='center', va='bottom', fontweight='bold')

plt.tight_layout()

# Save and display
plt.savefig('mzuzu_sunshine_plot.png')
plt.show()
