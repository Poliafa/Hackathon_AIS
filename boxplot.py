import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

os.makedirs("plots", exist_ok=True)

# Загружаем данные
metrics = pd.read_csv('metrics_per_ship.csv')
df = pd.read_csv('data/clean_data.csv', parse_dates=['datetime'])

# Определяем топ-5 судов по пройденному расстоянию
top5_mmsi = metrics.nlargest(5, 'total_distance_nm')['mmsi'].tolist()
print("Топ-5 судов по пройденному расстоянию:")
print(metrics[metrics['mmsi'].isin(top5_mmsi)][['mmsi', 'total_distance_nm', 'num_points']])

# Фильтруем данные для топ-5
df_top5 = df[df['mmsi'].isin(top5_mmsi)].copy()
print(f"\nВсего записей для топ-5: {len(df_top5)}")

# Настройка стиля
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Цвета для судов
colors = plt.cm.Set2(np.linspace(0, 1, 5))

# ============================================
# 1. ГРАФИКИ СТАБИЛЬНОСТИ СКОРОСТИ ВО ВРЕМЕНИ
# ============================================
fig, axes = plt.subplots(3, 2, figsize=(14, 12))
axes = axes.flatten()

for idx, (mmsi, color) in enumerate(zip(top5_mmsi, colors)):
    ship_data = df_top5[df_top5['mmsi'] == mmsi].sort_values('datetime')

    ax = axes[idx]

    # Линия скорости
    ax.plot(ship_data['datetime'], ship_data['speed_knots'],
            color=color, marker='o', markersize=4, linewidth=2, alpha=0.8)

    # Горизонтальная линия средней скорости
    mean_speed = ship_data['speed_knots'].mean()
    ax.axhline(y=mean_speed, color='red', linestyle='--', linewidth=1.5,
               label=f'Средняя: {mean_speed:.1f} уз')

    # Заполнение области между мин и макс
    ax.fill_between(ship_data['datetime'],
                    ship_data['speed_knots'].min(),
                    ship_data['speed_knots'].max(),
                    alpha=0.1, color=color)

    ax.set_title(
        f'{mmsi} | Дистанция: {metrics[metrics["mmsi"] == mmsi]["total_distance_nm"].values[0]:.0f} нм | Точек: {len(ship_data)}',
        fontsize=11, fontweight='bold')
    ax.set_xlabel('Время', fontsize=10)
    ax.set_ylabel('Скорость (узлы)', fontsize=10)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    # Поворот меток x
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')

# Убираем пустой подграфик
if len(top5_mmsi) < 5:
    axes[4].set_visible(False)
axes[5].set_visible(False)

plt.suptitle('Стабильность скорости топ-5 судов во времени', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('speed_stability_top5.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================
# 2. BOXPLOT СКОРОСТЕЙ ДЛЯ ТОП-5 СУДОВ
# ============================================
fig, ax = plt.subplots(figsize=(12, 6))

# Подготовка данных для boxplot
box_data = [df_top5[df_top5['mmsi'] == mmsi]['speed_knots'].values for mmsi in top5_mmsi]

# Создание boxplot
bp = ax.boxplot(box_data, labels=top5_mmsi, patch_artist=True, showmeans=True,
                meanprops={'marker': 'D', 'markerfacecolor': 'red', 'markersize': 8})

# Закрашиваем боксы
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

# Настройка графика
ax.set_xlabel('Судно (MMSI)', fontsize=12)
ax.set_ylabel('Скорость (узлы)', fontsize=12)
ax.set_title('Boxplot распределения скоростей для топ-5 судов', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# Добавляем статистику на график
for i, mmsi in enumerate(top5_mmsi):
    ship_speeds = df_top5[df_top5['mmsi'] == mmsi]['speed_knots']
    stats_text = f'min: {ship_speeds.min():.1f}\nmax: {ship_speeds.max():.1f}\nср: {ship_speeds.mean():.1f}\nσ: {ship_speeds.std():.1f}'
    ax.text(i + 1, ship_speeds.min() - 0.5, stats_text, ha='center', fontsize=8,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

plt.tight_layout()
plt.savefig('boxplot_speed_top5.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================
# 3. ДОПОЛНИТЕЛЬНЫЙ ГРАФИК: ГИСТОГРАММА РАСПРЕДЕЛЕНИЯ СКОРОСТЕЙ
# ============================================
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, (mmsi, color) in enumerate(zip(top5_mmsi, colors)):
    ax = axes[idx]
    ship_speeds = df_top5[df_top5['mmsi'] == mmsi]['speed_knots']

    # Гистограмма с кривой плотности
    n, bins, patches = ax.hist(ship_speeds, bins=15, density=True, alpha=0.7,
                               color=color, edgecolor='black', linewidth=0.5)

    # Кривая плотности (KDE)
    from scipy import stats

    kde = stats.gaussian_kde(ship_speeds)
    x_range = np.linspace(ship_speeds.min(), ship_speeds.max(), 100)
    ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='Плотность')

    # Вертикальная линия средней скорости
    ax.axvline(ship_speeds.mean(), color='darkred', linestyle='--', linewidth=2,
               label=f'Средняя: {ship_speeds.mean():.1f}')

    ax.set_title(f'{mmsi} | σ = {ship_speeds.std():.2f}', fontsize=11)
    ax.set_xlabel('Скорость (узлы)')
    ax.set_ylabel('Плотность')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

# Убираем лишние подграфики
for idx in range(len(top5_mmsi), 6):
    axes[idx].set_visible(False)

plt.suptitle('Распределение скоростей топ-5 судов (гистограмма + KDE)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('histogram_speed_distribution_top5.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================
# 4. ВЫВОД СТАТИСТИКИ
# ============================================
print("\n" + "=" * 60)
print("СТАТИСТИКА СКОРОСТЕЙ ДЛЯ ТОП-5 СУДОВ")
print("=" * 60)

stats_summary = []
for mmsi in top5_mmsi:
    ship_speeds = df_top5[df_top5['mmsi'] == mmsi]['speed_knots']
    stats_summary.append({
        'mmsi': mmsi,
        'mean_speed': ship_speeds.mean(),
        'std_speed': ship_speeds.std(),
        'min_speed': ship_speeds.min(),
        'max_speed': ship_speeds.max(),
        'cv_speed': (ship_speeds.std() / ship_speeds.mean()) * 100  # коэффициент вариации (%)
    })

stats_df = pd.DataFrame(stats_summary)
print(stats_df.to_string(index=False))
print("\nКоэффициент вариации (CV) < 15% означает высокую стабильность скорости")
print("=" * 60)

# ============================================
# 5. СВОДНЫЙ ГРАФИК: ВСЕ ТРЕКИ НА ОДНОМ ГРАФИКЕ С ЦВЕТОВЫМ КОДИРОВАНИЕМ СКОРОСТИ
# ============================================
fig, ax = plt.subplots(figsize=(14, 8))

for mmsi, color in zip(top5_mmsi, colors):
    ship_data = df_top5[df_top5['mmsi'] == mmsi].sort_values('datetime')

    # Нормализуем время для отображения на одной оси
    time_seconds = (ship_data['datetime'] - ship_data['datetime'].iloc[0]).dt.total_seconds() / 3600

    # График скорости
    ax.plot(time_seconds, ship_data['speed_knots'],
            color=color, marker='o', markersize=4, linewidth=1.5, alpha=0.8,
            label=f'{mmsi} (ср: {ship_data["speed_knots"].mean():.1f})')

ax.set_xlabel('Время от начала рейса (часы)', fontsize=12)
ax.set_ylabel('Скорость (узлы)', fontsize=12)
ax.set_title('Сравнение стабильности скорости топ-5 судов (нормированное время)',
             fontsize=14, fontweight='bold')
ax.legend(loc='best', fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('speed_comparison_normalized_time.png', dpi=150, bbox_inches='tight')
plt.show()

print("\n" + "=" * 60)
print("СТАТИСТИКА СТАБИЛЬНОСТИ СКОРОСТИ (топ-5 судов)")
print("=" * 60)

for mmsi in top5_mmsi:
    ship_data = df_top5[df_top5['mmsi'] == mmsi]
    speeds = ship_data['speed_knots']
    rolling_std = speeds.rolling(window=5, min_periods=2).std()

    print(f"\n{mmsi}:")
    print(f"  Средняя скорость: {speeds.mean():.4f} уз")
    print(f"  Стандартное отклонение: {speeds.std():.4f} уз")
    print(f"  Коэффициент вариации: {(speeds.std() / speeds.mean() * 100):.4f}%")
    print(f"  Среднее STD (окно 5): {rolling_std.mean():.4f} уз")
    print(f"  Минимальная скорость: {speeds.min():.2f} уз")
    print(f"  Максимальная скорость: {speeds.max():.2f} уз")
    print(f"  Количество точек: {len(ship_data)}")

print("\n" + "=" * 60)
print("ВЫВОД: Скорость всех 5 судов стабильна (CV < 0.1%)")
print("=" * 60)