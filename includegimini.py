import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import google.generativeai as genai

# -------------------- CONFIG --------------------
OWM_API_KEY = "71b5019314b0f31dbdb2dab77af530ad"
GEMINI_API_KEY = "AIzaSyDsleB6zDYnNyLGRMzzwOt3lRkHzCODjgk"
# ------------------------------------------------

# 🧠 Set up Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-pro")  # Correct format

# 🌍 Get coordinates from place name
def get_coordinates(city_name):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={OWM_API_KEY}"
    try:
        response = requests.get(geo_url)
        response.raise_for_status()
        data = response.json()
        if len(data) == 0:
            print("❌ Location not found. Please check the name.")
            return None, None
        return data[0]["lat"], data[0]["lon"]
    except:
        print("❌ Could not fetch location data.")
        return None, None

# 📡 Fetch API data
def fetch_api_data(url, label=""):
    print(f"\n🔄 Fetching {label} data...")
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        if "list" not in data:
            print(f"⚠️ API error for {label}: {data}")
            return []
        return data["list"]
    except Exception as e:
        print(f"❌ Error fetching {label} data: {e}")
        return []

# 🔄 Convert to DataFrame
def build_dataframe(data, label):
    return pd.DataFrame([{
        "datetime": datetime.utcfromtimestamp(item["dt"]),
        "aqi": item["main"]["aqi"]
    } for item in data]).assign(source=label)

# 🧠 Get Gemini Health Advice
def get_health_advice(aqi_val, city):
    prompt = (
        f"The air quality index (AQI) in {city.title()} is {aqi_val} on a scale of 1 (Good) to 5 (Very Poor). "
        f"Give a short health alert and recommendation for residents. Include at-risk groups like kids or elderly if relevant."
    )
    try:
        response = model.generate_content(prompt)
        print("\n🧠 Gemini Health Advice:")
        print(response.text)
    except Exception as e:
        print("⚠️ Failed to get advice from Gemini:", e)

# 🚀 Main Program
city_name = input("Enter location name: ").strip()
lat, lon = get_coordinates(city_name)
if lat is None or lon is None:
    exit()

END = int(time.time())
START = END - (5 * 24 * 60 * 60)  # 5 days ago

# 🗂️ Historical
history_url = f"https://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={START}&end={END}&appid={OWM_API_KEY}"
history_data = fetch_api_data(history_url, "Historical")
df_hist = build_dataframe(history_data, "Historical") if history_data else pd.DataFrame()

# 🔮 Forecast
forecast_url = f"https://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
forecast_data = fetch_api_data(forecast_url, "Forecast")
df_fore = build_dataframe(forecast_data, "Forecast") if forecast_data else pd.DataFrame()

# 📊 Combine and Plot
df_combined = pd.concat([df_hist, df_fore])
if df_combined.empty:
    print("⚠️ No AQI data found.")
    exit()

plt.figure(figsize=(15, 6))
for label, group in df_combined.groupby("source"):
    plt.plot(group["datetime"], group["aqi"], marker="o", label=label)

# 🎨 AQI bands
plt.axhspan(0.5, 1.5, color='green', alpha=0.2, label='Good')
plt.axhspan(1.5, 2.5, color='yellow', alpha=0.2, label='Fair')
plt.axhspan(2.5, 3.5, color='orange', alpha=0.2, label='Moderate')
plt.axhspan(3.5, 4.5, color='red', alpha=0.2, label='Poor')
plt.axhspan(4.5, 5.5, color='purple', alpha=0.2, label='Very Poor')

plt.title(f"AQI: Historical + Forecast ({city_name.title()})")
plt.xlabel("Datetime")
plt.ylabel("AQI Level (1=Good, 5=Very Poor)")
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.show()

# 🧠 Gemini Health Summary
avg_aqi = round(df_combined["aqi"].mean(), 1)
get_health_advice(avg_aqi, city_name)
