import click
import os
import sys
from loguru import logger

from .monitor import WeatherMonitor
from .config import settings

def setup_logging():
    """Setup logging configuration"""
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.remove()
    logger.add(
        settings.log_file,
        level=settings.log_level,
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="{time:HH:mm:ss} | {level} | {message}"
    )

@click.group()
def cli():
    """Weather Monitor CLI"""
    setup_logging()

@cli.command()
def start():
    """Start weather monitoring service"""
    monitor = WeatherMonitor()
    monitor.start_monitoring()

@cli.command()
def test():
    """Test database connection"""
    from .database.database_factory import get_database_manager
    
    db_manager = get_database_manager()
    if db_manager.test_connection():
        click.echo("✅ Database connection successful")
    else:
        click.echo("❌ Database connection failed")

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def radar_api(host, port, debug):
    """Start radar API proxy server"""
    from .api.radar_proxy import RadarProxyAPI
    
    api = RadarProxyAPI()
    api.run(host=host, port=port, debug=debug)

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5001, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def admin_api(host, port, debug):
    """Start admin API server for station management"""
    from .api.admin_api import AdminAPI
    
    api = AdminAPI()
    api.run(host=host, port=port, debug=debug)

@cli.command()
@click.option('--lat', default=45.575, help='Center latitude for radar collection')
@click.option('--lon', default=-73.88, help='Center longitude for radar collection')
def radar_collect(lat, lon):
    """Start radar data collection service"""
    from .services.radar_collector import RadarDataCollector
    
    collector = RadarDataCollector(center_lat=lat, center_lon=lon)
    try:
        collector.start_collection()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping radar collection...")
        collector.stop_collection()

@cli.command()
@click.option('--hours', default=2, help='Hours of historical data to collect')
@click.option('--lat', default=45.575, help='Center latitude for radar collection')
@click.option('--lon', default=-73.88, help='Center longitude for radar collection')
def radar_historical(hours, lat, lon):
    """Collect historical radar data"""
    from .services.radar_collector import RadarDataCollector
    
    collector = RadarDataCollector(center_lat=lat, center_lon=lon)
    success = collector.collect_historical_data(hours=hours)
    
    if success:
        click.echo(f"✅ Successfully collected {hours} hours of historical radar data")
    else:
        click.echo("❌ Failed to collect historical radar data")
    
    collector.close()

@cli.command()
def radar_status():
    """Show radar collection status"""
    from .services.radar_collector import RadarDataCollector
    
    collector = RadarDataCollector()
    status = collector.get_collection_status()
    
    click.echo("Radar Collection Status:")
    click.echo(f"  Running: {status.get('running', False)}")
    click.echo(f"  Center: {status.get('center_coordinates', {})}")
    click.echo(f"  Radar tiles stored: {status.get('radar_tiles_stored', 0)}")
    click.echo(f"  Satellite tiles stored: {status.get('satellite_tiles_stored', 0)}")
    click.echo(f"  Latest radar data: {status.get('latest_radar_data', 'None')}")
    click.echo(f"  Latest collection: {status.get('latest_collection', 'None')}")
    
    collector.close()

if __name__ == "__main__":
    cli()