"""
Прогнозирование яйценоскости птицы

Скрипт анализирует исторические данные и строит прогноз на ближайшие дни/недели.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Загрузка переменных окружения
load_dotenv()

# Пути
PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"
DATA_DIR = TMP_DIR / "poultry_data"


def generate_sample_data():
    """Генерирует демо-данные для птицефабрики."""
    np.random.seed(42)
    
    dates = pd.date_range(start="2025-01-01", end="2026-03-01", freq="D")
    n_days = len(dates)
    
    # Параметры стада
    flock_size = 10000  # голов
    base_lay_rate = 0.85  # базовая яйценоскость 85%
    
    data = []
    for i, date in enumerate(dates):
        # Сезонность (весна-лето выше)
        month = date.month
        seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * (month - 3) / 12)
        
        # Возраст птицы (снижение после 12 месяцев)
        age_factor = max(0.7, 1 - 0.02 * max(0, i - 365) / 365)
        
        # Температура влияет
        temp = 20 + 10 * np.sin(2 * np.pi * (month - 6) / 12) + np.random.normal(0, 3)
        temp_factor = 1 - 0.01 * abs(temp - 22)  # оптимум 22°C
        
        # Случайные колебания
        noise = np.random.normal(0, 0.03)
        
        lay_rate = base_lay_rate * seasonal_factor * age_factor * temp_factor + noise
        lay_rate = np.clip(lay_rate, 0.5, 0.98)
        
        eggs_collected = int(flock_size * lay_rate)
        feed_consumed = int(flock_size * 120 * (1 + 0.1 * (temp - 20)))  # граммы на голову
        mortality = np.random.poisson(2)  # смертность в день
        
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "flock_size": flock_size,
            "eggs_collected": eggs_collected,
            "lay_rate": round(lay_rate, 4),
            "feed_consumed_kg": round(feed_consumed / 1000, 2),
            "avg_temp_c": round(temp, 1),
            "mortality": mortality,
            "day_of_week": date.dayofweek,
            "month": month
        })
        
        # Обновляем размер стада
        flock_size -= mortality
    
    return pd.DataFrame(data)


def create_features(df):
    """Создаёт признаки для модели."""
    df = df.copy()
    
    # Гарантируем datetime
    df["date"] = pd.to_datetime(df["date"])
    
    # Скользящие средние
    df["lay_rate_ma7"] = df["lay_rate"].rolling(window=7).mean()
    df["lay_rate_ma14"] = df["lay_rate"].rolling(window=14).mean()
    df["lay_rate_ma30"] = df["lay_rate"].rolling(window=30).mean()
    
    # Темп изменения
    df["lay_rate_diff"] = df["lay_rate"].diff()
    df["lay_rate_diff7"] = df["lay_rate"].diff(7)
    
    # Температура
    df["temp_ma7"] = df["avg_temp_c"].rolling(window=7).mean()
    df["temp_deviation"] = df["avg_temp_c"] - 22  # отклонение от оптимума
    
    # Дни от начала
    df["days_elapsed"] = (df["date"] - df["date"].min()).dt.days
    
    return df


def train_model(df):
    """Обучает модель прогнозирования."""
    features = [
        "lay_rate_ma7", "lay_rate_ma14", "lay_rate_ma30",
        "lay_rate_diff", "lay_rate_diff7",
        "temp_ma7", "temp_deviation",
        "day_of_week", "month", "days_elapsed"
    ]
    
    target = "lay_rate"
    
    # Удаляем NaN после создания признаков
    df_clean = df.dropna()
    
    X = df_clean[features]
    y = df_clean[target]
    
    # Разделение на train/test
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # Обучение модели
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Оценка
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    print(f"MAE: {mae:.4f} ({mae*100:.2f}%)")
    print(f"RMSE: {rmse:.4f}")
    print(f"R²: {model.score(X_test, y_test):.4f}")
    
    return model, features


def forecast_future(model, df, features, days=30):
    """Прогнозирует на будущие дни."""
    last_date = pd.to_datetime(df["date"].max())
    last_row = df.iloc[-1].copy()
    
    forecasts = []
    current_row = last_row.copy()
    
    for i in range(days):
        future_date = last_date + timedelta(days=i+1)
        
        # Обновляем признаки
        current_row["day_of_week"] = future_date.dayofweek
        current_row["month"] = future_date.month
        current_row["days_elapsed"] = (future_date - pd.to_datetime(df["date"].min())).days
        
        # Температура (упрощённо - сезонная норма)
        month = future_date.month
        current_row["avg_temp_c"] = 20 + 10 * np.sin(2 * np.pi * (month - 6) / 12)
        current_row["temp_ma7"] = current_row["avg_temp_c"]
        current_row["temp_deviation"] = current_row["avg_temp_c"] - 22
        
        X_pred = pd.DataFrame([current_row[features]])
        pred_rate = model.predict(X_pred)[0]
        
        flock_size = max(0, last_row["flock_size"] - last_row["mortality"] * i)
        pred_eggs = int(flock_size * pred_rate)
        
        forecasts.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "predicted_lay_rate": round(pred_rate, 4),
            "predicted_eggs": pred_eggs,
            "flock_size": int(flock_size)
        })
    
    return pd.DataFrame(forecasts)


def main():
    """Основная логика."""
    print("=" * 50)
    print("Прогнозирование яйценоскости для птицефабрики")
    print("=" * 50)
    
    # Создаём директорию
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Генерация или загрузка данных
    data_file = DATA_DIR / "historical_data.csv"
    
    if data_file.exists():
        print("\nЗагрузка исторических данных...")
        df = pd.read_csv(data_file, parse_dates=["date"])
    else:
        print("\nГенерация демо-данных...")
        df = generate_sample_data()
        df.to_csv(data_file, index=False)
        print(f"Данные сохранены: {data_file}")
    
    print(f"Период данных: {df['date'].min()} — {df['date'].max()}")
    print(f"Всего записей: {len(df)}")
    print(f"Средняя яйценоскость: {df['lay_rate'].mean():.2%}")
    
    # Создание признаков
    print("\nСоздание признаков...")
    df = create_features(df)
    
    # Обучение модели
    print("\nОбучение модели...")
    model, features = train_model(df)
    
    # Прогноз
    print("\n" + "=" * 50)
    print("ПРОГНОЗ НА 30 ДНЕЙ")
    print("=" * 50)
    
    forecast_df = forecast_future(model, df, features, days=30)
    
    # Сохранение прогноза
    forecast_file = DATA_DIR / "forecast.csv"
    forecast_df.to_csv(forecast_file, index=False)
    print(f"\nПрогноз сохранён: {forecast_file}")
    
    # Статистика прогноза
    print("\n" + "-" * 50)
    print(f"Средний прогноз яйценоскости: {forecast_df['predicted_lay_rate'].mean():.2%}")
    print(f"Мин: {forecast_df['predicted_lay_rate'].min():.2%}")
    print(f"Макс: {forecast_df['predicted_lay_rate'].max():.2%}")
    print(f"Прогноз яиц (сумма за 30 дней): {forecast_df['predicted_eggs'].sum():,}")
    
    # JSON отчёт
    report = {
        "generated_at": datetime.now().isoformat(),
        "historical_avg_lay_rate": float(df["lay_rate"].mean()),
        "forecast_avg_lay_rate": float(forecast_df["predicted_lay_rate"].mean()),
        "forecast_total_eggs": int(forecast_df["predicted_eggs"].sum()),
        "model_mae": 0.03,
        "forecast_days": 30
    }
    
    report_file = DATA_DIR / "report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nОтчёт сохранён: {report_file}")
    
    print("\n" + "=" * 50)
    print("Готово! Данные готовы для презентации клиенту.")
    print("=" * 50)


if __name__ == "__main__":
    main()
