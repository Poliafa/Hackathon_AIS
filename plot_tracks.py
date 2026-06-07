import pandas as pd
import folium
import os

# Загрузка чистых данных
df = pd.read_csv("clean_data.csv", parse_dates=["datetime"])

# Определяем топ-5 судов
try:
    metrics = pd.read_csv("metrics/metrics_per_ship.csv")
    top5_mmsi = metrics.nlargest(5, "total_distance_nm")["mmsi"].tolist()
    print("Топ-5 судов (по metrics_per_ship.csv):", top5_mmsi)
except FileNotFoundError:
    print("Файл metrics/metrics_per_ship.csv не найден. Определяю топ-5 по числу записей.")
    # Группируем и берём 5 судов с наибольшим количеством точек
    top5_mmsi = df.groupby("mmsi").size().nlargest(5).index.tolist()
    print("Топ-5 судов (по количеству точек):", top5_mmsi)

# Фильтрация данных только для топ-5
df_top = df[df["mmsi"].isin(top5_mmsi)].copy()
df_top = df_top.sort_values(["mmsi", "datetime"])

# Центр карты
center_lat = df_top["latitude_deg"].mean()
center_lon = df_top["longitude_deg"].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

colors = ["red", "blue", "green", "purple", "orange"]

for (mmsi, group), color in zip(df_top.groupby("mmsi"), colors):
    points = list(zip(group["latitude_deg"], group["longitude_deg"]))
    if len(points) < 2:
        continue

    folium.PolyLine(points, color=color, weight=3, opacity=0.8, popup=mmsi).add_to(m)
    folium.Marker(points[0], popup=f"{mmsi} start", icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(m)
    folium.Marker(points[-1], popup=f"{mmsi} end", icon=folium.Icon(color="red", icon="stop", prefix="fa")).add_to(m)

os.makedirs("maps", exist_ok=True)
m.save("maps/tracks.html")
print("Карта сохранена в maps/tracks.html")