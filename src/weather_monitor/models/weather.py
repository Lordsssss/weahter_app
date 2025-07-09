from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class WeatherObservation(BaseModel):
    timestamp: datetime = Field(..., description="Observation timestamp")
    station_id: str = Field(..., description="Weather station ID")
    neighborhood: Optional[str] = Field(None, description="Neighborhood name")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, description="Humidity percentage")
    dewpoint: Optional[float] = Field(None, description="Dew point in Celsius")
    heat_index: Optional[float] = Field(None, description="Heat index in Celsius")
    wind_speed: Optional[float] = Field(None, description="Wind speed in km/h")
    wind_gust: Optional[float] = Field(None, description="Wind gust in km/h")
    wind_direction: Optional[int] = Field(None, description="Wind direction in degrees")
    pressure: Optional[float] = Field(None, description="Atmospheric pressure in hPa")
    uv_index: Optional[float] = Field(None, description="UV index")
    solar_radiation: Optional[float] = Field(None, description="Solar radiation")
    precipitation_rate: Optional[float] = Field(None, description="Precipitation rate in mm/h")
    precipitation_total: Optional[float] = Field(None, description="Total precipitation in mm")
    
    @classmethod
    def from_api_response(cls, data: dict) -> 'WeatherObservation':
        """Create WeatherObservation from API response"""
        obs = data.get('observations', [{}])[0]
        metric = obs.get('metric', {})
        
        # Use current UTC time instead of API's local time to avoid timezone issues
        current_time = datetime.now(timezone.utc)
        
        return cls(
            timestamp=current_time,
            station_id=obs.get('stationID', ''),
            neighborhood=obs.get('neighborhood'),
            temperature=metric.get('temp'),
            humidity=obs.get('humidity'),
            dewpoint=metric.get('dewpt'),
            heat_index=metric.get('heatIndex'),
            wind_speed=metric.get('windSpeed'),
            wind_gust=metric.get('windGust'),
            wind_direction=obs.get('winddir'),
            pressure=metric.get('pressure'),
            uv_index=obs.get('uv'),
            solar_radiation=obs.get('solarRadiation'),
            precipitation_rate=metric.get('precipRate'),
            precipitation_total=metric.get('precipTotal')
        )