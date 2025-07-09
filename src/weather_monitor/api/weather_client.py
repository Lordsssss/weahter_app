import requests
from typing import Optional
from loguru import logger

from ..config import settings
from ..models.weather import WeatherObservation

class WeatherAPIClient:
    def __init__(self):
        self.api_key = settings.weather_api_key
        self.station_id = settings.weather_station_id
        self.api_url = settings.weather_api_url
        self.session = requests.Session()
        
    def fetch_current_weather(self) -> Optional[WeatherObservation]:
        """Fetch current weather data from API"""
        params = {
            "apiKey": self.api_key,
            "stationId": self.station_id,
            "numericPrecision": "decimal",
            "format": "json",
            "units": "m"
        }
        
        try:
            response = self.session.get(
                self.api_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            observation = WeatherObservation.from_api_response(data)
            
            logger.info(f"Successfully fetched weather data for station {self.station_id}")
            return observation
            
        except requests.RequestException as e:
            logger.error(f"HTTP error fetching weather data: {e}")
            return None
        except ValueError as e:
            logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather data: {e}")
            return None
    
    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()