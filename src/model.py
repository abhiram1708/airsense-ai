"""Baseline next-hour PM2.5 model with an honest held-out evaluation."""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

FEATURES = [
    "pm2_5",
    "pm10",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "hour",
    "day_of_week",
]

FEATURE_LABELS = {
    "pm2_5": "PM₂.₅",
    "pm10": "PM₁₀",
    "nitrogen_dioxide": "NO₂",
    "sulphur_dioxide": "SO₂",
    "ozone": "O₃",
    "hour": "Hour of day",
    "day_of_week": "Day of week",
}


def train_pm25_model(hourly: pd.DataFrame) -> dict:
    df = hourly.copy().sort_values("time")
    required = ["time", "pm2_5", "pm10", "nitrogen_dioxide", "sulphur_dioxide", "ozone"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError("Missing model input columns: " + ", ".join(missing))

    for column in FEATURES[:-2] + ["pm2_5"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["hour"] = df["time"].dt.hour
    df["day_of_week"] = df["time"].dt.dayofweek
    df["target_next_hour_pm25"] = df["pm2_5"].shift(-1)
    usable = df[FEATURES + ["target_next_hour_pm25", "time"]].dropna()

    if len(usable) < 100:
        raise ValueError("Not enough complete historical records to train this baseline model.")

    X = usable[FEATURES]
    y = usable["target_next_hour_pm25"]
    split = int(len(usable) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = RandomForestRegressor(
        n_estimators=180,
        max_depth=9,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    test_predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, test_predictions)
    r2 = r2_score(y_test, test_predictions) if len(y_test) > 1 else 0.0

    # Persistence baseline: tomorrow's next hour looks like the current hour.
    persistence_predictions = X_test["pm2_5"]
    persistence_mae = mean_absolute_error(y_test, persistence_predictions)

    latest = df.dropna(subset=FEATURES).iloc[[-1]]
    prediction = float(model.predict(latest[FEATURES])[0])

    backtest = pd.DataFrame(
        {
            "time": usable.loc[X_test.index, "time"].to_numpy(),
            "Observed": y_test.to_numpy(),
            "Model": test_predictions,
            "Persistence": persistence_predictions.to_numpy(),
        }
    ).sort_values("time")

    return {
        "prediction": max(0.0, prediction),
        "mae": float(mae),
        "r2": float(r2),
        "persistence_mae": float(persistence_mae),
        "rows": int(len(usable)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "feature_importance": {
            FEATURE_LABELS.get(name, name): float(value)
            for name, value in zip(FEATURES, model.feature_importances_)
        },
        "backtest": backtest.tail(240),
    }
