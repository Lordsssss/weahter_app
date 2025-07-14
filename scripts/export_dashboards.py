#!/usr/bin/env python3
"""
Export Grafana dashboards from container to local filesystem for git versioning
"""

import json
import requests
import os
from pathlib import Path

# Grafana configuration
GRAFANA_URL = "http://localhost:3002"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "password123"

# Local dashboard directory
DASHBOARD_DIR = Path(__file__).parent.parent / "grafana" / "dashboards"

def get_auth():
    """Get Grafana authentication"""
    return (GRAFANA_USER, GRAFANA_PASSWORD)

def get_dashboards():
    """Get list of all dashboards"""
    url = f"{GRAFANA_URL}/api/search?type=dash-db"
    response = requests.get(url, auth=get_auth())
    response.raise_for_status()
    return response.json()

def export_dashboard(dashboard_uid, dashboard_title):
    """Export a specific dashboard"""
    url = f"{GRAFANA_URL}/api/dashboards/uid/{dashboard_uid}"
    response = requests.get(url, auth=get_auth())
    response.raise_for_status()
    
    dashboard_data = response.json()
    dashboard_json = dashboard_data["dashboard"]
    
    # Remove runtime metadata
    dashboard_json.pop("id", None)
    dashboard_json.pop("version", None)
    dashboard_json.pop("uid", None)
    
    # Clean filename
    filename = "".join(c for c in dashboard_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = filename.replace(' ', '-').lower() + ".json"
    
    # Save to file
    filepath = DASHBOARD_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(dashboard_json, f, indent=2, sort_keys=True)
    
    print(f"Exported: {dashboard_title} -> {filename}")
    return filepath

def main():
    """Export all dashboards"""
    print("Exporting Grafana dashboards...")
    
    # Ensure directory exists
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        dashboards = get_dashboards()
        
        if not dashboards:
            print("No dashboards found")
            return
        
        exported_files = []
        for dashboard in dashboards:
            try:
                filepath = export_dashboard(dashboard["uid"], dashboard["title"])
                exported_files.append(filepath)
            except Exception as e:
                print(f"Error exporting {dashboard['title']}: {e}")
        
        print(f"\nExported {len(exported_files)} dashboards to {DASHBOARD_DIR}")
        print("You can now commit these changes to git:")
        print(f"  git add {DASHBOARD_DIR}")
        print("  git commit -m 'Update Grafana dashboards'")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Grafana. Make sure it's running on port 3002")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()