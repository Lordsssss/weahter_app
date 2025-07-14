#!/usr/bin/env python3
"""
Auto-sync script to export Grafana dashboards after changes
Can be run as a cron job or manually after dashboard updates
"""

import json
import requests
import os
import time
from pathlib import Path
from datetime import datetime

# Grafana configuration
GRAFANA_URL = "http://localhost:3002"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "password123"

# Local dashboard directory
DASHBOARD_DIR = Path(__file__).parent.parent / "grafana" / "dashboards"

def get_auth():
    """Get Grafana authentication"""
    return (GRAFANA_USER, GRAFANA_PASSWORD)

def get_dashboard_metadata():
    """Get metadata for all dashboards including last modified time"""
    url = f"{GRAFANA_URL}/api/search?type=dash-db"
    response = requests.get(url, auth=get_auth())
    response.raise_for_status()
    
    dashboards = {}
    for dash in response.json():
        # Get detailed info including update time
        detail_url = f"{GRAFANA_URL}/api/dashboards/uid/{dash['uid']}"
        detail_response = requests.get(detail_url, auth=get_auth())
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            dashboards[dash['uid']] = {
                'title': dash['title'],
                'uid': dash['uid'],
                'updated': detail_data['meta']['updated'],
                'version': detail_data['dashboard']['version']
            }
    return dashboards

def export_dashboard(dashboard_uid, dashboard_title):
    """Export a specific dashboard"""
    url = f"{GRAFANA_URL}/api/dashboards/uid/{dashboard_uid}"
    response = requests.get(url, auth=get_auth())
    response.raise_for_status()
    
    dashboard_data = response.json()
    dashboard_json = dashboard_data["dashboard"]
    
    # Remove runtime metadata but keep a backup reference
    original_id = dashboard_json.pop("id", None)
    dashboard_json.pop("version", None)
    dashboard_json.pop("uid", None)
    
    # Add export metadata
    dashboard_json["__export_meta__"] = {
        "exported_at": datetime.now().isoformat(),
        "original_id": original_id,
        "grafana_url": GRAFANA_URL
    }
    
    # Clean filename
    filename = "".join(c for c in dashboard_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = filename.replace(' ', '-').lower() + ".json"
    
    # Save to file
    filepath = DASHBOARD_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(dashboard_json, f, indent=2, sort_keys=True)
    
    return filepath

def sync_dashboards(force=False):
    """Sync dashboards if they've been modified"""
    print("Checking for dashboard changes...")
    
    # Ensure directory exists
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        dashboards = get_dashboard_metadata()
        
        if not dashboards:
            print("No dashboards found")
            return False
        
        exported_count = 0
        for uid, metadata in dashboards.items():
            dashboard_title = metadata['title']
            filename = "".join(c for c in dashboard_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = filename.replace(' ', '-').lower() + ".json"
            filepath = DASHBOARD_DIR / filename
            
            # Check if export is needed
            needs_export = force
            
            if not needs_export and filepath.exists():
                # Check if dashboard has been updated since last export
                try:
                    with open(filepath, 'r') as f:
                        existing_data = json.load(f)
                    
                    export_meta = existing_data.get("__export_meta__", {})
                    last_export = export_meta.get("exported_at", "")
                    
                    # Compare timestamps (simplified check)
                    if last_export:
                        # For now, always export to be safe
                        # In a more sophisticated version, you'd parse and compare timestamps
                        needs_export = True
                    else:
                        needs_export = True
                        
                except (json.JSONDecodeError, KeyError):
                    needs_export = True
            else:
                needs_export = True
            
            if needs_export:
                try:
                    export_dashboard(uid, dashboard_title)
                    print(f"Exported: {dashboard_title} -> {filename}")
                    exported_count += 1
                except Exception as e:
                    print(f"Error exporting {dashboard_title}: {e}")
        
        if exported_count > 0:
            print(f"\nExported {exported_count} dashboard(s) to {DASHBOARD_DIR}")
            print("\nTo commit changes:")
            print("  git add grafana/dashboards/")
            print("  git commit -m 'Update Grafana dashboards'")
            print("  git push")
            return True
        else:
            print("No dashboards needed updating")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Grafana. Make sure it's running on port 3002")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main sync function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync Grafana dashboards to local filesystem')
    parser.add_argument('--force', action='store_true', help='Force export all dashboards')
    parser.add_argument('--watch', action='store_true', help='Watch for changes (not implemented)')
    
    args = parser.parse_args()
    
    if args.watch:
        print("Watch mode not implemented yet. Use cron job for periodic sync.")
        return
    
    sync_dashboards(force=args.force)

if __name__ == "__main__":
    main()