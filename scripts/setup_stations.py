#!/usr/bin/env python3
"""
Script to set up weather stations in the database
"""

import json
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from weather_monitor.models.weather import WeatherStation
from weather_monitor.database.influxdb import InfluxDBManager
from loguru import logger


def setup_weather_stations():
    """Load weather stations from config and write to database"""
    
    # Load station configuration
    config_path = Path(__file__).parent.parent / "config" / "weather_stations.json"
    
    if not config_path.exists():
        logger.error(f"Station configuration file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Initialize database connection
        db_manager = InfluxDBManager()
        
        # Test connection
        if not db_manager.test_connection():
            logger.error("Failed to connect to InfluxDB")
            return False
        
        # Process each station
        stations_added = 0
        for station_data in config.get("stations", []):
            try:
                station = WeatherStation(**station_data)
                
                if db_manager.write_station_metadata(station):
                    stations_added += 1
                    logger.info(f"Added station: {station.name} ({station.station_id})")
                else:
                    logger.warning(f"Failed to add station: {station.name}")
                    
            except Exception as e:
                logger.error(f"Error processing station {station_data}: {e}")
        
        logger.info(f"Successfully added {stations_added} weather stations")
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"Error setting up weather stations: {e}")
        return False


if __name__ == "__main__":
    if setup_weather_stations():
        logger.success("Weather stations setup completed successfully")
        sys.exit(0)
    else:
        logger.error("Weather stations setup failed")
        sys.exit(1)