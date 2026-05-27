import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.widgets import Button

# --- Load & prep data ---
file_path = "csv_-11.460602_34.014893_fixed_23_0_PT30M.csv"  # adjust if needed
df = pd.read_csv(file_path)

# Parse timestamps and convert to Europe/Zurich
df["period_end"] = pd.to_datetime(df["period_end"], utc=True).dt.tz_convert("Europe/Zurich")
df = df.sort_values("period_end")
df["date_local"] = df["period_end"].dt.date

unique_dates = sorted(df["date_local"].unique())
if not unique_dates:
    raise ValueError("No dates found in the CSV.")

# --- Plotting setup (create twin axes ONCE) ---
fig, ax1 = plt.subplots(figsize=(12, 5))
plt.subplots_adjust(bottom=0.18)  # room for buttons

ax2 = ax1.twinx()  # create once

# Buttons
axprev = plt.axes([0.30, 0.06, 0.12, 0.06])
axnext = plt.axes([0.58, 0.06, 0.12, 0.06])
bprev = Button(axprev, "◀ Prev day")
bnext = Button(axnext, "Next day ▶")

state = {"i": 0}

def plot_day(i):
    # Clear both axes
    ax1.cla()
    ax2.cla()

    day = unique_dates[i]
    day_slice = df[df["date_local"] == day]

    # Left y-axis: Temperature + Precipitation
    l1, = ax1.plot(day_slice["period_end"], day_slice["air_temp"], color="red", label="Air Temp (°C)")
    l2, = ax1.plot(day_slice["period_end"], day_slice["precipitation_rate"], color="blue", label="Precip (mm/h)")
    ax1.set_ylabel("Temp / Precipitation")

    # Right y-axis: Irradiance
    l3, = ax2.plot(day_slice["period_end"], day_slice["dni"], color="orange", label="DNI (W/m²)")
    l4, = ax2.plot(day_slice["period_end"], day_slice["ghi"], color="green", label="GHI (W/m²)")
    ax2.set_ylabel("Irradiance (W/m²)")

    # Formatting
    ax1.set_title(f"Weather & Solar Data — {day} (Europe/Zurich)")
    ax1.set_xlabel("Time")
    ax1.grid(True)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.autofmt_xdate()

    # Combined legend
    ax1.legend([l1, l2, l3, l4], [l.get_label() for l in [l1, l2, l3, l4]], loc="upper left")

    fig.canvas.draw_idle()

def on_prev(event):
    state["i"] = (state["i"] - 1) % len(unique_dates)
    plot_day(state["i"])

def on_next(event):
    state["i"] = (state["i"] + 1) % len(unique_dates)
    plot_day(state["i"])

def on_key(event):
    if event.key in ("left", "pageup"):
        on_prev(None)
    elif event.key in ("right", "pagedown"):
        on_next(None)

bprev.on_clicked(on_prev)
bnext.on_clicked(on_next)
fig.canvas.mpl_connect("key_press_event", on_key)

# Initial draw
plot_day(state["i"])
plt.show()
