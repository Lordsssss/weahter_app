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
    
    # Database Configuration
    database_type: str = os.getenv("DATABASE_TYPE", "sqlite")
    sqlite_db_path: str = os.getenv("SQLITE_DB_PATH", "/app/data/weather_data.db")
    
    # Data retention settings
    data_retention_days: int = int(os.getenv("DATA_RETENTION_DAYS", "30"))
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/weather_monitor.log")
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields

settings = Settings()