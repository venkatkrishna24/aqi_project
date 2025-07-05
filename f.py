from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import folium
import time
from datetime import datetime
from geopy.geocoders import Nominatim
import pandas as pd
import os

# -------------------- Config --------------------
API_KEY = os.getenv("OWM_API_KEY", "71b5019314b0f31dbdb2dab77af530ad")
HEATMAP_FILE = "aqi_heatmap.html"

# -------------------- FastAPI App Setup --------------------
app = FastAPI()

# Enable CORS for frontend & mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- AQI & Location Helpers --------------------
def get_coordinates(place):
    try:
        geolocator = Nominatim(user_agent="aqi_app")
        location = geolocator.geocode(place + ", India", timeout=10)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print("❌ Geolocation error:", e)
    return None

def get_aqi(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        return data["list"][0]["main"]["aqi"]
    except:
        return None

def get_color(aqi):
    return {
        1: "green", 2: "yellow", 3: "orange", 4: "red", 5: "purple"
    }.get(aqi, "gray")

def generate_heatmap():
    # Load districts from file
    with open("States and Districts.json", "r", encoding="utf-8") as f:
        states_data = json.load(f)

    districts = [d["name"] for s in states_data for d in s["districts"]]
    map_center = get_coordinates("India")
    m = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB positron")

    for district in districts:
        coords = get_coordinates(district)
        if coords:
            lat, lon = coords
            aqi = get_aqi(lat, lon)
            if aqi:
                color = get_color(aqi)
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=6,
                    popup=f"{district} — AQI: {aqi}",
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7
                ).add_to(m)
            time.sleep(1)  # avoid rate limits

    legend = """
    <div style="position: fixed; bottom: 30px; left: 30px; width: 150px;
    border:2px solid grey; background-color:white; padding:10px; z-index:9999;">
    <b>AQI Legend</b><br>
    <span style='background-color:green'>&nbsp;&nbsp;&nbsp;</span> Good (1)<br>
    <span style='background-color:yellow'>&nbsp;&nbsp;&nbsp;</span> Fair (2)<br>
    <span style='background-color:orange'>&nbsp;&nbsp;&nbsp;</span> Moderate (3)<br>
    <span style='background-color:red'>&nbsp;&nbsp;&nbsp;</span> Poor (4)<br>
    <span style='background-color:purple'>&nbsp;&nbsp;&nbsp;</span> Very Poor (5)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend))
    m.save(HEATMAP_FILE)

# -------------------- Routes --------------------
@app.get("/")
def root():
    return {"message": "AQI backend is running 🚀"}

@app.get("/heatmap")
def serve_heatmap():
    if not os.path.exists(HEATMAP_FILE):
        generate_heatmap()
    return FileResponse(HEATMAP_FILE, media_type="text/html")

@app.get("/aqi")
def get_aqi_json(city: str = Query(...)):
    coords = get_coordinates(city)
    if not coords:
        return JSONResponse(status_code=404, content={"error": "Location not found"})
    lat, lon = coords

    forecast_url = f"https://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={API_KEY}"
    current_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"

    try:
        forecast_data = requests.get(forecast_url).json().get("list", [])
        current_data = requests.get(current_url).json().get("list", [])

        combined = current_data + forecast_data
        df = pd.DataFrame([{
            "datetime": datetime.utcfromtimestamp(item["dt"]).isoformat(),
            "aqi": item["main"]["aqi"]
        } for item in combined])

        return {
            "city": city,
            "aqi_history": df.to_dict(orient="records")
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# -------------------- For Render --------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
