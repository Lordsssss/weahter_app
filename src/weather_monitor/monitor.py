import time
import signal
import sys
import os
from datetime import datetime
from pathlib import Path
from loguru import logger

from .api.weather_client import WeatherAPIClient
from .database.database_factory import get_database_manager
from .config import settings
from .station_manager import StationManager

class WeatherMonitor:
    def __init__(self):
        self.weather_client = WeatherAPIClient()
        self.db_manager = get_database_manager()
        self.station_manager = StationManager()
        self.running = True
        self.last_cleanup = datetime.now()
        self.config_reload_requested = False
        
        # Track config file modification time
        self.config_file_path = Path(__file__).parent.parent.parent / "config" / "weather_stations.json"
        self.last_config_mtime = self._get_config_mtime()
        
        # Set up signal handlers for graceful shutdown and config reload
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGUSR1, self._config_reload_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def _config_reload_handler(self, signum, frame):
        """Handle config reload signal"""
        logger.info(f"Received config reload signal {signum}")
        self.config_reload_requested = True
        
    def _get_config_mtime(self):
        """Get config file modification time"""
        try:
            if self.config_file_path.exists():
                return self.config_file_path.stat().st_mtime
        except Exception as e:
            logger.warning(f"Could not get config file mtime: {e}")
        return 0
        
    def _check_config_file_changes(self):
        """Check if config file has been modified"""
        current_mtime = self._get_config_mtime()
        if current_mtime > self.last_config_mtime:
            logger.info("Config file modification detected")
            self.last_config_mtime = current_mtime
            self.config_reload_requested = True
        
    def start_monitoring(self):
        """Start the weather monitoring loop"""
        logger.info("Starting weather monitoring service...")
        
        # Test database connection
        if not self.db_manager.test_connection():
            logger.error("Database connection failed. Exiting.")
            sys.exit(1)
        
        logger.info(f"Monitoring weather data every {settings.weather_fetch_interval} seconds")
        
        # Get all active stations
        active_stations = self.station_manager.get_active_stations()
        logger.info(f"Monitoring {len(active_stations)} weather stations")
        
        while self.running:
            try:
                # Check for config file changes
                self._check_config_file_changes()
                
                # Check for config reload request
                if self.config_reload_requested:
                    self._reload_configuration()
                    active_stations = self.station_manager.get_active_stations()
                    logger.info(f"Configuration reloaded, now monitoring {len(active_stations)} weather stations")
                    self.config_reload_requested = False
                
                # Fetch weather data from all stations
                for station in active_stations:
                    try:
                        observation = self.weather_client.fetch_current_weather(station_id=station.station_id)
                        
                        if observation:
                            # Add station location info
                            observation.city = station.city
                            observation.latitude = station.latitude
                            observation.longitude = station.longitude
                            
                            # Write to database
                            success = self.db_manager.write_weather_data(observation)
                            
                            if success:
                                logger.info(f"Weather data logged for {station.name}: {observation.temperature}°C, {observation.humidity}% humidity")
                            else:
                                logger.warning(f"Failed to write weather data for {station.name}")
                        else:
                            logger.warning(f"Failed to fetch weather data for {station.name}")
                    except Exception as e:
                        logger.error(f"Error fetching data for station {station.name}: {e}")
                        continue
                
                # Daily cleanup (run once per day)
                if (datetime.now() - self.last_cleanup).days >= 1:
                    logger.info("Running daily database cleanup...")
                    self.db_manager.cleanup_old_data(settings.data_retention_days)
                    self.last_cleanup = datetime.now()
                
                # Sleep until next fetch
                time.sleep(settings.weather_fetch_interval)
                
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                time.sleep(settings.weather_fetch_interval)
        
        self._cleanup()
        
    def _reload_configuration(self):
        """Reload station configuration"""
        try:
            logger.info("Reloading station configuration...")
            success = self.station_manager.load_stations()
            if success:
                # Sync new stations to database
                self.station_manager.sync_to_database()
                logger.info("Station configuration reloaded successfully")
            else:
                logger.error("Failed to reload station configuration")
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
    
    def _cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        self.weather_client.close()
        self.db_manager.close()
        logger.info("Weather monitoring service stopped")

def main():
    """Main entry point"""
    monitor = WeatherMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main()