# role_7_complete.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Создаём папку для графиков
os.makedirs("plots", exist_ok=True)

print("=" * 60)
print("РОЛЬ 7. КАЧЕСТВО СИГНАЛА, АНОМАЛИИ И ИЗВИЛИСТОСТЬ")
print("=" * 60)

# Загружаем данные
print("\nЗагрузка данных из clean_data.csv...")
df = pd.read_csv('data/clean_data.csv', parse_dates=['datetime'])
print(f"Загружено строк: {len(df)}")
print(f"Уникальных судов: {df['mmsi'].nunique()}")

# ============================================
# 7.1. КАЧЕСТВО СИГНАЛА
# ============================================
print("\n" + "=" * 60)
print("7.1. КАЧЕСТВО СИГНАЛА")
print("=" * 60)

# Проверяем наличие поля valid
if 'valid' in df.columns:
    print("\nАнализ поля valid (синхронизация PPS)...")

    # Для каждого судна вычисляем долю невалидных PPS
    quality_data = []
    for mmsi, group in df.groupby('mmsi'):
        total = len(group)
        if group['valid'].dtype == 'bool':
            invalid = (~group['valid']).sum()
        else:
            invalid = (group['valid'] == 0).sum()

        error_pct = (invalid / total * 100) if total > 0 else 0
        quality_data.append({
            'mmsi': mmsi,
            'total': total,
            'invalid': invalid,
            'error_pct': error_pct
        })

    quality_df = pd.DataFrame(quality_data)
    quality_df = quality_df.sort_values('error_pct', ascending=False)

    print(f"\nСтатистика по качеству сигнала:")
    print(f"  Средняя доля ошибок: {quality_df['error_pct'].mean():.2f}%")
    print(f"  Медианная доля ошибок: {quality_df['error_pct'].median():.2f}%")

    # Судно с худшим качеством
    worst = quality_df.iloc[0]
    print(f"\n⚠️ Судно с ХУДШИМ качеством сигнала: {worst['mmsi']}")
    print(f"   Невалидных PPS: {worst['invalid']} из {worst['total']} ({worst['error_pct']:.2f}%)")

    # Столбчатая диаграмма (топ-20)
    top_n = min(20, len(quality_df))
    quality_top = quality_df.head(top_n)

    plt.figure(figsize=(12, 6))
    bars = plt.bar(range(len(quality_top)), quality_top['error_pct'], color='steelblue', alpha=0.7)
    bars[0].set_color('red')
    plt.xlabel('Судно (MMSI)')
    plt.ylabel('Доля невалидных сигналов (%)')
    plt.title(f'Доля ошибок PPS по судам (топ-{top_n})')
    plt.xticks(range(len(quality_top)), quality_top['mmsi'], rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    for i, row in enumerate(quality_top.iterrows()):
        if row[1]['error_pct'] > 1:
            plt.text(i, row[1]['error_pct'] + 0.5, f'{row[1]["error_pct"]:.1f}%', ha='center', fontsize=8)

    plt.tight_layout()
    plt.savefig('plots/signal_quality.png', dpi=150)
    plt.show()
    print("\n✅ Сохранён: plots/signal_quality.png")
else:
    print("\n⚠️ Поле 'valid' не найдено в данных")
    print("Доступные колонки:", df.columns.tolist())


# ============================================
# Функция для расчёта расстояния (Haversine)
# ============================================
def haversine_nm(lat1, lon1, lat2, lon2):
    """Расстояние в морских милях"""
    R = 3440.065
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


# ============================================
# 7.2. АНОМАЛЬНЫЕ СКАЧКИ СКОРОСТИ
# ============================================
print("\n" + "=" * 60)
print("7.2. АНОМАЛЬНЫЕ СКАЧКИ СКОРОСТИ")
print("=" * 60)

SPEED_LIMIT = 60  # узлов

all_points = []
anomalies = []

for mmsi, group in df.groupby('mmsi'):
    group = group.sort_values('datetime')
    if len(group) < 2:
        continue

    for i in range(len(group) - 1):
        r1, r2 = group.iloc[i], group.iloc[i + 1]

        # Расстояние и время
        dist = haversine_nm(r1['latitude_deg'], r1['longitude_deg'],
                            r2['latitude_deg'], r2['longitude_deg'])
        dt_hours = (r2['datetime'] - r1['datetime']).total_seconds() / 3600

        # Мгновенная скорость
        inst_speed = dist / dt_hours if dt_hours > 0 else 0
        is_anomaly = inst_speed > SPEED_LIMIT

        all_points.append({
            'mmsi': mmsi,
            'time': r1['datetime'],
            'recorded_speed': r1['speed_knots'],
            'instant_speed': inst_speed,
            'is_anomaly': is_anomaly
        })

        if is_anomaly:
            anomalies.append({
                'mmsi': mmsi,
                'time': r1['datetime'],
                'instant_speed': inst_speed,
                'dist_nm': dist,
                'dt_sec': dt_hours * 3600
            })

points_df = pd.DataFrame(all_points)
anomalies_df = pd.DataFrame(anomalies) if anomalies else pd.DataFrame()

print(f"\nВсего переходов между точками: {len(points_df)}")
print(f"Аномалий (> {SPEED_LIMIT} уз): {len(anomalies_df)}")
if len(points_df) > 0:
    print(f"Доля аномалий: {len(anomalies_df) / len(points_df) * 100:.3f}%")

if len(anomalies_df) > 0:
    print(f"\nМаксимальная мгновенная скорость: {anomalies_df['instant_speed'].max():.1f} уз")
    print(f"Средняя аномальная скорость: {anomalies_df['instant_speed'].mean():.1f} уз")

    # Scatter-график
    plt.figure(figsize=(14, 6))

    normal = points_df[~points_df['is_anomaly']]
    anom = points_df[points_df['is_anomaly']]

    plt.scatter(normal['time'], normal['instant_speed'],
                c='blue', s=10, alpha=0.5, label='Нормальная скорость')
    plt.scatter(anom['time'], anom['instant_speed'],
                c='red', s=50, alpha=0.8, marker='x', label=f'Аномалия > {SPEED_LIMIT} уз')

    plt.axhline(y=SPEED_LIMIT, color='red', linestyle='--', alpha=0.7)
    plt.xlabel('Время')
    plt.ylabel('Мгновенная скорость (узлы)')
    plt.title('Аномальные скачки скорости в данных AIS')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('plots/speed_anomalies.png', dpi=150)
    plt.show()
    print("\n✅ Сохранён: plots/speed_anomalies.png")

    # Вывод
    print("\n" + "=" * 60)
    print("ВЫВОД ПО АНОМАЛИЯМ:")
    print("=" * 60)
    print("""  
    Аномальные скачки скорости (>60 узлов) связаны с ОШИБКАМИ ДАННЫХ:
    - Сбой GPS приёмника
    - Ошибка декодирования AIS-сообщения
    - Потеря синхронизации (valid=False)

    Реальное ускорение до 60+ узлов маловероятно для торговых судов,
    крейсерская скорость которых составляет ~15 узлов.
    """)
else:
    print("\n✅ Аномальных скачков скорости не обнаружено!")

# ============================================
# 7.3. ИЗВИЛИСТОСТЬ МАРШРУТА
# ============================================
print("\n" + "=" * 60)
print("7.3. ИЗВИЛИСТОСТЬ МАРШРУТА")
print("=" * 60)


def calculate_sinuosity(group):
    """Коэффициент извилистости = фактический путь / прямая дистанция"""
    if len(group) < 2:
        return None

    lats = group['latitude_deg'].values
    lons = group['longitude_deg'].values

    # Прямая дистанция (первая - последняя точка)
    straight = haversine_nm(lats[0], lons[0], lats[-1], lons[-1])

    # Фактическая дистанция (сумма сегментов)
    actual = 0
    for i in range(len(lats) - 1):
        actual += haversine_nm(lats[i], lons[i], lats[i + 1], lons[i + 1])

    sinuosity = actual / straight if straight > 0 else 1.0
    return sinuosity, actual, straight


windiness = []
for mmsi, group in df.groupby('mmsi'):
    if len(group) >= 2:
        sin, actual, straight = calculate_sinuosity(group)
        windiness.append({
            'mmsi': mmsi,
            'sinuosity': sin,
            'actual_nm': actual,
            'straight_nm': straight,
            'n_points': len(group)
        })

wind_df = pd.DataFrame(windiness)
wind_df = wind_df.sort_values('sinuosity')

print(f"\nПроанализировано маршрутов: {len(wind_df)}")
print(f"\nСтатистика извилистости:")
print(f"  Средний коэффициент: {wind_df['sinuosity'].mean():.4f}")
print(f"  Медианный: {wind_df['sinuosity'].median():.4f}")
print(f"  Минимальный (самый прямой): {wind_df['sinuosity'].min():.4f}")
print(f"  Максимальный (самый извилистый): {wind_df['sinuosity'].max():.4f}")

# Самое прямое судно
straightest = wind_df.iloc[0]
print(f"\n✅ Судно с САМЫМ ПРЯМЫМ маршрутом: {straightest['mmsi']}")
print(f"   Коэффициент извилистости: {straightest['sinuosity']:.4f}")
print(f"   Фактический путь: {straightest['actual_nm']:.1f} нм")
print(f"   Прямая дистанция: {straightest['straight_nm']:.1f} нм")

# Самое извилистое
windiest = wind_df.iloc[-1]
print(f"\n⚠️ Судно с САМЫМ ИЗВИЛИСТЫМ маршрутом: {windiest['mmsi']}")
print(f"   Коэффициент извилистости: {windiest['sinuosity']:.4f}")

# Столбчатая диаграмма (топ-20 самых прямых)
top_n = min(20, len(wind_df))
wind_top = wind_df.head(top_n)

plt.figure(figsize=(12, 6))
colors_wind = ['green' if s < 1.05 else 'orange' if s < 1.2 else 'red' for s in wind_top['sinuosity']]
bars = plt.bar(range(len(wind_top)), wind_top['sinuosity'], color=colors_wind, alpha=0.7)
plt.xlabel('Судно (MMSI)')
plt.ylabel('Коэффициент извилистости')
plt.title(f'Извилистость маршрутов (топ-{top_n} самых прямых)')
plt.xticks(range(len(wind_top)), wind_top['mmsi'], rotation=45, ha='right')
plt.axhline(y=1.0, color='green', linestyle='--', label='Идеально прямой (1.0)')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.savefig('plots/route_windiness.png', dpi=150)
plt.show()
print("\n✅ Сохранён: plots/route_windiness.png")

# Гистограмма распределения
plt.figure(figsize=(10, 5))
plt.hist(wind_df['sinuosity'], bins=25, color='steelblue', alpha=0.7, edgecolor='black')
plt.axvline(x=1.0, color='green', linestyle='--', label='Прямой (1.0)')
plt.axvline(x=wind_df['sinuosity'].mean(), color='red', linestyle='--',
            label=f'Среднее: {wind_df["sinuosity"].mean():.3f}')
plt.xlabel('Коэффициент извилистости')
plt.ylabel('Количество маршрутов')
plt.title('Распределение извилистости маршрутов')
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('plots/windiness_distribution.png', dpi=150)
plt.show()
print("✅ Сохранён: plots/windiness_distribution.png")

# ============================================
# ФИНАЛЬНЫЙ ВЫВОД (как в первом запросе)
# ============================================
print("\n" + "=" * 60)
print("ИТОГОВАЯ СТАТИСТИКА:")
print("=" * 60)
print(f"Суда с худшим качеством сигнала: {worst['mmsi']} ({worst['error_pct']:.2f}% ошибок)")
print(f"Аномальных скачков скорости: {len(anomalies_df)} ({len(anomalies_df) / len(points_df) * 100:.3f}%)")
print(f"Самая прямая траектория: {straightest['mmsi']} (коэфф. {straightest['sinuosity']:.4f})")
print(f"\nФайлы сохранены в папку plots/")
print("=" * 60)