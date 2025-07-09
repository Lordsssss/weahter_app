import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Weather API Configuration
    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
    weather_station_id: str = os.getenv("WEATHER_STATION_ID", "")
    weather_api_url: str = os.getenv("WEATHER_API_URL", "https://api.weather.com/v2/pws/observations/current")
    weather_fetch_interval: int = int(os.getenv("WEATHER_FETCH_INTERVAL", "20"))
    
    # InfluxDB Configuration
    influxdb_url: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    influxdb_token: str = os.getenv("INFLUXDB_TOKEN", "")
    influxdb_org: str = os.getenv("INFLUXDB_ORG", "weather-monitoring")
    influxdb_bucket: str = os.getenv("INFLUXDB_BUCKET", "weather-data")
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/weather_monitor.log")
    
    class Config:
        env_file = ".env"

settings = Settings()