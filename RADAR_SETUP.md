# Weather Radar Integration

This document describes the weather radar integration using RainViewer API that has been added to the weather monitoring system.

## Overview

The radar integration provides:
- Real-time weather radar tile proxy with caching
- Historical radar data collection and storage
- RESTful API for accessing radar data
- Integration with existing Grafana dashboards

## Components

### 1. Radar API Proxy (`radar-api` service)
- **Port**: 5000
- **Container**: weather-radar-api
- **Purpose**: Proxies radar tile requests to RainViewer API with local caching

### 2. Radar Data Collector (`radar-collector` service)
- **Container**: weather-radar-collector
- **Purpose**: Collects and stores radar data every 10 minutes
- **Coverage**: Montreal area (45.575, -73.88) with configurable radius

### 3. Database Schema
New tables added to SQLite database:
- `radar_tiles`: Stores compressed radar tile data
- `radar_animations`: Stores metadata about radar animation frames

## API Endpoints

All endpoints are available through nginx proxy at `http://your-server/api/radar/`

### Get Weather Maps
```
GET /api/radar/maps
```
Returns available radar animation frames from RainViewer API.

### Get Radar Tile (with caching)
```
GET /api/radar/tile/{tile_path}?zoom=6&x=16&y=23&color=1&snow=false&smooth=true&host=tilecache.rainviewer.com
```
Returns a radar tile image, cached locally for 1 hour.

### Get Coverage Area
```
GET /api/radar/coverage?lat=45.575&lon=-73.88&zoom=6&radius=2
```
Returns tile coordinates covering the specified area.

### Get Historical Data
```
GET /api/radar/historical?hours=2&type=radar
```
Returns historical radar frames stored locally.

### Health Check
```
GET /health
```
Returns system health status.

## CLI Commands

### Start Radar API Server
```bash
python -m weather_monitor.cli radar-api --host 0.0.0.0 --port 5000
```

### Start Radar Collection
```bash
python -m weather_monitor.cli radar-collect --lat 45.575 --lon -73.88
```

### Collect Historical Data
```bash
python -m weather_monitor.cli radar-historical --hours 2 --lat 45.575 --lon -73.88
```

### Check Collection Status
```bash
python -m weather_monitor.cli radar-status
```

## Docker Deployment

The radar services are automatically included in docker-compose.yml:

```bash
# Start all services including radar
docker-compose up -d

# Check radar services
docker-compose logs radar-api
docker-compose logs radar-collector

# Restart just radar services
docker-compose restart radar-api radar-collector
```

## Configuration

### Environment Variables
- `DATABASE_TYPE`: Database type (default: sqlite)
- `SQLITE_DB_PATH`: Path to SQLite database file
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

### Collection Settings
- **Interval**: 10 minutes (600 seconds)
- **Zoom Levels**: 6, 7 (configurable in RadarDataCollector)
- **Tile Radius**: 3 tiles around center point
- **Cache Duration**: 1 hour for tiles
- **Data Retention**: 24 hours for radar data

## Integration with Grafana

The radar API can be used to create custom Grafana panels or external visualizations:

1. **Radar Overlay Panel**: Create a custom panel that overlays radar data on the weather station map
2. **Animation Controls**: Use the historical data API to create radar animation controls
3. **Real-time Updates**: Poll the maps endpoint for new radar frames

### Example JavaScript for Grafana Panel
```javascript
// Get radar maps
fetch('/api/radar/maps')
  .then(response => response.json())
  .then(data => {
    // Process radar frames for animation
    const frames = data.radar;
    // Display on map overlay
  });

// Get specific tile
const tileUrl = `/api/radar/tile/${tilePath}?zoom=6&x=16&y=23&color=1`;
// Use tileUrl in map overlay
```

## Monitoring and Maintenance

### Check Service Health
```bash
curl http://your-server/health
```

### Monitor Collection Status
```bash
docker exec weather-radar-collector python -m weather_monitor.cli radar-status
```

### Database Maintenance
- Radar tiles are automatically cleaned up after 24 hours
- Database includes indexes for optimal query performance
- Compressed tile storage minimizes disk usage

### Logs
- Radar API logs: `./logs/weather_monitor.log`
- Docker logs: `docker-compose logs radar-api radar-collector`

## Troubleshooting

### Common Issues

1. **Radar tiles not loading**
   - Check nginx configuration for `/api/radar/` proxy
   - Verify radar-api service is running: `docker-compose ps`
   - Check RainViewer API availability

2. **No historical data**
   - Ensure radar-collector service is running
   - Check collection status: `docker exec weather-radar-collector python -m weather_monitor.cli radar-status`
   - Verify database permissions and disk space

3. **High memory usage**
   - Radar data collection can use significant memory
   - Adjust tile radius and zoom levels in RadarDataCollector
   - Monitor docker container resource limits

### Performance Optimization

1. **Reduce tile collection**:
   - Decrease tile_radius in RadarDataCollector
   - Use fewer zoom levels
   - Increase collection interval

2. **Improve caching**:
   - Increase cache duration for frequently accessed tiles
   - Add Redis cache layer for high-traffic deployments

3. **Database optimization**:
   - Regular VACUUM operations for SQLite
   - Consider PostgreSQL for high-volume deployments

## API Rate Limiting

The integration is designed to be respectful to RainViewer API:
- 0.1 second delay between tile requests
- 1 second delay for historical collection
- Local caching reduces API calls
- Covers only Montreal area by default

For larger coverage areas or more frequent updates, consider RainViewer's commercial API plans.