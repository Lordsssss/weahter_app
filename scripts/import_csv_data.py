#!/usr/bin/env python3
"""
Script to import existing CSV weather data into SQLite database
"""

import sys
import os
import csv
from datetime import datetime
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from weather_monitor.database.database_factory import get_database_manager
from weather_monitor.models.weather import WeatherObservation

def import_csv_data(csv_file_path: str):
    """Import weather data from CSV file into SQLite database"""
    
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file '{csv_file_path}' not found")
        return False
    
    db_manager = get_database_manager()
    
    # Test connection
    if not db_manager.test_connection():
        print("Error: Could not connect to database")
        return False
    
    imported_count = 0
    errors = 0
    
    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    # Convert CSV row to WeatherObservation
                    observation = WeatherObservation(
                        timestamp=datetime.fromisoformat(row['obsTimeLocal']),
                        station_id=row['stationID'],
                        neighborhood=row['neighborhood'] if row['neighborhood'] else None,
                        temperature=float(row['temp']) if row['temp'] else None,
                        humidity=float(row['humidity']) if row['humidity'] else None,
                        dewpoint=float(row['dewpt']) if row['dewpt'] else None,
                        heat_index=float(row['heatIndex']) if row['heatIndex'] else None,
                        wind_speed=float(row['windSpeed']) if row['windSpeed'] else None,
                        wind_gust=float(row['windGust']) if row['windGust'] else None,
                        wind_direction=int(row['winddir']) if row['winddir'] else None,
                        pressure=float(row['pressure']) if row['pressure'] else None,
                        uv_index=float(row['uv']) if row['uv'] else None,
                        solar_radiation=float(row['solarRadiation']) if row['solarRadiation'] else None,
                        precipitation_rate=float(row['precipRate']) if row['precipRate'] else None,
                        precipitation_total=float(row['precipTotal']) if row['precipTotal'] else None
                    )
                    
                    # Write to database
                    if db_manager.write_weather_data(observation):
                        imported_count += 1
                        if imported_count % 100 == 0:
                            print(f"Imported {imported_count} records...")
                    else:
                        errors += 1
                        
                except Exception as e:
                    print(f"Error processing row: {e}")
                    errors += 1
                    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return False
    
    finally:
        db_manager.close()
    
    print(f"Import completed: {imported_count} records imported, {errors} errors")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_csv_data.py <csv_file_path>")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    success = import_csv_data(csv_file_path)
    
    if not success:
        sys.exit(1)