import time
import signal
import sys
from loguru import logger

from .api.weather_client import WeatherAPIClient
from .database.influxdb import InfluxDBManager
from .config import settings

class WeatherMonitor:
    def __init__(self):
        self.weather_client = WeatherAPIClient()
        self.db_manager = InfluxDBManager()
        self.running = True
        
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
        
        while self.running:
            try:
                # Fetch weather data
                observation = self.weather_client.fetch_current_weather()
                
                if observation:
                    # Write to database
                    success = self.db_manager.write_weather_data(observation)
                    
                    if success:
                        logger.info(f"Weather data logged: {observation.temperature}°C, {observation.humidity}% humidity")
                    else:
                        logger.warning("Failed to write weather data to database")
                else:
                    logger.warning("Failed to fetch weather data")
                
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