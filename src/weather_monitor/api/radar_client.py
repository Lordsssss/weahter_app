import requests
import gzip
from typing import Optional, Tuple
from loguru import logger
from datetime import datetime, timezone

from ..models.radar import RadarAnimation, RadarTileInfo

class RainViewerClient:
    """Client for RainViewer weather radar API"""
    
    def __init__(self):
        self.api_base_url = "https://api.rainviewer.com/public/weather-maps.json"
        self.session = requests.Session()
        
    def get_weather_maps(self) -> Optional[RadarAnimation]:
        """Fetch available weather maps from RainViewer API"""
        try:
            response = self.session.get(self.api_base_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            animation = RadarAnimation.from_api_response(data)
            
            logger.info(f"Successfully fetched {len(animation.radar)} radar frames and {len(animation.satellite)} satellite frames")
            return animation
            
        except requests.RequestException as e:
            logger.error(f"HTTP error fetching weather maps: {e}")
            return None
        except ValueError as e:
            logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather maps: {e}")
            return None
    
    def get_radar_tile(self, host: str, path: str, tile_info: RadarTileInfo) -> Optional[bytes]:
        """Fetch a specific radar tile"""
        # Clean up host URL (remove https:// if present)
        clean_host = host.replace('https://', '').replace('http://', '')
        
        # Ensure path starts with / but doesn't have duplicate slashes
        clean_path = path if path.startswith('/') else f'/{path}'
        
        # Construct tile URL - RainViewer format: https://host/path/zoom/x/y/color/snow_smooth.png
        tile_url = f"https://{clean_host}{clean_path}/{tile_info.zoom}/{tile_info.x}/{tile_info.y}/{tile_info.color_scheme}/{'1' if tile_info.snow else '0'}_{'1' if tile_info.smooth else '0'}.png"
        
        try:
            response = self.session.get(tile_url, timeout=10)
            response.raise_for_status()
            
            # Compress the tile data for storage
            compressed_data = gzip.compress(response.content)
            
            logger.debug(f"Successfully fetched radar tile {tile_info.zoom}/{tile_info.x}/{tile_info.y}")
            return compressed_data
            
        except requests.RequestException as e:
            logger.error(f"HTTP error fetching radar tile: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching radar tile: {e}")
            return None
    
    def calculate_tile_coordinates(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """Calculate tile coordinates for given lat/lon at zoom level"""
        import math
        
        # Convert lat/lon to tile coordinates
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        
        x = int((lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        
        return x, y
    
    def get_coverage_tiles(self, center_lat: float, center_lon: float, zoom: int = 6, radius: int = 2) -> list:
        """Get list of tile coordinates covering an area around center point"""
        center_x, center_y = self.calculate_tile_coordinates(center_lat, center_lon, zoom)
        
        tiles = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                x = center_x + dx
                y = center_y + dy
                
                # Ensure tiles are within valid bounds
                max_tile = 2 ** zoom
                if 0 <= x < max_tile and 0 <= y < max_tile:
                    tiles.append((x, y))
        
        return tiles
    
    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()