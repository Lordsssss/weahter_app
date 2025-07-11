"""
Weather Station Manager for handling multiple weather stations
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from .models.weather import WeatherStation
from .database.database_factory import get_database_manager


class StationManager:
    """Manager for weather station configuration and metadata"""
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "weather_stations.json"
        
        self.config_path = config_path
        self.stations: Dict[str, WeatherStation] = {}
        self.cities: Dict[str, List[str]] = {}  # city -> list of station_ids
        
        self.load_stations()
    
    def load_stations(self) -> bool:
        """Load weather stations from configuration file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Station configuration file not found: {self.config_path}")
                return False
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            self.stations.clear()
            self.cities.clear()
            
            for station_data in config.get("stations", []):
                station = WeatherStation(**station_data)
                self.stations[station.station_id] = station
                
                # Group by city
                if station.city not in self.cities:
                    self.cities[station.city] = []
                self.cities[station.city].append(station.station_id)
            
            logger.info(f"Loaded {len(self.stations)} weather stations from {len(self.cities)} cities")
            return True
            
        except Exception as e:
            logger.error(f"Error loading station configuration: {e}")
            return False
    
    def get_station(self, station_id: str) -> Optional[WeatherStation]:
        """Get station by ID"""
        return self.stations.get(station_id)
    
    def get_stations_by_city(self, city: str) -> List[WeatherStation]:
        """Get all stations in a city"""
        station_ids = self.cities.get(city, [])
        return [self.stations[sid] for sid in station_ids if sid in self.stations]
    
    def get_active_stations(self) -> List[WeatherStation]:
        """Get all active stations"""
        return [station for station in self.stations.values() if station.active]
    
    def get_cities(self) -> List[str]:
        """Get list of all cities"""
        return list(self.cities.keys())
    
    def get_station_ids(self) -> List[str]:
        """Get list of all station IDs"""
        return list(self.stations.keys())
    
    def sync_to_database(self) -> bool:
        """Sync station metadata to database"""
        try:
            db_manager = get_database_manager()
            
            if not db_manager.test_connection():
                logger.error("Failed to connect to database")
                return False
            
            synced_count = 0
            for station in self.stations.values():
                if db_manager.write_station_metadata(station):
                    synced_count += 1
                else:
                    logger.warning(f"Failed to sync station: {station.name}")
            
            logger.info(f"Synced {synced_count} stations to database")
            db_manager.close()
            return True
            
        except Exception as e:
            logger.error(f"Error syncing stations to database: {e}")
            return False
    
    def add_station(self, station: WeatherStation) -> bool:
        """Add a new station"""
        try:
            self.stations[station.station_id] = station
            
            # Update city mapping
            if station.city not in self.cities:
                self.cities[station.city] = []
            if station.station_id not in self.cities[station.city]:
                self.cities[station.city].append(station.station_id)
            
            logger.info(f"Added station: {station.name} ({station.station_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding station: {e}")
            return False
    
    def remove_station(self, station_id: str) -> bool:
        """Remove a station"""
        try:
            if station_id not in self.stations:
                logger.warning(f"Station {station_id} not found")
                return False
            
            station = self.stations[station_id]
            
            # Remove from city mapping
            if station.city in self.cities and station_id in self.cities[station.city]:
                self.cities[station.city].remove(station_id)
                if not self.cities[station.city]:  # Empty city list
                    del self.cities[station.city]
            
            del self.stations[station_id]
            logger.info(f"Removed station: {station.name} ({station_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error removing station: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save current station configuration to file"""
        try:
            config = {
                "stations": [station.dict() for station in self.stations.values()]
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved station configuration to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving station configuration: {e}")
            return False