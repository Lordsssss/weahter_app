import time
import signal
import sys
from datetime import datetime
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
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
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