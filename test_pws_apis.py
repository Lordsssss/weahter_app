#!/usr/bin/env python3
"""
Test script for various free weather APIs and personal weather station networks
"""

import requests
import json
import sys
import os
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_environment_canada_api():
    """Test Environment Canada MSC GeoMet API"""
    print("🍁 Testing Environment Canada MSC GeoMet API")
    print("-" * 50)
    
    # Test basic API endpoint
    try:
        # Get weather stations near Montreal
        base_url = "https://api.weather.gc.ca"
        
        # Test API availability
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"✅ API accessible: {response.status_code}")
        
        # Try to get weather data for Montreal area
        # Note: This API uses OGC standards and might require specific parameters
        stations_url = f"{base_url}/collections/weather-stations/items"
        response = requests.get(stations_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Weather stations data retrieved")
            print(f"📊 Available features: {len(data.get('features', []))}")
            
            # Look for Montreal area stations
            montreal_stations = []
            for feature in data.get('features', [])[:10]:  # Check first 10
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                coords = geometry.get('coordinates', [])
                
                if coords and len(coords) >= 2:
                    lon, lat = coords[0], coords[1]
                    # Check if near Montreal (roughly)
                    if -74.5 <= lon <= -73.0 and 45.0 <= lat <= 46.0:
                        montreal_stations.append({
                            'name': properties.get('name', 'Unknown'),
                            'id': properties.get('id', 'Unknown'),
                            'latitude': lat,
                            'longitude': lon,
                            'province': properties.get('province', 'Unknown')
                        })
            
            print(f"🌡️  Found {len(montreal_stations)} stations near Montreal")
            for station in montreal_stations[:5]:
                print(f"  📍 {station['name']} (ID: {station['id']})")
                print(f"     {station['latitude']:.4f}, {station['longitude']:.4f}")
            
        else:
            print(f"❌ Error accessing stations: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Environment Canada API error: {e}")
    
    print()

def test_cwop_network():
    """Test access to CWOP network data"""
    print("🌐 Testing CWOP (Citizen Weather Observer Program) Network")
    print("-" * 50)
    
    # CWOP data is available through various sources
    # Let's try to find Quebec/Montreal CWOP stations
    
    try:
        # Try accessing CWOP data through MesoWest or similar services
        # Note: Direct CWOP access might require specific protocols
        
        # Alternative: Check if we can find CWOP stations in Montreal area
        # CWOP station IDs typically start with specific prefixes for different regions
        
        # Canadian CWOP stations often have specific ID patterns
        potential_montreal_cwop = [
            'CW1234',  # Example format
            'VE2ABC',  # Amateur radio format
            'FW1234',  # Another format
        ]
        
        print("🔍 CWOP network requires specific station IDs")
        print("📋 For Montreal area, you would need to:")
        print("   1. Register your personal weather station with CWOP")
        print("   2. Get assigned a station ID")
        print("   3. Use APRS or similar protocol to transmit data")
        print("   4. Access data through MesoWest or similar aggregators")
        
    except Exception as e:
        print(f"❌ CWOP network error: {e}")
    
    print()

def test_weatherapi_com():
    """Test WeatherAPI.com for free tier"""
    print("🌤️  Testing WeatherAPI.com (Free Tier)")
    print("-" * 50)
    
    # WeatherAPI.com offers free tier with limited calls
    # You would need to sign up for a free API key
    
    print("📝 WeatherAPI.com Free Tier:")
    print("   - 1,000,000 calls per month")
    print("   - Current weather")
    print("   - 3-day forecast")
    print("   - Historical data (7 days)")
    print("   - Search/autocomplete")
    print("   ⚠️  Requires free registration for API key")
    
    print()

def test_ambient_weather_network():
    """Test Ambient Weather Network access"""
    print("🏠 Testing Ambient Weather Network")
    print("-" * 50)
    
    # Ambient Weather provides API access for device owners
    print("🔑 Ambient Weather Network:")
    print("   - Free API access for Ambient Weather device owners")
    print("   - Real-time data from your own stations")
    print("   - Historical data from your devices")
    print("   - Requires Ambient Weather station purchase")
    print("   - Station data also feeds into Weather Underground")
    
    print()

def discover_montreal_area_alternatives():
    """Look for alternative data sources for Montreal area"""
    print("🔍 Alternative Weather Data Sources for Montreal")
    print("-" * 50)
    
    alternatives = [
        {
            "name": "PWSWeather.com",
            "access": "Free for contributors",
            "description": "Network of personal weather stations",
            "api": "Available for data contributors",
            "coverage": "Global, including Montreal area"
        },
        {
            "name": "Weatherflow Tempest",
            "access": "Free for device owners",
            "description": "Smart weather station network",
            "api": "REST API for device owners",
            "coverage": "Growing network, some Montreal area coverage"
        },
        {
            "name": "Davis WeatherLink",
            "access": "Free for device owners",
            "description": "Davis Instruments weather station network",
            "api": "WeatherLink API for device owners",
            "coverage": "Large network, good Montreal coverage"
        },
        {
            "name": "Netatmo Weather Map",
            "access": "Limited free access",
            "description": "Netatmo personal weather station network",
            "api": "API available with restrictions",
            "coverage": "Dense urban coverage including Montreal"
        },
        {
            "name": "OpenSenseMap",
            "access": "Free and open",
            "description": "Open source environmental sensor network",
            "api": "Open API",
            "coverage": "Growing network, some Canadian coverage"
        }
    ]
    
    for alt in alternatives:
        print(f"📊 {alt['name']}")
        print(f"   🔑 Access: {alt['access']}")
        print(f"   📝 Description: {alt['description']}")
        print(f"   🌐 API: {alt['api']}")
        print(f"   📍 Coverage: {alt['coverage']}")
        print()

def main():
    print("🌡️  Personal Weather Station API Discovery")
    print("=" * 60)
    print("Testing free APIs for personal weather station networks")
    print("Focus: Greater Montreal area, Quebec, Canada")
    print("=" * 60)
    print()
    
    # Test various APIs
    test_environment_canada_api()
    test_cwop_network()
    test_weatherapi_com()
    test_ambient_weather_network()
    discover_montreal_area_alternatives()
    
    print("=" * 60)
    print("📋 RECOMMENDATIONS")
    print("=" * 60)
    
    print("🥇 Best options for Montreal area PWS data:")
    print()
    print("1. 🍁 Environment Canada MSC GeoMet API")
    print("   - Completely free")
    print("   - Official government data")
    print("   - Good coverage of Quebec")
    print("   - Reliable and well-maintained")
    print()
    
    print("2. 🌐 WeatherAPI.com (Free Tier)")
    print("   - 1M calls/month free")
    print("   - Good Montreal coverage")
    print("   - Easy to integrate")
    print("   - Requires registration")
    print()
    
    print("3. 🏠 Netatmo Weather Map")
    print("   - Dense urban coverage")
    print("   - Personal weather stations")
    print("   - Free access with limitations")
    print("   - Good for hyperlocal data")
    print()
    
    print("4. 📡 Weather Underground PWS")
    print("   - Requires owning a weather station")
    print("   - Access to contributed data")
    print("   - Best granular coverage")
    print("   - No longer free for general public")
    print()
    
    print("💡 Next steps:")
    print("1. Test Environment Canada API for official stations")
    print("2. Register for WeatherAPI.com free tier")
    print("3. Explore Netatmo Weather Map API")
    print("4. Consider purchasing personal weather station for WU access")

if __name__ == "__main__":
    main()