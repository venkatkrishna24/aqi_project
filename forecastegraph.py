import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time

# -------------------- Configuration --------------------
API_KEY = "71b5019314b0f31dbdb2dab77af530ad"  # <-- Replace this!
LAT, LON = 13.0827, 80.2707  # Chennai
END = int(time.time())  # current time
START = END - (5 * 24 * 60 * 60)  # 5 days ago

# -------------------- Helper Function --------------------
def fetch_api_data(url, label=""):
    print(f"\n🔄 Fetching {label} data...")
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        if "list" not in data:
            print(f"⚠️ API returned error for {label}: {data}")
            return []
        return data["list"]
    except requests.exceptions.HTTPError as err:
        print(f"❌ HTTP Error: {err}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
    return []

def build_dataframe(data, label):
    return pd.DataFrame([{
        "datetime": datetime.utcfromtimestamp(item["dt"]),
        "aqi": item["main"]["aqi"]
    } for item in data]).assign(source=label)

# -------------------- Historical Data --------------------
history_url = (
    f"https://api.openweathermap.org/data/2.5/air_pollution/history"
    f"?lat={LAT}&lon={LON}&start={START}&end={END}&appid={API_KEY}"
)
history_data = fetch_api_data(history_url, "Historical")
df_hist = build_dataframe(history_data, "Historical") if history_data else pd.DataFrame()

# -------------------- Forecast Data --------------------
forecast_url = (
    f"https://api.openweathermap.org/data/2.5/air_pollution/forecast"
    f"?lat={LAT}&lon={LON}&appid={API_KEY}"
)
forecast_data = fetch_api_data(forecast_url, "Forecast")
df_fore = build_dataframe(forecast_data, "Forecast") if forecast_data else pd.DataFrame()

# -------------------- Combine & Plot --------------------
df_combined = pd.concat([df_hist, df_fore])

if df_combined.empty:
    print("⚠️ No AQI data available. Please check your API key or internet connection.")
    exit()

# -------------------- Plotting --------------------
plt.figure(figsize=(14, 6))
for label, group in df_combined.groupby("source"):
    plt.plot(group["datetime"], group["aqi"], marker="o", label=label)

# AQI Category bands
plt.axhspan(0.5, 1.5, color='green', alpha=0.2, label='Good')
plt.axhspan(1.5, 2.5, color='yellow', alpha=0.2, label='Fair')
plt.axhspan(2.5, 3.5, color='orange', alpha=0.2, label='Moderate')
plt.axhspan(3.5, 4.5, color='red', alpha=0.2, label='Poor')
plt.axhspan(4.5, 5.5, color='purple', alpha=0.2, label='Very Poor')

plt.title("AQI: Historical + Forecast (Chennai)")
plt.xlabel("Datetime")
plt.ylabel("AQI Level (1=Good, 5=Very Poor)")
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.show()
