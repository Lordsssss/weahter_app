import time
import asyncio
from datetime import datetime, timezone
from typing import List, Tuple
from loguru import logger

from ..api.radar_client import RainViewerClient
from ..models.radar import RadarTileInfo, RadarAnimation
from ..database.database_factory import get_database_manager
from ..config import settings

class RadarDataCollector:
    """Service for collecting and storing radar data"""
    
    def __init__(self, center_lat: float = 45.575, center_lon: float = -73.88):
        self.radar_client = RainViewerClient()
        self.db_manager = get_database_manager()
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.collection_interval = 600  # 10 minutes
        self.running = False
        
        # Montreal area coverage
        self.zoom_levels = [6, 7]  # Different zoom levels for different detail
        self.tile_radius = 3  # Tiles around center point
        
    def start_collection(self):
        """Start radar data collection in background"""
        self.running = True
        logger.info("Starting radar data collection service...")
        
        while self.running:
            try:
                self._collect_radar_data()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in radar collection loop: {e}")
                time.sleep(60)  # Wait 1 minute on error before retrying
    
    def stop_collection(self):
        """Stop radar data collection"""
        self.running = False
        logger.info("Stopping radar data collection service...")
    
    def _collect_radar_data(self):
        """Collect current radar data and store in database"""
        try:
            # Get available weather maps
            animation = self.radar_client.get_weather_maps()
            if not animation:
                logger.warning("Failed to fetch weather maps")
                return
            
            logger.info(f"Found {len(animation.radar)} radar frames, collecting recent data...")
            
            # Store animation metadata
            self.db_manager.write_radar_animation(
                timestamp=datetime.now(timezone.utc),
                version=animation.version,
                generated=animation.generated,
                host=animation.host,
                frame_count=len(animation.radar)
            )
            
            # Collect tiles for the most recent radar frames (last 3 frames)
            recent_frames = animation.radar[-3:] if len(animation.radar) >= 3 else animation.radar
            
            for frame in recent_frames:
                self._collect_frame_tiles(frame, animation.host, 'radar')
            
            # Also collect satellite data if available
            if animation.satellite:
                recent_satellite = animation.satellite[-1:]  # Just the latest satellite frame
                for frame in recent_satellite:
                    self._collect_frame_tiles(frame, animation.host, 'satellite')
            
            # Cleanup old data
            self.db_manager.cleanup_old_radar_data(hours_to_keep=24)
            
            logger.info("Radar data collection completed successfully")
            
        except Exception as e:
            logger.error(f"Error collecting radar data: {e}")
    
    def _collect_frame_tiles(self, frame, host: str, data_type: str):
        """Collect tiles for a specific radar frame"""
        try:
            tiles_collected = 0
            tiles_total = 0
            
            for zoom in self.zoom_levels:
                # Get tile coordinates for coverage area
                coverage_tiles = self.radar_client.get_coverage_tiles(
                    self.center_lat, 
                    self.center_lon, 
                    zoom, 
                    self.tile_radius
                )
                
                tiles_total += len(coverage_tiles)
                
                for x, y in coverage_tiles:
                    tile_info = RadarTileInfo(
                        timestamp=frame.timestamp,
                        zoom=zoom,
                        x=x,
                        y=y,
                        color_scheme=1,
                        snow=False,
                        smooth=True
                    )
                    
                    # Check if we already have this tile cached
                    cached_tile = self.db_manager.get_radar_tile(
                        frame.path, zoom, x, y, max_age_hours=1
                    )
                    
                    if cached_tile:
                        logger.debug(f"Tile {zoom}/{x}/{y} already cached, skipping")
                        tiles_collected += 1
                        continue
                    
                    # Fetch and store the tile
                    tile_data = self.radar_client.get_radar_tile(host, frame.path, tile_info)
                    
                    if tile_data:
                        success = self.db_manager.write_radar_tile(
                            timestamp=frame.timestamp,
                            data_type=data_type,
                            tile_path=frame.path,
                            zoom=zoom,
                            x=x,
                            y=y,
                            tile_data=tile_data,
                            color_scheme=1,
                            snow=False,
                            smooth=True
                        )
                        
                        if success:
                            tiles_collected += 1
                            logger.debug(f"Collected {data_type} tile {zoom}/{x}/{y}")
                        else:
                            logger.warning(f"Failed to store {data_type} tile {zoom}/{x}/{y}")
                    else:
                        logger.warning(f"Failed to fetch {data_type} tile {zoom}/{x}/{y}")
                    
                    # Small delay to avoid overwhelming the API
                    time.sleep(0.1)
            
            logger.info(f"Collected {tiles_collected}/{tiles_total} {data_type} tiles for frame {frame.timestamp}")
            
        except Exception as e:
            logger.error(f"Error collecting frame tiles: {e}")
    
    def collect_historical_data(self, hours: int = 2):
        """One-time collection of historical radar data"""
        try:
            logger.info(f"Starting historical radar data collection for {hours} hours")
            
            animation = self.radar_client.get_weather_maps()
            if not animation:
                logger.error("Failed to fetch weather maps for historical collection")
                return False
            
            # Filter frames to last N hours
            cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)
            historical_frames = [
                frame for frame in animation.radar
                if frame.timestamp.timestamp() >= cutoff_time
            ]
            
            logger.info(f"Found {len(historical_frames)} frames in the last {hours} hours")
            
            for i, frame in enumerate(historical_frames):
                logger.info(f"Collecting historical frame {i+1}/{len(historical_frames)}: {frame.timestamp}")
                self._collect_frame_tiles(frame, animation.host, 'radar')
                
                # Longer delay for historical collection to be respectful to the API
                time.sleep(1)
            
            logger.info("Historical radar data collection completed")
            return True
            
        except Exception as e:
            logger.error(f"Error in historical data collection: {e}")
            return False
    
    def get_collection_status(self) -> dict:
        """Get status of radar data collection"""
        try:
            # Get database stats
            import sqlite3
            conn = sqlite3.connect(self.db_manager.db_path)
            
            # Count radar tiles
            radar_count = conn.execute("SELECT COUNT(*) FROM radar_tiles WHERE data_type = 'radar'").fetchone()[0]
            satellite_count = conn.execute("SELECT COUNT(*) FROM radar_tiles WHERE data_type = 'satellite'").fetchone()[0]
            
            # Get latest data timestamp
            latest_radar = conn.execute("""
                SELECT MAX(timestamp) FROM radar_tiles WHERE data_type = 'radar'
            """).fetchone()[0]
            
            # Get data age
            latest_animation = conn.execute("""
                SELECT MAX(created_at) FROM radar_animations
            """).fetchone()[0]
            
            conn.close()
            
            return {
                'running': self.running,
                'center_coordinates': {'lat': self.center_lat, 'lon': self.center_lon},
                'collection_interval_seconds': self.collection_interval,
                'zoom_levels': self.zoom_levels,
                'tile_radius': self.tile_radius,
                'radar_tiles_stored': radar_count,
                'satellite_tiles_stored': satellite_count,
                'latest_radar_data': latest_radar,
                'latest_collection': latest_animation
            }
            
        except Exception as e:
            logger.error(f"Error getting collection status: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close resources"""
        self.stop_collection()
        if self.radar_client:
            self.radar_client.close()
        if self.db_manager:
            self.db_manager.close()