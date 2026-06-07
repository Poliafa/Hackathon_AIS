# clean_data.py
import pandas as pd
import os

INPUT_FILE = r"C:\Users\User\PycharmProjects\hahahaha\data\raw_data.csv"
OUTPUT_FILE = r"C:\Users\User\PycharmProjects\hahahaha\clean_data.csv"


def load_and_clean_data(input_path=INPUT_FILE, output_path=OUTPUT_FILE):
    print("=" * 60)
    print("ОЧИСТКА ДАННЫХ AIS")
    print("=" * 60)

    # 1. Загрузить data/raw_data.csv
    print(f"\nЗагрузка данных из {input_path}...")

    if not os.path.exists(input_path):
        print(f"Ошибка: файл {input_path} не найден")
        return None

    df = pd.read_csv(input_path)
    print(f"Загружено строк: {len(df)}")

    # 2. Удалить строки с нулевыми координатами (0, 0)
    print("\nУдаление строк с нулевыми координатами...")
    before_count = len(df)

    df['latitude_deg'] = pd.to_numeric(df['latitude_deg'], errors='coerce')
    df['longitude_deg'] = pd.to_numeric(df['longitude_deg'], errors='coerce')

    mask_zero = (df['latitude_deg'].abs() < 0.0001) & (df['longitude_deg'].abs() < 0.0001)
    df = df[~mask_zero]
    df = df.dropna(subset=['latitude_deg', 'longitude_deg'])

    after_count = len(df)
    removed = before_count - after_count
    print(f"Удалено строк: {removed} ({(removed / before_count * 100):.1f}%)")

    # 3. Преобразовать utc_s в читаемый формат datetime
    print("\nПреобразование времени...")
    df['utc_s'] = pd.to_numeric(df['utc_s'], errors='coerce')

    # Удаляем строки с некорректным временем (0 или None)
    before_time = len(df)
    df = df[df['utc_s'].notna()]
    df = df[df['utc_s'] > 0]  # удаляем нулевые метки времени (1970-01-01)
    after_time = len(df)

    if before_time > after_time:
        print(f"Удалено строк с некорректным временем: {before_time - after_time}")

    df['datetime'] = pd.to_datetime(df['utc_s'], unit='s', errors='coerce')
    valid_dates = df['datetime'].notna().sum()
    print(f"Преобразовано строк: {valid_dates} из {len(df)}")

    if valid_dates > 0:
        print(f"Диапазон дат: {df['datetime'].min()} - {df['datetime'].max()}")

    # 4. Пересчитать скорость: ground_ms → узлы (коэффициент 1.94384)
    print("\nПересчёт скорости...")
    df['ground_ms'] = pd.to_numeric(df['ground_ms'], errors='coerce')

    # ground_ms в миллиметрах в секунду, переводим в узлы
    df['speed_knots'] = (df['ground_ms'] / 1000) * 1.94384
    df['speed_knots'] = df['speed_knots'].round(2)

    print(f"Добавлена колонка 'speed_knots'")
    print(f"Скорость: мин={df['speed_knots'].min():.1f}, "
          f"макс={df['speed_knots'].max():.1f}, "
          f"средняя={df['speed_knots'].mean():.1f} узлов")

    # 5. Отсортировать записи внутри каждого судна по времени
    print("\nСортировка записей...")
    df = df.sort_values(['mmsi', 'datetime'])
    print("Отсортировано по судну и времени")

    # 6. Удалить дубликаты (одинаковое судно, время, координаты)
    print("\nУдаление дубликатов...")
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['mmsi', 'datetime', 'latitude_deg', 'longitude_deg'], keep='first')
    after_dedup = len(df)
    removed = before_dedup - after_dedup
    print(f"Удалено дубликатов: {removed}")
    print(f"Осталось уникальных записей: {after_dedup}")

    # 7. Сохранить результат
    print(f"\nСохранение результата в {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8')

    # Финальная статистика
    print("\n" + "=" * 60)
    print("ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 60)
    print(f"Итоговое количество записей: {len(df)}")
    print(f"Уникальных судов: {df['mmsi'].nunique()}")

    if len(df) > 0 and df['datetime'].notna().any():
        print(f"Диапазон дат: {df['datetime'].min()} - {df['datetime'].max()}")

    print(f"Средняя скорость: {df['speed_knots'].mean():.1f} узлов")
    print(f"Максимальная скорость: {df['speed_knots'].max():.1f} узлов")
    print(f"\nФайл сохранён: {output_path}")
    print("=" * 60)

    return df


def main():
    print("\nЗАПУСК СКРИПТА ОЧИСТКИ ДАННЫХ")
    load_and_clean_data()


if __name__ == "__main__":
    main()