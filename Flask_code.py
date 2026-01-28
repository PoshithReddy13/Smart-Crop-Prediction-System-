from flask import Flask, request
import csv
import pickle
import pandas as pd
import os
import requests
from datetime import date, timedelta

app = Flask(__name__)

# ============================================================
# Location & Rainfall
# ============================================================
def get_coordinates(location):
    url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers).json()
    return float(res[0]['lat']), float(res[0]['lon'])

def get_avg_rainfall(lat, lon):
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=365 * 10)

    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start}&end_date={end}"
        f"&daily=precipitation_sum"
    )
    data = requests.get(url).json()
    df = pd.DataFrame({
        "date": data["daily"]["time"],
        "rain": data["daily"]["precipitation_sum"]
    })
    return df["rain"].mean()

# ============================================================
# Load ML Artifacts
# ============================================================
model = pickle.load(open("crop_model.pkl", "rb"))
scaler = pickle.load(open("scaler.pkl", "rb"))
le = pickle.load(open("label_encoder.pkl", "rb"))

# ============================================================
# Location Input
# ============================================================
location = input("Enter location: ")
lat, lon = get_coordinates(location)
avg_rainfall = get_avg_rainfall(lat, lon)

# ============================================================
# CSV
# ============================================================
csv_file = "esp_data_log.csv"
if not os.path.exists(csv_file):
    with open(csv_file, "w", newline="") as f:
        csv.writer(f).writerow(
            ["temperature", "humidity", "P", "K", "ph", "ec", "rainfall", "crop"]
        )

# ============================================================
# ESP ENDPOINT
# ============================================================
@app.route("/sensor", methods=["POST"])
def sensor():
    data = request.get_json()

    df = pd.DataFrame([{
        "ph": float(data["ph"]),
        "soil_ec": float(data["ec"]),
        "P": float(data["phosphorus"]),
        "K": float(data["potassium"]),
        "humidity": float(data["humidity"]),
        "temperature": float(data["temperature"]),
        "rainfall": avg_rainfall
    }])

    df_scaled = scaler.transform(df)
    pred = model.predict(df_scaled)[0]
    crop = le.inverse_transform([pred])[0]

    with open(csv_file, "a", newline="") as f:
        csv.writer(f).writerow([
            data["temperature"], data["humidity"],
            data["phosphorus"], data["potassium"],
            data["ph"], data["ec"], avg_rainfall, crop
        ])

    return {"predicted_crop": crop}

@app.route("/")
def home():
    return "ESP32 Crop Prediction Server Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
