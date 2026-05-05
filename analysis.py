import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# =========================
# LOAD DATA
# =========================
imu = pd.read_csv("./logs/1777836759.181342/imu.csv")
gps = pd.read_csv("./logs/1777836759.181342/gps.csv")

# Ensure sorted by time
imu = imu.sort_values("Time")
gps = gps.sort_values("Time")

imu_time = imu["Time"].values
y_dot = imu["Y dot"].values

gps_time = gps["Time"].values


# =========================
# HELPER FUNCTIONS
# =========================
def get_segment(start_time, duration=20):
    mask = (imu_time >= start_time) & (imu_time <= start_time + duration)
    return imu_time[mask], y_dot[mask]


def get_gps_at(time):
    idx = np.argmin(np.abs(gps_time - time))
    row = gps.iloc[idx]
    return row["Lat"], row["Lon"]


# =========================
# INITIAL VALUES
# =========================
t_min = imu_time.min()
t_max = imu_time.max() - 20

t1_init = t_min
t2_init = t_min + 40  # offset so they aren't identical


# =========================
# PLOT SETUP
# =========================
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.3)

t1, y1 = get_segment(t1_init)
t2, y2 = get_segment(t2_init)

line1, = ax.plot(t1 - t1[0], y1, label="Segment 1")
line2, = ax.plot(t2 - t2[0], y2, label="Segment 2")

ax.set_xlabel("Time (s, relative)")
ax.set_ylabel("Y dot")
ax.legend()

# GPS text
gps_text = ax.text(0.02, 0.95, "", transform=ax.transAxes, va='top')


# =========================
# SLIDERS
# =========================
ax_slider1 = plt.axes([0.15, 0.15, 0.7, 0.03])
ax_slider2 = plt.axes([0.15, 0.08, 0.7, 0.03])

slider1 = Slider(ax_slider1, "Segment 1 Start", t_min, t_max, valinit=t1_init)
slider2 = Slider(ax_slider2, "Segment 2 Start", t_min, t_max, valinit=t2_init)


# =========================
# UPDATE FUNCTION
# =========================
def update(val):
    t1_start = slider1.val
    t2_start = slider2.val

    t1, y1 = get_segment(t1_start)
    t2, y2 = get_segment(t2_start)

    if len(t1) > 0:
        line1.set_xdata(t1 - t1[0])
        line1.set_ydata(y1)

    if len(t2) > 0:
        line2.set_xdata(t2 - t2[0])
        line2.set_ydata(y2)

    # Update GPS info
    lat1, lon1 = get_gps_at(t1_start)
    lat2, lon2 = get_gps_at(t2_start)

    gps_text.set_text(
        f"Segment 1 GPS: ({lat1:.6f}, {lon1:.6f})\n"
        f"Segment 2 GPS: ({lat2:.6f}, {lon2:.6f})"
    )

    ax.relim()
    ax.autoscale_view()

    fig.canvas.draw_idle()


slider1.on_changed(update)
slider2.on_changed(update)

# Initial GPS display
update(None)

plt.show()