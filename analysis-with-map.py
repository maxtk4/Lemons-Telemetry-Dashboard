import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt

# =========================
# LOAD DATASETS
# =========================
imu1 = pd.read_csv("./logs/1777661479.0555258/imu.csv").sort_values("Time")
gps1 = pd.read_csv("./logs/1777661479.0555258/gps.csv").sort_values("Time")

imu2 = pd.read_csv("./logs/1777836759.181342/imu.csv").sort_values("Time")
gps2 = pd.read_csv("./logs/1777836759.181342/gps.csv").sort_values("Time")


# Extract arrays
def unpack(imu, gps):
    return (
        imu["Time"].values,
        imu["Y dot"].values,
        gps["Time"].values,
        gps["Lat"].values,
        gps["Lon"].values
    )

imu_time1, ydot1, gps_time1, lat1_all, lon1_all = unpack(imu1, gps1)
imu_time2, ydot2, gps_time2, lat2_all, lon2_all = unpack(imu2, gps2)


# =========================
# HELPERS
# =========================
def get_imu_segment(time_arr, y_arr, start, duration=20):
    mask = (time_arr >= start) & (time_arr <= start + duration)
    return time_arr[mask], y_arr[mask]


def get_gps_segment(time_arr, lat_arr, lon_arr, start, duration=20):
    mask = (time_arr >= start) & (time_arr <= start + duration)
    return lat_arr[mask], lon_arr[mask]


def get_gps_point(time_arr, lat_arr, lon_arr, t):
    idx = np.argmin(np.abs(time_arr - t))
    return lat_arr[idx], lon_arr[idx]


# =========================
# INITIAL VALUES
# =========================
t1_min, t1_max = imu_time1.min(), imu_time1.max() - 20
t2_min, t2_max = imu_time2.min(), imu_time2.max() - 20

t1_init = t1_min
t2_init = t2_min


# =========================
# MAP TILE SETUP
# =========================
tiler = cimgt.OSM()
map_crs = tiler.crs


# =========================
# FIGURE
# =========================
fig = plt.figure(figsize=(12, 5))

ax_plot = fig.add_subplot(1, 2, 1)
ax_map = fig.add_subplot(1, 2, 2, projection=map_crs)

plt.subplots_adjust(bottom=0.3)


# =========================
# INITIAL SEGMENTS
# =========================
t1, y1 = get_imu_segment(imu_time1, ydot1, t1_init)
t2, y2 = get_imu_segment(imu_time2, ydot2, t2_init)

lat1, lon1 = get_gps_segment(gps_time1, lat1_all, lon1_all, t1_init)
lat2, lon2 = get_gps_segment(gps_time2, lat2_all, lon2_all, t2_init)


# =========================
# IMU PLOT
# =========================
line1, = ax_plot.plot(t1 - t1[0], y1, label="Session 1")
line2, = ax_plot.plot(t2 - t2[0], y2, label="Session 2")

ax_plot.set_xlabel("Time (s, relative)")
ax_plot.set_ylabel("Y dot")
ax_plot.set_title("IMU Comparison")
ax_plot.legend()

gps_text = ax_plot.text(0.02, 0.95, "", transform=ax_plot.transAxes, va='top')


# =========================
# MAP
# =========================
zoom = 16
ax_map.add_image(tiler, zoom)

track1, = ax_map.plot([], [], transform=ccrs.PlateCarree(), label="Session 1")
track2, = ax_map.plot([], [], transform=ccrs.PlateCarree(), label="Session 2")

start1, = ax_map.plot([], [], 'o', transform=ccrs.PlateCarree())
start2, = ax_map.plot([], [], 'o', transform=ccrs.PlateCarree())

ax_map.set_title("GPS Track Comparison")
ax_map.legend()


# =========================
# SLIDERS
# =========================
ax_slider1 = plt.axes([0.15, 0.15, 0.7, 0.03])
ax_slider2 = plt.axes([0.15, 0.08, 0.7, 0.03])

slider1 = Slider(ax_slider1, "Session 1 Start", t1_min, t1_max, valinit=t1_init)
slider2 = Slider(ax_slider2, "Session 2 Start", t2_min, t2_max, valinit=t2_init)


# =========================
# UPDATE
# =========================
def update(val):
    s1 = slider1.val
    s2 = slider2.val

    # IMU
    t1, y1 = get_imu_segment(imu_time1, ydot1, s1)
    t2, y2 = get_imu_segment(imu_time2, ydot2, s2)

    if len(t1):
        line1.set_data(t1 - t1[0], y1)
    if len(t2):
        line2.set_data(t2 - t2[0], y2)

    # GPS tracks
    lat1, lon1 = get_gps_segment(gps_time1, lat1_all, lon1_all, s1)
    lat2, lon2 = get_gps_segment(gps_time2, lat2_all, lon2_all, s2)

    if len(lat1):
        track1.set_data(lon1, lat1)
    if len(lat2):
        track2.set_data(lon2, lat2)

    # Start points
    s1_lat, s1_lon = get_gps_point(gps_time1, lat1_all, lon1_all, s1)
    s2_lat, s2_lon = get_gps_point(gps_time2, lat2_all, lon2_all, s2)

    start1.set_data([s1_lon], [s1_lat])
    start2.set_data([s2_lon], [s2_lat])

    # Text
    gps_text.set_text(
        f"Session 1 GPS: ({s1_lat:.6f}, {s1_lon:.6f})\n"
        f"Session 2 GPS: ({s2_lat:.6f}, {s2_lon:.6f})"
    )

    # Map extent
    all_lats = np.concatenate([lat1, lat2]) if len(lat1) and len(lat2) else lat1
    all_lons = np.concatenate([lon1, lon2]) if len(lon1) and len(lon2) else lon1

    if len(all_lats):
        pad = 0.0005
        ax_map.set_extent([
            all_lons.min() - pad,
            all_lons.max() + pad,
            all_lats.min() - pad,
            all_lats.max() + pad
        ], crs=ccrs.PlateCarree())

    ax_plot.relim()
    ax_plot.autoscale_view()

    fig.canvas.draw_idle()


slider1.on_changed(update)
slider2.on_changed(update)

update(None)
plt.show()