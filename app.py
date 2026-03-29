"""
Веб-приложение для прогнозирования яйценоскости птицы
Запуск: streamlit run app.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import streamlit as st

# Пути
PROJECT_ROOT = Path(__file__).parent
TMP_DIR = PROJECT_ROOT / ".tmp" / "poultry_data"


def generate_sample_data():
    """Генерирует демо-данные для птицефабрики."""
    np.random.seed(42)
    
    dates = pd.date_range(start="2025-01-01", end="2026-03-01", freq="D")
    n_days = len(dates)
    
    flock_size = 10000
    base_lay_rate = 0.85
    
    data = []
    for i, date in enumerate(dates):
        month = date.month
        seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * (month - 3) / 12)
        age_factor = max(0.7, 1 - 0.02 * max(0, i - 365) / 365)
        temp = 20 + 10 * np.sin(2 * np.pi * (month - 6) / 12) + np.random.normal(0, 3)
        temp_factor = 1 - 0.01 * abs(temp - 22)
        noise = np.random.normal(0, 0.03)
        
        lay_rate = base_lay_rate * seasonal_factor * age_factor * temp_factor + noise
        lay_rate = np.clip(lay_rate, 0.5, 0.98)
        
        eggs_collected = int(flock_size * lay_rate)
        feed_consumed = int(flock_size * 120 * (1 + 0.1 * (temp - 20)))
        mortality = np.random.poisson(2)
        
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
        
        flock_size -= mortality
    
    return pd.DataFrame(data)


def create_features(df):
    """Создаёт признаки для модели."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    
    df["lay_rate_ma7"] = df["lay_rate"].rolling(window=7).mean()
    df["lay_rate_ma14"] = df["lay_rate"].rolling(window=14).mean()
    df["lay_rate_ma30"] = df["lay_rate"].rolling(window=30).mean()
    df["lay_rate_diff"] = df["lay_rate"].diff()
    df["lay_rate_diff7"] = df["lay_rate"].diff(7)
    df["temp_ma7"] = df["avg_temp_c"].rolling(window=7).mean()
    df["temp_deviation"] = df["avg_temp_c"] - 22
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
    
    df_clean = df.dropna()
    X = df_clean[features]
    y = df_clean["lay_rate"]
    
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    
    return model, features, mae


def forecast_future(model, df, features, days=30):
    """Прогнозирует на будущие дни."""
    last_date = pd.to_datetime(df["date"].max())
    last_row = df.iloc[-1].copy()
    
    forecasts = []
    current_row = last_row.copy()
    
    for i in range(days):
        future_date = last_date + timedelta(days=i+1)
        
        current_row["day_of_week"] = future_date.dayofweek
        current_row["month"] = future_date.month
        current_row["days_elapsed"] = (future_date - pd.to_datetime(df["date"].min())).days
        
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


def load_or_generate_data():
    """Загружает или генерирует данные."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    data_file = TMP_DIR / "historical_data.csv"
    
    if data_file.exists():
        df = pd.read_csv(data_file, parse_dates=["date"])
    else:
        df = generate_sample_data()
        df.to_csv(data_file, index=False)
    
    return df


# ============================================
# UI ПРИЛОЖЕНИЯ
# ============================================

st.set_page_config(
    page_title="Прогноз яйценоскости",
    page_icon="🥚",
    layout="wide"
)

st.title("🥚 Прогнозирование яйценоскости птицы")
st.markdown("---")

# Загрузка данных
with st.spinner("Загрузка данных..."):
    df = load_or_generate_data()
    df = create_features(df)
    model, features, mae = train_model(df)
    forecast_df = forecast_future(model, df, features, days=30)

# KPI метрики
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📊 Средняя яйценоскость",
        value=f"{df['lay_rate'].mean():.1%}",
        delta=f"{df['lay_rate'].std():.1%} σ"
    )

with col2:
    st.metric(
        label="📈 Прогноз (30 дней)",
        value=f"{forecast_df['predicted_lay_rate'].mean():.1%}",
        delta=f"{(forecast_df['predicted_lay_rate'].mean() - df['lay_rate'].mean()):.1%}"
    )

with col3:
    total_eggs = forecast_df['predicted_eggs'].sum()
    st.metric(
        label="🥚 Прогноз яиц",
        value=f"{total_eggs:,}",
        delta="за 30 дней"
    )

with col4:
    st.metric(
        label="🎯 Точность модели",
        value=f"{(1 - mae):.1%}",
        delta=f"MAE: {mae:.2%}"
    )

st.markdown("---")

# Графики
tab1, tab2, tab3 = st.tabs(["📈 Динамика", "📊 Анализ", "📋 Данные"])

with tab1:
    st.subheader("История и прогноз яйценоскости")
    
    # Объединение истории и прогноза
    hist_fig = go.Figure()
    
    hist_fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["lay_rate"],
        name="История",
        line=dict(color="blue", width=2),
        hovertemplate="%{x}<br>Яйценоскость: %{y:.1%}<extra></extra>"
    ))
    
    hist_fig.add_trace(go.Scatter(
        x=pd.to_datetime(forecast_df["date"]),
        y=forecast_df["predicted_lay_rate"],
        name="Прогноз",
        line=dict(color="green", width=2, dash="dash"),
        hovertemplate="%{x}<br>Прогноз: %{y:.1%}<extra></extra>"
    ))
    
    hist_fig.update_layout(
        height=400,
        xaxis_title="Дата",
        yaxis_title="Яйценоскость",
        yaxis_tickformat=".0%",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1)
    )
    
    st.plotly_chart(hist_fig, use_container_width=True)
    
    # Детальный прогноз по дням
    st.subheader("📅 Детальный прогноз на 30 дней")
    
    forecast_display = forecast_df.copy()
    forecast_display["date"] = pd.to_datetime(forecast_display["date"]).dt.strftime("%d.%m.%Y")
    forecast_display = forecast_display.rename(columns={
        "predicted_lay_rate": "Яйценоскость",
        "predicted_eggs": "Яиц (шт)",
        "flock_size": "Поголовье"
    })
    
    st.dataframe(
        forecast_display[["date", "Яйценоскость", "Яиц (шт)", "Поголовье"]].style.format({
            "Яйценоскость": "{:.1%}"
        }),
        use_container_width=True,
        height=400
    )

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Влияние температуры")
        
        temp_fig = go.Figure()
        temp_fig.add_trace(go.Scatter(
            x=df["avg_temp_c"],
            y=df["lay_rate"],
            mode="markers",
            marker=dict(color=df["lay_rate"], colorscale="RdYlGn", size=8),
            hovertemplate="Температура: %{x}°C<br>Яйценоскость: %{y:.1%}<extra></extra>"
        ))
        temp_fig.update_layout(
            height=350,
            xaxis_title="Температура (°C)",
            yaxis_title="Яйценоскость",
            yaxis_tickformat=".0%"
        )
        st.plotly_chart(temp_fig, use_container_width=True)
    
    with col2:
        st.subheader("Распределение яйценоскости")
        
        dist_fig = go.Figure()
        dist_fig.add_trace(go.Histogram(
            x=df["lay_rate"],
            nbinsx=30,
            marker_color="steelblue"
        ))
        dist_fig.add_vline(
            x=df["lay_rate"].mean(),
            line_dash="dash",
            line_color="red",
            annotation_text=f"Среднее: {df['lay_rate'].mean():.1%}"
        )
        dist_fig.update_layout(
            height=350,
            xaxis_title="Яйценоскость",
            xaxis_tickformat=".0%",
            showlegend=False
        )
        st.plotly_chart(dist_fig, use_container_width=True)
    
    # Поголовье и смертность
    st.subheader("🐔 Динамика поголовья")
    
    flock_fig = go.Figure()
    flock_fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["flock_size"],
        name="Поголовье",
        line=dict(color="orange", width=2)
    ))
    flock_fig.update_layout(
        height=300,
        xaxis_title="Дата",
        yaxis_title="Количество птиц",
        showlegend=False
    )
    st.plotly_chart(flock_fig, use_container_width=True)

with tab3:
    st.subheader("Исторические данные")
    
    st.dataframe(
        df[["date", "flock_size", "eggs_collected", "lay_rate", "feed_consumed_kg", "mortality"]]
        .rename(columns={
            "date": "Дата",
            "flock_size": "Поголовье",
            "eggs_collected": "Собрано яиц",
            "lay_rate": "Яйценоскость",
            "feed_consumed_kg": "Корм (кг)",
            "mortality": "Смертность"
        })
        .style.format({
            "Дата": lambda x: x.strftime("%d.%m.%Y") if isinstance(x, pd.Timestamp) else x,
            "Яйценоскость": "{:.1%}"
        }),
        use_container_width=True,
        height=400
    )
    
    # Экспорт
    st.subheader("💾 Экспорт данных")
    
    csv_history = df.to_csv(index=False).encode("utf-8")
    csv_forecast = forecast_df.to_csv(index=False).encode("utf-8")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Скачать историю (CSV)",
            data=csv_history,
            file_name="historical_data.csv",
            mime="text/csv"
        )
    with col2:
        st.download_button(
            label="📥 Скачать прогноз (CSV)",
            data=csv_forecast,
            file_name="forecast.csv",
            mime="text/csv"
        )

# Боковая панель
with st.sidebar:
    st.header("⚙️ Настройки")
    
    st.info(f"""
    **Данные:**
    - Период: {df['date'].min().strftime('%d.%m.%Y')} — {df['date'].max().strftime('%d.%m.%Y')}
    - Записей: {len(df):,}
    - Точность модели: {(1 - mae):.1%}
    """)
    
    st.markdown("---")
    st.markdown("""
    ### 📞 Контакты
    
    По вопросам внедрения:
    - 📧 email@example.com
    - 📱 +998 90 123 45 67
    """)

# Футер
st.markdown("---")
st.caption("🤖 Industrial AI Hub | Прогнозирование для птицефабрик")
