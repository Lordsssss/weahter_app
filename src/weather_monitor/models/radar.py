from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

class RadarTileInfo(BaseModel):
    """Information about a radar tile"""
    timestamp: datetime = Field(..., description="Timestamp of the radar data")
    zoom: int = Field(..., description="Zoom level (0-7)")
    x: int = Field(..., description="Tile X coordinate")
    y: int = Field(..., description="Tile Y coordinate")
    color_scheme: int = Field(1, description="Color scheme (1-8)")
    snow: bool = Field(False, description="Snow radar data")
    smooth: bool = Field(True, description="Smooth radar data")
    
class RadarFrame(BaseModel):
    """Radar animation frame from RainViewer API"""
    timestamp: datetime = Field(..., description="UTC timestamp of radar data")
    path: str = Field(..., description="Path to radar tile")
    
    @classmethod
    def from_api_response(cls, timestamp: int, path: str) -> 'RadarFrame':
        """Create RadarFrame from API response"""
        return cls(
            timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
            path=path
        )

class RadarAnimation(BaseModel):
    """Collection of radar frames for animation"""
    version: str = Field(..., description="API version")
    generated: datetime = Field(..., description="When the data was generated")
    host: str = Field(..., description="CDN host for tiles")
    radar: List[RadarFrame] = Field(default_factory=list, description="Radar frames")
    satellite: List[RadarFrame] = Field(default_factory=list, description="Satellite frames")
    
    @classmethod
    def from_api_response(cls, data: dict) -> 'RadarAnimation':
        """Create RadarAnimation from RainViewer API response"""
        radar_frames = []
        if 'radar' in data and 'past' in data['radar']:
            radar_frames = [
                RadarFrame.from_api_response(item['time'], item['path'])
                for item in data['radar']['past']
                if isinstance(item, dict) and 'time' in item and 'path' in item
            ]
        
        satellite_frames = []
        if 'satellite' in data and 'infrared' in data['satellite']:
            satellite_frames = [
                RadarFrame.from_api_response(item['time'], item['path'])
                for item in data['satellite']['infrared']
                if isinstance(item, dict) and 'time' in item and 'path' in item
            ]
        
        return cls(
            version=data.get('version', ''),
            generated=datetime.fromtimestamp(data.get('generated', 0), tz=timezone.utc),
            host=data.get('host', ''),
            radar=radar_frames,
            satellite=satellite_frames
        )

class StoredRadarData(BaseModel):
    """Stored radar data in database"""
    id: Optional[int] = Field(None, description="Database ID")
    timestamp: datetime = Field(..., description="Radar data timestamp")
    data_type: str = Field(..., description="Type: radar or satellite")
    tile_data: bytes = Field(..., description="Compressed tile data")
    zoom: int = Field(..., description="Zoom level")
    x: int = Field(..., description="Tile X coordinate")
    y: int = Field(..., description="Tile Y coordinate")
    color_scheme: int = Field(1, description="Color scheme")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))