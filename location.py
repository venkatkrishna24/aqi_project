import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
from geopy.geocoders import Nominatim
import google.generativeai as genai

# -------------------- CONFIG --------------------
OWM_API_KEY = "71b5019314b0f31dbdb2dab77af530ad"  # Replace with your OpenWeather key
GEMINI_API_KEY = "AIzaSyDsleB6zDYnNyLGRMzzwOt3lRkHzCODjgk"   # Replace with your Gemini API key
genai.configure(api_key=GEMINI_API_KEY)

gemini_model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# -------------------- Location Functions --------------------
def get_current_location_coords():
    try:
        response = requests.get("https://ipinfo.io/json")
        response.raise_for_status()
        data = response.json()
        loc = data.get("loc")
        if loc:
            lat_str, lon_str = loc.split(",")
            return float(lat_str), float(lon_str), data.get("city", "Unknown")
        else:
            return None
    except Exception as e:
        print("❌ Error detecting location via IP:", e)
        return None

def get_coordinates(place):
    try:
        geolocator = Nominatim(user_agent="aqi_app")
        location = geolocator.geocode(place)
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except Exception as e:
        print("❌ Error fetching coordinates:", e)
        return None

# -------------------- Data Fetch --------------------
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

# -------------------- Gemini Advice --------------------
def generate_health_advice(location, aqi_val):
    prompt = (
        f"Provide a short health alert for AQI value {aqi_val} in {location}. "
        f"Include risk level and precautions in one sentence."
    )
    try:
        response = gemini_model.generate_content(prompt)
        print("\n🧠 Gemini Health Alert:\n")
        print(response.text)
    except Exception as e:
        print("⚠️ Gemini Error:", e)
        print(f"🧠 Basic Advice: AQI {aqi_val} in {location} — reduce outdoor activity if sensitive.\n")

# -------------------- Main --------------------
if __name__ == "__main__":
    use_auto_location = input("Use your current location? (y/n): ").strip().lower() == 'y'

    if use_auto_location:
        result = get_current_location_coords()
        if not result:
            print("❌ Failed to get your current location via IP.")
            exit()
        lat, lon, place = result
        print(f"📍 Detected location: {place} (Lat: {lat}, Lon: {lon})")
    else:
        place = input("Enter location name: ").strip()
        coords = get_coordinates(place)
        if not coords:
            print("❌ Could not fetch location data.")
            exit()
        lat, lon = coords

    END = int(time.time())
    START = END - (5 * 24 * 60 * 60)  # last 5 days

    history_url = (
        f"https://api.openweathermap.org/data/2.5/air_pollution/history"
        f"?lat={lat}&lon={lon}&start={START}&end={END}&appid={OWM_API_KEY}"
    )
    forecast_url = (
        f"https://api.openweathermap.org/data/2.5/air_pollution/forecast"
        f"?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
    )
    current_url = (
        f"https://api.openweathermap.org/data/2.5/air_pollution"
        f"?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
    )

    history_data = fetch_api_data(history_url, "Historical")
    forecast_data = fetch_api_data(forecast_url, "Forecast")
    current_data = fetch_api_data(current_url, "Current")

    df_hist = build_dataframe(history_data, "Historical") if history_data else pd.DataFrame()
    df_fore = build_dataframe(forecast_data, "Forecast") if forecast_data else pd.DataFrame()
    df_current = build_dataframe(current_data, "Current") if current_data else pd.DataFrame()

    df_combined = pd.concat([df_hist, df_fore, df_current])

    if df_combined.empty:
        print("⚠️ No AQI data available. Check API key or internet connection.")
        exit()

    # Print real-time AQI
    if not df_current.empty:
        latest_current = df_current.iloc[-1]
        print(f"\n📡 Real-Time AQI in {place.title()} ({latest_current['datetime']} UTC): {latest_current['aqi']}")

    # -------------------- Plot --------------------
    plt.figure(figsize=(14, 6))
    for label, group in df_combined.groupby("source"):
        plt.plot(group["datetime"], group["aqi"], marker="o", label=label)

    plt.axhspan(0.5, 1.5, color='green', alpha=0.2, label='Good')
    plt.axhspan(1.5, 2.5, color='yellow', alpha=0.2, label='Fair')
    plt.axhspan(2.5, 3.5, color='orange', alpha=0.2, label='Moderate')
    plt.axhspan(3.5, 4.5, color='red', alpha=0.2, label='Poor')
    plt.axhspan(4.5, 5.5, color='purple', alpha=0.2, label='Very Poor')

    plt.title(f"AQI: Historical + Forecast + Real-Time ({place.title()})")
    plt.xlabel("Datetime")
    plt.ylabel("AQI Level (1=Good, 5=Very Poor)")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # 🧠 Generate Health Tip
    latest_aqi = latest_current["aqi"] if not df_current.empty else df_combined.iloc[-1]["aqi"]
    generate_health_advice(place, latest_aqi)
