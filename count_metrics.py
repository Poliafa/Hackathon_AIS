import pandas as pd
import numpy as np

df = pd.read_csv(r"C:\Users\Polina\Desktop\hakaton_project\clean_ais_data.py")

df = df.sort_values(['mmsi', 'datetime'])

def haversine(lat1, lon1, lat2, lon2):
    R = 3440.065
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def calc_metrics(group):
    lats = group['latitude_deg'].values
    lons = group['longitude_deg'].values
    times = pd.to_datetime(group['datetime'])

    if len(lats) > 1:
        distances = haversine(lats[:-1], lons[:-1], lats[1:], lons[1:])
        time_diffs = times.diff().dt.total_seconds().iloc[1:].values / 3600
        point_speeds = np.where(time_diffs > 0, distances / time_diffs, 0)
        valid_mask = point_speeds < 50
        total_distance_nm = distances[valid_mask].sum()
        max_speed_knots = point_speeds[valid_mask].max() if valid_mask.any() else 0.0
    else:
        total_distance_nm = 0.0
        max_speed_knots = 0.0

    start_time = times.min()
    end_time = times.max()
    duration_hours = (end_time - start_time).total_seconds() / 3600
    avg_speed_knots = total_distance_nm / duration_hours if duration_hours > 0 else 0.0

    return pd.Series({
        'total_distance_nm': round(total_distance_nm, 4),
        'duration_hours':    round(duration_hours, 4),
        'avg_speed_knots':   round(avg_speed_knots, 4),
        'max_speed_knots':   round(max_speed_knots, 4),
        'num_points':        len(group),
        'start_time':        start_time,
        'end_time':          end_time,
    })

metrics = df.groupby('mmsi').apply(calc_metrics, include_groups=False).reset_index()

# Топ-5 по расстоянию
top5 = metrics.nlargest(5, 'total_distance_nm')

# Сохраняем только топ-5
output_path = r"C:\Users\danba\PycharmProjects\hakaton\data\metrics_per_ship.csv"
top5.to_csv(output_path, index=False)

print("Топ-5 судов по пройденному расстоянию:")
print(top5.to_string(index=False))
print(f"\nФайл сохранён: {output_path}")