import folium
import requests
from geopy.geocoders import Nominatim
from folium.plugins import FloatImage
import time

# ✅ Replace with your OpenWeatherMap API Key
API_KEY = "71b5019314b0f31dbdb2dab77af530ad"

# 🏙️ Deduplicated List of Major Indian Cities
cities = list(set([
    "Chennai", "Delhi", "Mumbai", "Kolkata", "Hyderabad", "Bangalore", "Ahmedabad", "Kerala", "Pune", "Jaipur",
    "Lucknow", "Kanpur", "Nagpur", "Visakhapatnam", "Surat", "Bhopal", "Patna", "Vadodara", "Ghaziabad", "Indore",
    "Coimbatore", "Agra", "Madurai", "Nashik", "Faridabad", "Meerut", "Rajkot", "Kalyan", "Vasai", "Varanasi",
    "Srinagar", "Aurangabad", "Dhanbad", "Amritsar", "Prayagraj", "Ranchi", "Howrah", "Jabalpur", "Gwalior", "Vijayawada",
    "Jodhpur", "Raipur", "Kota", "Chandigarh", "Thane", "Solapur", "Bareilly", "Moradabad", "Mysore", "Gurgaon",
    "Aligarh", "Jalandhar", "Bhubaneswar", "Salem", "Warangal", "Jammu", "Thiruvananthapuram", "Bikaner", "Saharanpur",
    "Guntur", "Amravati", "Noida", "Jamshedpur", "Bhilai", "Cuttack", "Firozabad", "Kochi", "Bhavnagar", "Dehradun",
    "Durgapur", "Asansol", "Nanded", "Ajmer", "Ujjain", "Sagar", "Rourkela", "Kolhapur", "Erode", "Tirunelveli", "Tiruppur",
    "Kumbakonam", "Thanjavur", "Hosur", "Nagercoil", "Puducherry", "Kozhikode", "Tirupati", "Anantapur", "Kadapa", "Karimnagar",
    "Khammam", "Mahbubnagar", "Nizamabad", "Sangli", "Kanchipuram", "Suryapet", "Siddipet", "Jangaon", "Medchal",
]))

# 🌍 Get coordinates using geopy
def get_coordinates(city):
    try:
        geolocator = Nominatim(user_agent="aqi_mapper")
        location = geolocator.geocode(city)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None

# 📊 Get AQI from OpenWeather API
def get_aqi(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        res = requests.get(url)
        data = res.json()
        return data["list"][0]["main"]["aqi"]
    except:
        return None

# 🎯 AQI Color Scale
def get_color(aqi):
    return {
        1: "green",    # Good
        2: "yellow",   # Fair
        3: "orange",   # Moderate
        4: "red",      # Poor
        5: "purple"    # Very Poor
    }.get(aqi, "gray")

# 🗺️ Center map on India
map_center = get_coordinates("India")
m = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB positron")

# 📍 Add each city marker
for city in cities:
    coords = get_coordinates(city)
    if coords:
        lat, lon = coords
        aqi = get_aqi(lat, lon)
        if aqi:
            color = get_color(aqi)
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=f"{city} — AQI: {aqi}",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7
            ).add_to(m)
        time.sleep(1)  # ⏱ To avoid hitting API rate limits

# 🎨 Add legend (HTML inline)
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

# 💾 Save map
m.save("aqi_heatmap.html")
print("✅ AQI Heatmap saved as aqi_heatmap.html")
