import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

FEATURES = [
    "pm2_5", "pm10", "nitrogen_dioxide", "sulphur_dioxide",
    "ozone", "hour", "day_of_week"
]

def train_pm25_model(hourly: pd.DataFrame) -> dict:
    df = hourly.copy().sort_values("time")
    df["hour"] = df["time"].dt.hour
    df["day_of_week"] = df["time"].dt.dayofweek
    df["target_next_hour_pm25"] = df["pm2_5"].shift(-1)

    usable = df[FEATURES + ["target_next_hour_pm25"]].dropna()
    if len(usable) < 100:
        raise ValueError("Not enough complete historical records to train reliably yet.")

    X = usable[FEATURES]
    y = usable["target_next_hour_pm25"]

    split = int(len(usable) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=8,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)

    latest = df.dropna(subset=FEATURES).iloc[[-1]]
    next_value = float(model.predict(latest[FEATURES])[0])

    return {
        "prediction": max(0.0, next_value),
        "mae": float(mae),
        "rows": int(len(usable)),
    }
