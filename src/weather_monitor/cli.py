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

if __name__ == "__main__":
    cli()