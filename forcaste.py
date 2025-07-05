import requests
import json

# ✅ Correct GitHub RAW link
url = "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/countries/india.json"

response = requests.get(url)

try:
    data = response.json()
except json.JSONDecodeError as e:
    print("JSON Decode Error:", e)
    print("Raw response:\n", response.text[:200])
    exit()

# Extract all unique cities (districts)
districts = set()
for state in data['states']:
    for city in state.get('cities', []):
        districts.add(city['name'])

# Print results
print(f"Total Districts/Cities: {len(districts)}")
for district in sorted(districts):
    print(district)
