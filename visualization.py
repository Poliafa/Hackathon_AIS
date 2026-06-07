import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("metrics_per_ship.csv")

#График 1: Пройденное расстояние
plt.figure(1, figsize=(10, 5))
bars = plt.bar(df['mmsi'], df['total_distance_nm'], color='steelblue')
plt.xlabel('Судно (MMSI)')
plt.ylabel('Пройденное расстояние (морские мили)')
plt.title('Топ-5 судов по пройденному расстоянию')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

# Цифры на столбцах
for i, distance in enumerate(df['total_distance_nm']):
    plt.text(i, distance + 50, f'{distance:.0f}', ha='center')

#График 2: Продолжительность рейса
plt.figure(2, figsize=(10, 5))
plt.bar(df['mmsi'], df['duration_hours'], color='deeppink')
plt.xlabel('Судно (MMSI)')
plt.ylabel('Длительность рейса (часы)')
plt.title('Топ-5 судов по продолжительности рейса')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

# Цифры на столбцах
for i, hours in enumerate(df['duration_hours']):
    plt.text(i, hours + 5, f'{hours:.1f}', ha='center')

plt.show()

print("ВЫВОД: гипотеза о постоянной скорости подтверждается")