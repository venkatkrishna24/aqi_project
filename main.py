import json
import folium
import requests
import time
from geopy.geocoders import Nominatim

# Load the JSON data from the uploaded file
with open("States and Districts.json", "r", encoding="utf-8") as f:
    states_data = json.load(f)

# ✅ Replace with your OpenWeatherMap API Key
API_KEY = "71b5019314b0f31dbdb2dab77af530ad"

# Extract all district names
districts = []
for state in states_data:
    for district in state["districts"]:
        districts.append(district["name"])

# Function to get coordinates
def get_coordinates(city):
    try:
        geolocator = Nominatim(user_agent="aqi_mapper")
        location = geolocator.geocode(city + ", India", timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None

# Function to get AQI from OpenWeatherMap
def get_aqi(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        res = requests.get(url)
        data = res.json()
        return data["list"][0]["main"]["aqi"]
    except:
        return None

# Function to assign color
def get_color(aqi):
    return {
        1: "green",
        2: "yellow",
        3: "orange",
        4: "red",
        5: "purple"
    }.get(aqi, "gray")

# Create the base map
geolocator = Nominatim(user_agent="aqi_mapper")
map_center = get_coordinates("India")
m = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB positron")

# Plot each district
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
        time.sleep(1)  # API rate limit protection

# Add legend
legend_html = """
<div style="position: fixed; 
     bottom: 30px; left: 30px; width: 150px; height: 140px; 
     border:2px solid grey; z-index:9999; font-size:14px; background-color:white; padding:10px;">
<b>AQI Legend</b><br>
<span style="background-color:green; width:10px; height:10px; display:inline-block;"></span> Good (1)<br>
<span style="background-color:yellow; width:10px; height:10px; display:inline-block;"></span> Fair (2)<br>
<span style="background-color:orange; width:10px; height:10px; display:inline-block;"></span> Moderate (3)<br>
<span style="background-color:red; width:10px; height:10px; display:inline-block;"></span> Poor (4)<br>
<span style="background-color:purple; width:10px; height:10px; display:inline-block;"></span> Very Poor (5)<br>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Save the map
map_path = "/mnt/data/aqi_heatmap_all_districts.html"
m.save(map_path)
map_path
