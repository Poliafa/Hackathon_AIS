import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from pathlib import Path

# Текущая директория (hakaton_project)
PROJECT_ROOT = Path(__file__).parent.parent

st.set_page_config(page_title="Анализ движения судов", layout="wide")
st.title("🚢 Анализ движения судов по данным АИС")

# Поиск файлов в разных местах
def find_file(filename):
    """Ищет файл в корне проекта и в подпапках"""
    # Ищем в корне
    root_file = PROJECT_ROOT / filename
    if root_file.exists():
        return root_file
    
    # Ищем в папке data
    data_file = PROJECT_ROOT / "data" / filename
    if data_file.exists():
        return data_file
    
    # Ищем в папке metrics
    metrics_file = PROJECT_ROOT / "metrics" / filename
    if metrics_file.exists():
        return metrics_file
    
    return None

# Загрузка метрик (есть!)
metrics_path = find_file("metrics_per_ship.csv")
if metrics_path:
    metrics_df = pd.read_csv(metrics_path)
    st.success(f"✅ Загружены метрики: {len(metrics_df)} судов")
else:
    st.error("❌ metrics_per_ship.csv не найден!")
    st.stop()

# Загрузка clean_data (нужно найти!)
clean_path = find_file("clean_data.csv")
if clean_path:
    clean_df = pd.read_csv(clean_path)
    # Преобразуем время, если нужно
    if 'datetime' in clean_df.columns:
        clean_df['datetime'] = pd.to_datetime(clean_df['datetime'])
    st.success(f"✅ Загружены данные треков: {len(clean_df)} записей")
else:
    st.error("❌ clean_data.csv не найден! Дождитесь, пока Маша подготовит файл.")
    st.info("📌 Файл должен лежать в папке hakaton_project/ или hakaton_project/data/")
    
    # Показываем, какие файлы есть в проекте
    st.subheader("📁 Найденные файлы в проекте:")
    for f in PROJECT_ROOT.glob("*"):
        if f.is_file():
            st.write(f"- {f.name}")
    for f in PROJECT_ROOT.glob("*/"):
        st.write(f"- 📂 {f.name}/")
    
    st.stop()

# Боковая панель
st.sidebar.header("⚙️ Настройки")

# Получаем топ-5 судов
top5_ships = metrics_df.nlargest(5, 'total_distance_nm')['mmsi'].tolist()
ship_list = sorted(metrics_df['mmsi'].tolist())

selected = st.sidebar.selectbox(
    "Выберите судно:", 
    ["🌟 Все топ-5 судов"] + ship_list
)

if selected == "🌟 Все топ-5 судов":
    show_all = True
    df_filtered = clean_df[clean_df['mmsi'].isin(top5_ships)]
else:
    show_all = False
    df_filtered = clean_df[clean_df['mmsi'] == selected]
    ship_metrics = metrics_df[metrics_df['mmsi'] == selected].iloc[0]

# ==================== МЕТРИКИ ====================
if not show_all:
    st.subheader(f"📊 Метрики судна {selected}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚀 Пройденное расстояние", f"{ship_metrics['total_distance_nm']:.1f} миль")
    with col2:
        st.metric("⏱️ Средняя скорость", f"{ship_metrics['avg_speed_knots']:.1f} узлов")
    with col3:
        st.metric("⚡ Макс. скорость", f"{ship_metrics['max_speed_knots']:.1f} узлов")
    with col4:
        st.metric("⌛ Длительность", f"{ship_metrics['duration_hours']:.1f} ч")
else:
    st.subheader("🏆 Топ-5 судов по пройденному расстоянию")
    st.dataframe(metrics_df.nlargest(5, 'total_distance_nm')[['mmsi', 'total_distance_nm', 'duration_hours', 'avg_speed_knots']])

st.markdown("---")

# ==================== КАРТА ====================
st.header("🗺️ Трек судна")

if not df_filtered.empty:
    center_lat = df_filtered['latitude_deg'].mean()
    center_lon = df_filtered['longitude_deg'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
    
    if show_all:
        colors = ['red', 'blue', 'green', 'purple', 'orange']
        for i, ship_id in enumerate(top5_ships):
            ship_df = clean_df[clean_df['mmsi'] == ship_id].sort_values('datetime')
            points = list(zip(ship_df['latitude_deg'], ship_df['longitude_deg']))
            if len(points) > 1:
                folium.PolyLine(points, color=colors[i % len(colors)], weight=3, opacity=0.8, popup=f"Судно {ship_id}").add_to(m)
    else:
        ship_df = df_filtered.sort_values('datetime')
        points = list(zip(ship_df['latitude_deg'], ship_df['longitude_deg']))
        if len(points) > 1:
            folium.PolyLine(points, color='blue', weight=3, opacity=0.8).add_to(m)
            # Маркеры
            folium.Marker(points[0], popup="🟢 Старт", icon=folium.Icon(color='green')).add_to(m)
            folium.Marker(points[-1], popup="🔴 Финиш", icon=folium.Icon(color='red')).add_to(m)
    
    st_folium(m, width=700, height=500)
else:
    st.warning("Нет данных для отображения")

st.markdown("---")

# ==================== ГРАФИК СКОРОСТИ ====================
st.header("📈 График скорости")

if not show_all and not df_filtered.empty:
    ship_df = df_filtered.sort_values('datetime')
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Проверяем, есть ли колонка speed_knots
    if 'speed_knots' in ship_df.columns:
        ax.plot(ship_df['datetime'], ship_df['speed_knots'], 'o-', linewidth=1.5, markersize=3)
        ax.set_ylabel("Скорость (узлы)")
    elif 'ground_ms' in ship_df.columns:
        # Пересчитываем скорость если нужно
        speed = (ship_df['ground_ms'] / 1000) * 1.94384
        ax.plot(ship_df['datetime'], speed, 'o-', linewidth=1.5, markersize=3)
        ax.set_ylabel("Скорость (узлы)")
    
    ax.set_xlabel("Время")
    ax.set_title(f"Скорость судна {selected}")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
elif show_all:
    st.info("💡 Выберите отдельное судно, чтобы увидеть график скорости")