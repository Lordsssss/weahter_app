import requests
from typing import Optional, List, Dict, Any
from loguru import logger
import json

class OpenWeatherMapClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org"
        self.session = requests.Session()
        
    def get_current_weather_by_city(self, city: str, country_code: str = "CA") -> Optional[Dict[str, Any]]:
        """Get current weather for a city"""
        url = f"{self.base_url}/data/2.5/weather"
        params = {
            "q": f"{city},{country_code}",
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching weather for {city}: {e}")
            return None
    
    def get_current_weather_by_coords(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get current weather for coordinates"""
        url = f"{self.base_url}/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching weather for coords {lat},{lon}: {e}")
            return None
    
    def get_one_call_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get comprehensive weather data using One Call API"""
        url = f"{self.base_url}/data/3.0/onecall"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching One Call data for {lat},{lon}: {e}")
            return None
    
    def find_nearby_stations(self, lat: float, lon: float, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Find nearby weather stations"""
        url = f"{self.base_url}/data/2.5/find"
        params = {
            "lat": lat,
            "lon": lon,
            "cnt": limit,
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("list", [])
        except requests.RequestException as e:
            logger.error(f"Error finding nearby stations: {e}")
            return None
    
    def get_air_pollution(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get air pollution data"""
        url = f"{self.base_url}/data/2.5/air_pollution"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching air pollution data: {e}")
            return None
    
    def test_api_key(self) -> bool:
        """Test if the API key is valid"""
        try:
            # Test with Montreal coordinates
            result = self.get_current_weather_by_coords(45.5088, -73.5878)
            return result is not None
        except:
            return False
    
    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()