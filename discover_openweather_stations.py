#!/usr/bin/env python3
"""
Discover OpenWeatherMap stations and weather data points in Greater Montreal area
"""

import json
import sys
import os
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from weather_monitor.api.openweather_client import OpenWeatherMapClient

def main():
    # Your OpenWeatherMap API key
    api_key = "10a631d20fa3bdb7392901bb1024ced4"
    
    client = OpenWeatherMapClient(api_key)
    
    print("🌡️  OpenWeatherMap API Station Discovery")
    print("=" * 50)
    
    # Test API key first
    print("Testing API key...")
    if not client.test_api_key():
        print("❌ API key test failed!")
        return
    print("✅ API key is valid")
    print()
    
    # Define key locations in Greater Montreal area
    locations = [
        {"name": "Montreal", "lat": 45.5088, "lon": -73.5878},
        {"name": "Laval", "lat": 45.5586, "lon": -73.7567},
        {"name": "Longueuil", "lat": 45.5301, "lon": -73.4781},
        {"name": "Saint-Eustache", "lat": 45.5653, "lon": -73.9057},
        {"name": "Verdun", "lat": 45.4683, "lon": -73.5709},
        {"name": "Pierrefonds", "lat": 45.4978, "lon": -73.8369},
        {"name": "Boisbriand", "lat": 45.6014, "lon": -73.8369},
        {"name": "Delson", "lat": 45.3745, "lon": -73.5388},
        {"name": "Saint-Constant", "lat": 45.3667, "lon": -73.5667},
        {"name": "Deux-Montagnes", "lat": 45.5339, "lon": -73.8997},
    ]
    
    print("🔍 Discovering weather data for key locations:")
    print("-" * 50)
    
    all_stations = []
    
    for location in locations:
        print(f"\n📍 {location['name']} ({location['lat']}, {location['lon']})")
        
        # Get current weather
        current = client.get_current_weather_by_coords(location['lat'], location['lon'])
        if current:
            station_info = {
                "name": location['name'],
                "type": "OpenWeatherMap_City",
                "station_id": f"OWM_{current['id']}",
                "city": current.get('name', location['name']),
                "country": current.get('sys', {}).get('country', 'CA'),
                "latitude": current['coord']['lat'],
                "longitude": current['coord']['lon'],
                "current_weather": {
                    "temperature": current['main']['temp'],
                    "humidity": current['main']['humidity'],
                    "pressure": current['main']['pressure'],
                    "description": current['weather'][0]['description'],
                    "wind_speed": current.get('wind', {}).get('speed', 0)
                }
            }
            all_stations.append(station_info)
            
            print(f"  ✅ Station ID: {station_info['station_id']}")
            print(f"  🌡️  Current: {current['main']['temp']}°C, {current['weather'][0]['description']}")
            print(f"  💨 Wind: {current.get('wind', {}).get('speed', 0)} m/s")
            print(f"  💧 Humidity: {current['main']['humidity']}%")
        
        # Find nearby stations
        nearby = client.find_nearby_stations(location['lat'], location['lon'], 5)
        if nearby:
            print(f"  📡 Found {len(nearby)} nearby stations:")
            for i, station in enumerate(nearby[:3]):  # Show first 3
                print(f"    {i+1}. {station.get('name', 'Unknown')} (ID: {station.get('id', 'N/A')})")
                print(f"       📍 {station['coord']['lat']:.4f}, {station['coord']['lon']:.4f}")
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    print(f"Total locations discovered: {len(all_stations)}")
    print("\nAvailable station types:")
    print("1. 🏙️  City-based queries (by name or coordinates)")
    print("2. 🌐 One Call API (comprehensive weather data)")
    print("3. 🔍 Nearby station discovery")
    print("4. 🌫️  Air pollution data")
    
    print("\nOpenWeatherMap API Capabilities:")
    print("- Current weather conditions")
    print("- Hourly forecasts (48 hours)")
    print("- Daily forecasts (7 days)")
    print("- Historical weather data")
    print("- Air quality index")
    print("- Weather alerts")
    
    print("\n📋 Recommended approach for Greater Montreal:")
    print("1. Use coordinates-based queries for specific locations")
    print("2. City names work well for major areas")
    print("3. One Call API provides the most comprehensive data")
    print("4. Higher precision than Weather.com API in urban areas")
    
    # Test One Call API for Montreal
    print("\n🚀 Testing One Call API for Montreal...")
    one_call = client.get_one_call_weather(45.5088, -73.5878)
    if one_call:
        current = one_call.get('current', {})
        print(f"✅ One Call API successful!")
        print(f"   🌡️  Temperature: {current.get('temp', 'N/A')}°C")
        print(f"   🌤️  Weather: {current.get('weather', [{}])[0].get('description', 'N/A')}")
        print(f"   👁️  Visibility: {current.get('visibility', 'N/A')} meters")
        print(f"   ☁️  Clouds: {current.get('clouds', 'N/A')}%")
        print(f"   📊 Hourly forecasts: {len(one_call.get('hourly', []))} hours")
        print(f"   📅 Daily forecasts: {len(one_call.get('daily', []))} days")
    
    # Save stations to file
    output_file = "/opt/weather-app/weahter_app/config/openweather_stations.json"
    with open(output_file, 'w') as f:
        json.dump({"stations": all_stations}, f, indent=2)
    
    print(f"\n💾 Station data saved to: {output_file}")
    
    client.close()

if __name__ == "__main__":
    main()