from ..config import settings
from .sqlite_db import SQLiteManager

def get_database_manager() -> SQLiteManager:
    """Factory function to get the appropriate database manager based on configuration"""
    if settings.database_type.lower() == "sqlite":
        return SQLiteManager(settings.sqlite_db_path)
    else:
        raise ValueError(f"Unsupported database type: {settings.database_type}. Only 'sqlite' is supported.")