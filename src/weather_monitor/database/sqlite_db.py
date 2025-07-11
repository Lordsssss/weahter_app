import sqlite3
import aiosqlite
from datetime import datetime
from loguru import logger
from typing import Optional, List
import json

from ..models.weather import WeatherObservation, WeatherStation

class SQLiteManager:
    def __init__(self, db_path: str = "weather_data.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Weather observations table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS weather_observations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        station_id TEXT NOT NULL,
                        neighborhood TEXT,
                        city TEXT,
                        latitude REAL,
                        longitude REAL,
                        temperature REAL,
                        humidity REAL,
                        dewpoint REAL,
                        heat_index REAL,
                        wind_speed REAL,
                        wind_gust REAL,
                        wind_direction REAL,
                        pressure REAL,
                        uv_index REAL,
                        solar_radiation REAL,
                        precipitation_rate REAL,
                        precipitation_total REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Weather stations metadata table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS weather_stations (
                        station_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        city TEXT NOT NULL,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        active BOOLEAN DEFAULT TRUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better query performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON weather_observations(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_station_id ON weather_observations(station_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_station_timestamp ON weather_observations(station_id, timestamp)")
                
                conn.commit()
                logger.info("SQLite database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing SQLite database: {e}")
            raise
    
    def write_weather_data(self, observation: WeatherObservation) -> bool:
        """Write weather observation to SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO weather_observations 
                    (timestamp, station_id, neighborhood, city, latitude, longitude,
                     temperature, humidity, dewpoint, heat_index, wind_speed, wind_gust,
                     wind_direction, pressure, uv_index, solar_radiation, 
                     precipitation_rate, precipitation_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    observation.timestamp,
                    observation.station_id,
                    observation.neighborhood,
                    observation.city,
                    observation.latitude,
                    observation.longitude,
                    observation.temperature,
                    observation.humidity,
                    observation.dewpoint,
                    observation.heat_index,
                    observation.wind_speed,
                    observation.wind_gust,
                    observation.wind_direction,
                    observation.pressure,
                    observation.uv_index,
                    observation.solar_radiation,
                    observation.precipitation_rate,
                    observation.precipitation_total
                ))
                conn.commit()
                
            logger.info(f"Successfully wrote weather data for station {observation.station_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing to SQLite: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test SQLite connection"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT 1")
                logger.info("SQLite connection successful")
                return True
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            return False
    
    def write_station_metadata(self, station: WeatherStation) -> bool:
        """Write weather station metadata to SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO weather_stations 
                    (station_id, name, city, latitude, longitude, active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    station.station_id,
                    station.name,
                    station.city,
                    station.latitude,
                    station.longitude,
                    station.active
                ))
                conn.commit()
                
            logger.info(f"Successfully wrote station metadata for {station.station_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing station metadata to SQLite: {e}")
            return False
    
    def get_latest_observations(self, station_id: Optional[str] = None, limit: int = 100) -> List[dict]:
        """Get latest weather observations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if station_id:
                    cursor = conn.execute("""
                        SELECT * FROM weather_observations 
                        WHERE station_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (station_id, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM weather_observations 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error querying SQLite: {e}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """Remove old data to keep database size manageable"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM weather_observations 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                deleted_rows = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_rows} old weather observations")
                return True
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False
    
    def get_database_stats(self) -> dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get row counts
                observations_count = conn.execute("SELECT COUNT(*) FROM weather_observations").fetchone()[0]
                stations_count = conn.execute("SELECT COUNT(*) FROM weather_stations").fetchone()[0]
                
                # Get database size
                db_size = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()").fetchone()[0]
                
                # Get date range
                date_range = conn.execute("""
                    SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest 
                    FROM weather_observations
                """).fetchone()
                
                return {
                    "observations_count": observations_count,
                    "stations_count": stations_count,
                    "database_size_bytes": db_size,
                    "database_size_mb": round(db_size / 1024 / 1024, 2),
                    "earliest_observation": date_range[0],
                    "latest_observation": date_range[1]
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def close(self):
        """Close database connection - no-op for SQLite"""
        pass