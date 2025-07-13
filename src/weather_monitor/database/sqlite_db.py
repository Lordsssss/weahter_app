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
                # Optimize SQLite for low memory usage
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL") 
                conn.execute("PRAGMA cache_size=2000")  # Reduce cache size
                conn.execute("PRAGMA temp_store=memory")
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB max mmap
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
                
                # Radar data table for caching tiles
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS radar_tiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        data_type TEXT NOT NULL CHECK(data_type IN ('radar', 'satellite')),
                        tile_path TEXT NOT NULL,
                        zoom INTEGER NOT NULL,
                        x INTEGER NOT NULL,
                        y INTEGER NOT NULL,
                        color_scheme INTEGER DEFAULT 1,
                        snow BOOLEAN DEFAULT FALSE,
                        smooth BOOLEAN DEFAULT TRUE,
                        tile_data BLOB NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Radar animation metadata table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS radar_animations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        version TEXT,
                        generated DATETIME,
                        host TEXT,
                        frame_count INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better query performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON weather_observations(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_station_id ON weather_observations(station_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_station_timestamp ON weather_observations(station_id, timestamp)")
                
                # Radar indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_radar_timestamp ON radar_tiles(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_radar_path ON radar_tiles(tile_path)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_radar_coords ON radar_tiles(zoom, x, y)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_radar_type ON radar_tiles(data_type)")
                
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
    
    def write_radar_tile(self, timestamp: datetime, data_type: str, tile_path: str, 
                        zoom: int, x: int, y: int, tile_data: bytes, 
                        color_scheme: int = 1, snow: bool = False, smooth: bool = True) -> bool:
        """Write radar tile data to SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO radar_tiles 
                    (timestamp, data_type, tile_path, zoom, x, y, color_scheme, snow, smooth, tile_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    data_type,
                    tile_path,
                    zoom,
                    x,
                    y,
                    color_scheme,
                    snow,
                    smooth,
                    tile_data
                ))
                conn.commit()
                
            logger.debug(f"Successfully wrote radar tile {tile_path} ({zoom}/{x}/{y})")
            return True
            
        except Exception as e:
            logger.error(f"Error writing radar tile to SQLite: {e}")
            return False
    
    def get_radar_tile(self, tile_path: str, zoom: int, x: int, y: int, 
                      max_age_hours: int = 1) -> Optional[bytes]:
        """Get cached radar tile from SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT tile_data FROM radar_tiles 
                    WHERE tile_path = ? AND zoom = ? AND x = ? AND y = ?
                    AND created_at > datetime('now', '-{} hours')
                    ORDER BY created_at DESC 
                    LIMIT 1
                """.format(max_age_hours), (tile_path, zoom, x, y))
                
                row = cursor.fetchone()
                return row[0] if row else None
                
        except Exception as e:
            logger.error(f"Error getting radar tile from SQLite: {e}")
            return None
    
    def write_radar_animation(self, timestamp: datetime, version: str, 
                            generated: datetime, host: str, frame_count: int) -> bool:
        """Write radar animation metadata to SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO radar_animations 
                    (timestamp, version, generated, host, frame_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (timestamp, version, generated, host, frame_count))
                conn.commit()
                
            logger.debug(f"Successfully wrote radar animation metadata")
            return True
            
        except Exception as e:
            logger.error(f"Error writing radar animation to SQLite: {e}")
            return False
    
    def get_historical_radar_frames(self, hours: int = 2, data_type: str = 'radar') -> List[dict]:
        """Get historical radar frames from the last N hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT DISTINCT timestamp, tile_path 
                    FROM radar_tiles 
                    WHERE data_type = ? 
                    AND timestamp > datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours), (data_type,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error querying historical radar frames: {e}")
            return []
    
    def cleanup_old_radar_data(self, hours_to_keep: int = 24):
        """Remove old radar data to save space"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM radar_tiles 
                    WHERE created_at < datetime('now', '-{} hours')
                """.format(hours_to_keep))
                
                deleted_tiles = cursor.rowcount
                
                cursor = conn.execute("""
                    DELETE FROM radar_animations 
                    WHERE created_at < datetime('now', '-{} hours')
                """.format(hours_to_keep))
                
                deleted_animations = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_tiles} old radar tiles and {deleted_animations} animations")
                
        except Exception as e:
            logger.error(f"Error cleaning up radar data: {e}")

    def close(self):
        """Close database connection - no-op for SQLite"""
        pass