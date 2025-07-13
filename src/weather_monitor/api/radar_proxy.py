from flask import Flask, Response, request, jsonify, send_file
from flask_cors import CORS
import gzip
import io
from typing import Optional
from loguru import logger
from datetime import datetime, timezone

from .radar_client import RainViewerClient
from ..models.radar import RadarTileInfo
from ..database.database_factory import get_database_manager

class RadarProxyAPI:
    """Flask API for radar data proxy and storage"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for Grafana integration
        
        self.radar_client = RainViewerClient()
        self.db_manager = get_database_manager()
        
        self._register_routes()
        
    def _register_routes(self):
        """Register API routes"""
        
        @self.app.route('/api/radar/maps', methods=['GET'])
        def get_weather_maps():
            """Get available weather maps from RainViewer"""
            try:
                animation = self.radar_client.get_weather_maps()
                if animation:
                    return jsonify(animation.dict())
                else:
                    return jsonify({'error': 'Failed to fetch weather maps'}), 500
            except Exception as e:
                logger.error(f"Error in get_weather_maps: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/radar/latest-tile-url', methods=['GET'])
        def get_latest_tile_url():
            """Get URL template for latest radar tiles"""
            try:
                animation = self.radar_client.get_weather_maps()
                if animation and animation.radar:
                    # Get the latest radar frame
                    latest_frame = animation.radar[-1]
                    # Return tile URL template for Grafana
                    tile_url = f"/api/radar/tile{latest_frame.path}/{{z}}/{{x}}/{{y}}/1/0_1.png"
                    return jsonify({
                        'tileUrl': tile_url,
                        'timestamp': latest_frame.timestamp.isoformat(),
                        'opacity': 0.6
                    })
                else:
                    return jsonify({'error': 'No radar data available'}), 404
            except Exception as e:
                logger.error(f"Error getting latest tile URL: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/radar/tile/<path:tile_path>', methods=['GET'])
        def get_radar_tile(tile_path):
            """Proxy radar tile requests to RainViewer with caching"""
            try:
                # Parse query parameters
                zoom = int(request.args.get('zoom', 6))
                x = int(request.args.get('x', 0))
                y = int(request.args.get('y', 0))
                color_scheme = int(request.args.get('color', 1))
                snow = request.args.get('snow', 'false').lower() == 'true'
                smooth = request.args.get('smooth', 'true').lower() == 'true'
                
                tile_info = RadarTileInfo(
                    timestamp=datetime.now(timezone.utc),
                    zoom=zoom,
                    x=x,
                    y=y,
                    color_scheme=color_scheme,
                    snow=snow,
                    smooth=smooth
                )
                
                # Try to get from cache first
                cached_tile = self._get_cached_tile(tile_path, tile_info)
                if cached_tile:
                    # Decompress and return cached tile
                    decompressed = gzip.decompress(cached_tile)
                    return Response(decompressed, mimetype='image/png')
                
                # Get host from query params or maps API
                host = request.args.get('host', 'tilecache.rainviewer.com')
                
                # Clean up the tile_path and host for proper URL construction
                clean_tile_path = tile_path.strip('/')
                tile_data = self.radar_client.get_radar_tile(host, f"/{clean_tile_path}", tile_info)
                
                if tile_data:
                    # Cache the tile
                    self._cache_tile(tile_path, tile_info, tile_data)
                    
                    # Return decompressed tile
                    decompressed = gzip.decompress(tile_data)
                    return Response(decompressed, mimetype='image/png')
                else:
                    return jsonify({'error': 'Failed to fetch radar tile'}), 404
                    
            except Exception as e:
                logger.error(f"Error in get_radar_tile: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/radar/coverage', methods=['GET'])
        def get_radar_coverage():
            """Get radar coverage tiles for a specific area"""
            try:
                lat = float(request.args.get('lat', 45.575))
                lon = float(request.args.get('lon', -73.88))
                zoom = int(request.args.get('zoom', 6))
                radius = int(request.args.get('radius', 2))
                
                tiles = self.radar_client.get_coverage_tiles(lat, lon, zoom, radius)
                
                return jsonify({
                    'center': {'lat': lat, 'lon': lon},
                    'zoom': zoom,
                    'radius': radius,
                    'tiles': [{'x': x, 'y': y} for x, y in tiles]
                })
                
            except Exception as e:
                logger.error(f"Error in get_radar_coverage: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/radar/historical', methods=['GET'])
        def get_historical_radar():
            """Get historical radar data from local storage"""
            try:
                hours = int(request.args.get('hours', 2))
                data_type = request.args.get('type', 'radar')
                
                historical_data = self._get_historical_data(hours, data_type)
                
                return jsonify({
                    'data_type': data_type,
                    'hours': hours,
                    'frames': historical_data
                })
                
            except Exception as e:
                logger.error(f"Error in get_historical_radar: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'services': {
                    'database': self.db_manager.test_connection(),
                    'radar_api': True  # Could add actual RainViewer API health check
                }
            })
    
    def _get_cached_tile(self, tile_path: str, tile_info: RadarTileInfo) -> Optional[bytes]:
        """Get cached tile from database"""
        try:
            return self.db_manager.get_radar_tile(
                tile_path, 
                tile_info.zoom, 
                tile_info.x, 
                tile_info.y, 
                max_age_hours=1
            )
        except Exception as e:
            logger.error(f"Error getting cached tile: {e}")
            return None
    
    def _cache_tile(self, tile_path: str, tile_info: RadarTileInfo, tile_data: bytes):
        """Cache tile data in database"""
        try:
            self.db_manager.write_radar_tile(
                timestamp=tile_info.timestamp,
                data_type='radar',
                tile_path=tile_path,
                zoom=tile_info.zoom,
                x=tile_info.x,
                y=tile_info.y,
                tile_data=tile_data,
                color_scheme=tile_info.color_scheme,
                snow=tile_info.snow,
                smooth=tile_info.smooth
            )
        except Exception as e:
            logger.error(f"Error caching tile: {e}")
    
    def _get_historical_data(self, hours: int, data_type: str) -> list:
        """Get historical radar data from database"""
        try:
            return self.db_manager.get_historical_radar_frames(hours, data_type)
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask application"""
        logger.info(f"Starting radar proxy API on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
    
    def get_app(self):
        """Get Flask app instance for WSGI deployment"""
        return self.app