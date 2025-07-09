from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from loguru import logger
from typing import Optional

from ..config import settings
from ..models.weather import WeatherObservation, WeatherStation

class InfluxDBManager:
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.influxdb_url,
            token=settings.influxdb_token,
            org=settings.influxdb_org
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        
    def write_weather_data(self, observation: WeatherObservation) -> bool:
        """Write weather observation to InfluxDB"""
        try:
            point = Point("weather_data")
            point.tag("station_id", observation.station_id)
            
            if observation.neighborhood:
                point.tag("neighborhood", observation.neighborhood)
            if observation.city:
                point.tag("city", observation.city)
            if observation.latitude is not None:
                point.field("latitude", observation.latitude)
            if observation.longitude is not None:
                point.field("longitude", observation.longitude)
            
            # Add fields with null checks
            fields = {
                "temperature": observation.temperature,
                "humidity": observation.humidity,
                "dewpoint": observation.dewpoint,
                "heat_index": observation.heat_index,
                "wind_speed": observation.wind_speed,
                "wind_gust": observation.wind_gust,
                "wind_direction": observation.wind_direction,
                "pressure": observation.pressure,
                "uv_index": observation.uv_index,
                "solar_radiation": observation.solar_radiation,
                "precipitation_rate": observation.precipitation_rate,
                "precipitation_total": observation.precipitation_total
            }
            
            # Only add non-null fields
            for field_name, value in fields.items():
                if value is not None:
                    point.field(field_name, value)
            
            point.time(observation.timestamp)
            
            self.write_api.write(
                bucket=settings.influxdb_bucket,
                org=settings.influxdb_org,
                record=point
            )
            
            logger.info(f"Successfully wrote weather data for station {observation.station_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test InfluxDB connection"""
        try:
            self.client.ping()
            logger.info("InfluxDB connection successful")
            return True
        except Exception as e:
            logger.error(f"InfluxDB connection failed: {e}")
            return False
    
    def write_station_metadata(self, station: WeatherStation) -> bool:
        """Write weather station metadata to InfluxDB"""
        try:
            point = Point("weather_stations")
            point.tag("station_id", station.station_id)
            point.tag("city", station.city)
            point.field("name", station.name)
            point.field("latitude", station.latitude)
            point.field("longitude", station.longitude)
            point.field("active", station.active)
            
            self.write_api.write(
                bucket=settings.influxdb_bucket,
                org=settings.influxdb_org,
                record=point
            )
            
            logger.info(f"Successfully wrote station metadata for {station.station_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing station metadata to InfluxDB: {e}")
            return False
    
    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()