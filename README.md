# Weather Station Monitoring System

A comprehensive weather monitoring system that collects weather data from Weather.com API and visualizes it in Grafana dashboards using InfluxDB as the time-series database.

[![Docker](https://img.shields.io/badge/Docker-supported-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- **Real-time Weather Data Collection**: Fetches weather data from Weather.com API
- **Time-series Database**: Stores data in SQLite for efficient querying
- **Grafana Dashboards**: Beautiful visualizations and monitoring dashboards
- **Dashboard Export**: Export Grafana dashboard changes to git-trackable files
- **Docker Support**: Easy deployment with Docker Compose
- **Configuration Management**: Environment-based configuration
- **Robust Error Handling**: Comprehensive logging and error recovery
- **Data Migration**: Import existing CSV data into the system
- **Multiple Station Support**: Monitor multiple weather stations simultaneously
- **VM Monitoring**: Comprehensive system and container monitoring with Prometheus

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Weather API    │───▶│ Weather Monitor │───▶│    InfluxDB     │
│  (Weather.com)  │    │   (Python App)  │    │ (Time-series DB)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │     Grafana     │
                                               │  (Dashboards)   │
                                               └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Weather.com API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd weather_app
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Weather API credentials
```

### 3. Start the Stack

```bash
docker-compose up -d
```

### 4. Access Services

- **Grafana**: http://localhost:3000 (admin/admin)
- **InfluxDB**: http://localhost:8086
- **Weather Monitor**: Runs automatically in container

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WEATHER_API_KEY` | Weather.com API key | Required |
| `WEATHER_STATION_ID` | Weather station ID | Required |
| `WEATHER_FETCH_INTERVAL` | Fetch interval in seconds | 20 |
| `INFLUXDB_URL` | InfluxDB URL | http://localhost:8086 |
| `INFLUXDB_TOKEN` | InfluxDB authentication token | Required |
| `INFLUXDB_ORG` | InfluxDB organization | weather-monitoring |
| `INFLUXDB_BUCKET` | InfluxDB bucket name | weather-data |
| `LOG_LEVEL` | Logging level | INFO |

### Weather API Setup

1. Get an API key from Weather.com
2. Find your weather station ID
3. Update the `.env` file with your credentials

## Local Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Set environment variables
export PYTHONPATH=src

# Test database connection
python -m weather_monitor.cli test

# Start monitoring
python -m weather_monitor.cli start
```

## Data Migration

Import existing CSV data (optional):

```bash
python scripts/import_csv_data.py your_weather_data.csv
```

## Grafana Dashboards

The system includes pre-configured dashboards showing:

- **Current Weather**: Temperature, humidity, pressure readings
- **Trends**: Historical data visualization
- **Environmental**: UV index, solar radiation, precipitation
- **Wind Data**: Speed, direction, and gusts

### Dashboard Features

- Real-time updates (5-second refresh)
- Historical data analysis
- Responsive design
- Customizable time ranges
- Alert capabilities

## Docker Deployment

The system uses Docker Compose for easy deployment:

```yaml
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f weather-monitor

# Stop services
docker-compose down
```

## Admin Interface

### Weather Station Management

The system includes a web-based admin interface for managing weather stations at runtime:

- **Admin Dashboard**: http://localhost:5001/admin
- **Default Admin Key**: `admin123` (change via `ADMIN_API_KEY` environment variable)

### Admin Features

- ✅ Add new weather stations without restarting services
- ✅ Edit existing station information (name, location, status)
- ✅ Activate/deactivate stations
- ✅ Delete stations
- ✅ View system status and statistics
- ✅ Real-time configuration updates

### Admin Workflow

1. Open admin dashboard: http://localhost:5001/admin
2. Enter admin key: `admin123`
3. Add/edit weather stations as needed
4. Changes are automatically saved to `config/weather_stations.json`
5. Monitor picks up changes and starts tracking new stations

### API Endpoints

All admin API endpoints require the `X-Admin-Key` header:

```bash
# Get all stations
curl -H "X-Admin-Key: admin123" http://localhost:5001/api/admin/stations

# Add new station
curl -X POST -H "Content-Type: application/json" -H "X-Admin-Key: admin123" \
  -d '{"station_id":"ITEST001","name":"Test Station","city":"Test City","latitude":45.5,"longitude":-73.6}' \
  http://localhost:5001/api/admin/stations

# Update station
curl -X PUT -H "Content-Type: application/json" -H "X-Admin-Key: admin123" \
  -d '{"active":false}' \
  http://localhost:5001/api/admin/stations/ITEST001

# Delete station
curl -X DELETE -H "X-Admin-Key: admin123" \
  http://localhost:5001/api/admin/stations/ITEST001
```

## Dashboard Management

### Exporting Dashboard Changes

When you make changes to Grafana dashboards through the UI, they are stored in the container's database but not automatically saved to your local files. To export changes for git tracking:

```bash
# Export all dashboards to local files
./scripts/export_dashboards.sh

# Or use the Python script directly
python3 scripts/export_dashboards.py

# Force export all dashboards
python3 scripts/sync_dashboards.py --force
```

### Workflow for Dashboard Changes

1. Make changes in Grafana UI (http://localhost:3002)
2. Export dashboards: `./scripts/export_dashboards.sh`
3. Review changes: `git diff grafana/dashboards/`
4. Commit changes: `git add grafana/dashboards/ && git commit -m "Update dashboards"`
5. Push to remote: `git push`

### Dashboard Files

- Local dashboard files: `grafana/dashboards/`
- Provisioning config: `grafana/provisioning/dashboards/dashboard.yml`
- Container storage: `grafana_data` volume (not persisted)

## VM Monitoring

### Available Dashboards

The system includes comprehensive VM monitoring via Prometheus + cAdvisor:

- **VM Monitoring Dashboard**: Complete system metrics (CPU, Memory, Disk, Network)
- **Prometheus**: http://localhost:9090 (metrics collection)
- **cAdvisor**: http://localhost:8080 (container insights)

### Monitored Metrics

- **System**: CPU usage, memory usage, disk I/O, network traffic
- **Containers**: Docker container resource usage and performance
- **Load**: System load averages and process information
- **Storage**: Disk usage and filesystem metrics

### Starting VM Monitoring

```bash
# Start monitoring stack
docker-compose up -d prometheus node-exporter cadvisor

# Access dashboards
# Grafana: http://localhost:3002 (admin/password123)
# Prometheus: http://localhost:9090
# cAdvisor: http://localhost:8080
```

## Monitoring and Alerts

### Logs

- Application logs: `logs/weather_monitor.log`
- Docker logs: `docker-compose logs`

### Health Checks

```bash
# Test database connection
python -m weather_monitor.cli test

# Check service status
docker-compose ps
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check InfluxDB is running: `docker-compose ps`
   - Verify token in `.env` file
   - Check network connectivity

2. **API Errors**
   - Verify API key is valid
   - Check station ID format
   - Monitor rate limits

3. **Grafana Dashboard Issues**
   - Check datasource configuration
   - Verify InfluxDB connection
   - Restart Grafana: `docker-compose restart grafana`

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python -m weather_monitor.cli start
```

## API Reference

### Weather Data Model

```python
{
    "timestamp": "2025-07-08T20:52:08",
    "station_id": "ISAINT6228",
    "neighborhood": "Saint-Eustache",
    "temperature": 23.1,
    "humidity": 64.0,
    "dewpoint": 15.9,
    "heat_index": 23.1,
    "wind_speed": 0.0,
    "wind_gust": 0.0,
    "wind_direction": 248,
    "pressure": 1014.9,
    "uv_index": null,
    "solar_radiation": null,
    "precipitation_rate": 0.0,
    "precipitation_total": 0.0
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for error details