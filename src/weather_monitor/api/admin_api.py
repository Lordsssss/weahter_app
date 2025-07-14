"""
Admin API for weather station management
"""

from flask import Flask, Response, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
import json
import os
import signal
from typing import Dict, List, Optional
from loguru import logger
from pathlib import Path

from ..station_manager import StationManager
from ..models.weather import WeatherStation
from ..database.database_factory import get_database_manager


class AdminAPI:
    """Flask API for administrative functions"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.station_manager = StationManager()
        self.db_manager = get_database_manager()
        
        # Simple admin authentication (can be enhanced later)
        self.admin_key = os.getenv("ADMIN_API_KEY", "admin123")
        
        self._register_routes()
        
    def _check_admin_auth(self) -> bool:
        """Check if request has valid admin authentication"""
        auth_key = request.headers.get('X-Admin-Key') or request.args.get('admin_key')
        return auth_key == self.admin_key
        
    def _admin_required(self, f):
        """Decorator for admin-only endpoints"""
        def wrapper(*args, **kwargs):
            if not self._check_admin_auth():
                return jsonify({'error': 'Admin authentication required'}), 401
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
        
    def _register_routes(self):
        """Register API routes"""
        
        # Admin dashboard (web interface)
        @self.app.route('/admin')
        def admin_dashboard():
            """Serve admin dashboard"""
            return render_template_string(self._get_admin_html())
            
        @self.app.route('/admin/api.js')
        def admin_api_js():
            """Serve admin API JavaScript"""
            return Response(self._get_admin_js(), mimetype='application/javascript')
            
        # Station management API endpoints
        @self.app.route('/api/admin/stations', methods=['GET'])
        @self._admin_required
        def get_stations():
            """Get all weather stations"""
            try:
                stations = []
                for station in self.station_manager.stations.values():
                    station_dict = station.dict()
                    # Add status info
                    station_dict['status'] = self._get_station_status(station.station_id)
                    stations.append(station_dict)
                
                return jsonify({
                    'stations': stations,
                    'total_count': len(stations),
                    'active_count': len([s for s in stations if s['active']]),
                    'cities': self.station_manager.get_cities()
                })
            except Exception as e:
                logger.error(f"Error getting stations: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/admin/stations', methods=['POST'])
        @self._admin_required
        def add_station():
            """Add a new weather station"""
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['station_id', 'name', 'city', 'latitude', 'longitude']
                for field in required_fields:
                    if field not in data:
                        return jsonify({'error': f'Missing required field: {field}'}), 400
                
                # Create station object
                station = WeatherStation(
                    station_id=data['station_id'],
                    name=data['name'],
                    city=data['city'],
                    latitude=float(data['latitude']),
                    longitude=float(data['longitude']),
                    active=data.get('active', True)
                )
                
                # Check if station already exists
                if self.station_manager.get_station(station.station_id):
                    return jsonify({'error': 'Station already exists'}), 409
                
                # Add station
                if self.station_manager.add_station(station):
                    # Save config
                    self.station_manager.save_config()
                    
                    # Sync to database
                    self.station_manager.sync_to_database()
                    
                    # Signal monitor to reload config
                    self._signal_config_reload()
                    
                    logger.info(f"Added new station: {station.name} ({station.station_id})")
                    return jsonify({'message': 'Station added successfully', 'station': station.dict()}), 201
                else:
                    return jsonify({'error': 'Failed to add station'}), 500
                    
            except ValueError as e:
                return jsonify({'error': f'Invalid data: {e}'}), 400
            except Exception as e:
                logger.error(f"Error adding station: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/admin/stations/<station_id>', methods=['PUT'])
        @self._admin_required
        def update_station(station_id):
            """Update an existing weather station"""
            try:
                data = request.get_json()
                
                station = self.station_manager.get_station(station_id)
                if not station:
                    return jsonify({'error': 'Station not found'}), 404
                
                # Update station fields
                if 'name' in data:
                    station.name = data['name']
                if 'city' in data:
                    station.city = data['city']
                if 'latitude' in data:
                    station.latitude = float(data['latitude'])
                if 'longitude' in data:
                    station.longitude = float(data['longitude'])
                if 'active' in data:
                    station.active = bool(data['active'])
                
                # Save config
                self.station_manager.save_config()
                self.station_manager.sync_to_database()
                
                # Signal monitor to reload config
                self._signal_config_reload()
                
                logger.info(f"Updated station: {station.name} ({station.station_id})")
                return jsonify({'message': 'Station updated successfully', 'station': station.dict()})
                
            except ValueError as e:
                return jsonify({'error': f'Invalid data: {e}'}), 400
            except Exception as e:
                logger.error(f"Error updating station: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/admin/stations/<station_id>', methods=['DELETE'])
        @self._admin_required
        def delete_station(station_id):
            """Delete a weather station"""
            try:
                station = self.station_manager.get_station(station_id)
                if not station:
                    return jsonify({'error': 'Station not found'}), 404
                
                station_name = station.name
                
                if self.station_manager.remove_station(station_id):
                    # Save config
                    self.station_manager.save_config()
                    
                    # Signal monitor to reload config
                    self._signal_config_reload()
                    
                    logger.info(f"Deleted station: {station_name} ({station_id})")
                    return jsonify({'message': 'Station deleted successfully'})
                else:
                    return jsonify({'error': 'Failed to delete station'}), 500
                    
            except Exception as e:
                logger.error(f"Error deleting station: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/admin/reload-config', methods=['POST'])
        @self._admin_required
        def reload_config():
            """Reload station configuration"""
            try:
                # Reload station manager config
                self.station_manager.load_stations()
                
                # Signal monitor to reload config
                self._signal_config_reload()
                
                return jsonify({'message': 'Configuration reloaded successfully'})
            except Exception as e:
                logger.error(f"Error reloading config: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/admin/status', methods=['GET'])
        @self._admin_required
        def get_system_status():
            """Get system status"""
            try:
                # Get database status
                db_status = self.db_manager.test_connection()
                
                # Get recent weather data count
                recent_data_count = 0
                try:
                    # This would need to be implemented in the database manager
                    # recent_data_count = self.db_manager.get_recent_data_count()
                    pass
                except:
                    pass
                
                return jsonify({
                    'database_connected': db_status,
                    'total_stations': len(self.station_manager.stations),
                    'active_stations': len(self.station_manager.get_active_stations()),
                    'cities': len(self.station_manager.get_cities()),
                    'recent_data_points': recent_data_count
                })
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _get_station_status(self, station_id: str) -> Dict:
        """Get status information for a specific station"""
        try:
            # Get recent data from database (simplified)
            return {
                'last_update': None,  # Would query database for last update
                'data_available': True,  # Would check if station has recent data
                'api_accessible': True   # Would test API accessibility
            }
        except:
            return {
                'last_update': None,
                'data_available': False,
                'api_accessible': False
            }
    
    def _signal_config_reload(self):
        """Signal the weather monitor to reload configuration"""
        try:
            import subprocess
            import psutil
            
            # Find weather monitor processes
            monitor_pids = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and any('weather_monitor.cli' in cmd and 'start' in cmd for cmd in proc.info['cmdline']):
                        monitor_pids.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if monitor_pids:
                for pid in monitor_pids:
                    os.kill(pid, signal.SIGUSR1)
                    logger.info(f"Sent config reload signal to weather monitor process {pid}")
            else:
                logger.warning("No weather monitor processes found for reload signal")
                
        except Exception as e:
            logger.warning(f"Could not signal config reload: {e}")
    
    def _get_admin_html(self) -> str:
        """Get the admin dashboard HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weather Station Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header h1 { color: #333; margin-bottom: 10px; }
        .auth-section { background: #fff3cd; padding: 15px; border-radius: 6px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .stat-label { color: #666; margin-top: 5px; }
        .section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .section h2 { margin-bottom: 15px; color: #333; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 15px; }
        .form-group { display: flex; flex-direction: column; }
        .form-group label { margin-bottom: 5px; font-weight: 500; color: #555; }
        .form-group input, .form-group select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; transition: background-color 0.2s; }
        .btn-primary { background: #007bff; color: white; }
        .btn-primary:hover { background: #0056b3; }
        .btn-success { background: #28a745; color: white; }
        .btn-success:hover { background: #1e7e34; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-danger:hover { background: #c82333; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-secondary:hover { background: #545b62; }
        .station-list { margin-top: 20px; }
        .station-item { background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .station-info { flex-grow: 1; }
        .station-name { font-weight: bold; margin-bottom: 5px; }
        .station-details { color: #666; font-size: 0.9em; }
        .station-actions { display: flex; gap: 10px; }
        .status-active { color: #28a745; }
        .status-inactive { color: #dc3545; }
        .message { padding: 10px; border-radius: 4px; margin-bottom: 15px; }
        .message.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .message.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .hidden { display: none; }
        .loading { opacity: 0.6; pointer-events: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌤️ Weather Station Admin</h1>
            <p>Manage weather stations and monitor system status</p>
        </div>
        
        <div class="auth-section" id="authSection">
            <strong>🔑 Authentication Required</strong>
            <div style="margin-top: 10px;">
                <input type="password" id="adminKey" placeholder="Enter admin key" style="margin-right: 10px; padding: 8px;">
                <button class="btn btn-primary" onclick="authenticate()">Login</button>
            </div>
        </div>
        
        <div id="adminContent" class="hidden">
            <div id="messageContainer"></div>
            
            <div class="stats" id="statsContainer">
                <div class="stat-card">
                    <div class="stat-value" id="totalStations">-</div>
                    <div class="stat-label">Total Stations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="activeStations">-</div>
                    <div class="stat-label">Active Stations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="totalCities">-</div>
                    <div class="stat-label">Cities</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="dbStatus">-</div>
                    <div class="stat-label">Database</div>
                </div>
            </div>
            
            <div class="section">
                <h2>➕ Add New Station</h2>
                <form id="addStationForm">
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="stationId">Station ID *</label>
                            <input type="text" id="stationId" name="stationId" required placeholder="e.g., IMONTR123">
                        </div>
                        <div class="form-group">
                            <label for="stationName">Station Name *</label>
                            <input type="text" id="stationName" name="stationName" required placeholder="e.g., Downtown Weather Station">
                        </div>
                        <div class="form-group">
                            <label for="stationCity">City *</label>
                            <input type="text" id="stationCity" name="stationCity" required placeholder="e.g., Montreal">
                        </div>
                        <div class="form-group">
                            <label for="stationLat">Latitude *</label>
                            <input type="number" id="stationLat" name="stationLat" step="0.0001" required placeholder="e.g., 45.5017">
                        </div>
                        <div class="form-group">
                            <label for="stationLon">Longitude *</label>
                            <input type="number" id="stationLon" name="stationLon" step="0.0001" required placeholder="e.g., -73.5673">
                        </div>
                        <div class="form-group">
                            <label for="stationActive">Status</label>
                            <select id="stationActive" name="stationActive">
                                <option value="true">Active</option>
                                <option value="false">Inactive</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-success">Add Station</button>
                    <button type="button" class="btn btn-secondary" onclick="refreshData()">Refresh Data</button>
                </form>
            </div>
            
            <div class="section">
                <h2>📍 Existing Stations</h2>
                <div id="stationsList" class="station-list">
                    Loading stations...
                </div>
            </div>
        </div>
    </div>
    
    <script src="/admin/api.js"></script>
</body>
</html>
        '''
    
    def _get_admin_js(self) -> str:
        """Get the admin dashboard JavaScript"""
        return '''
let adminKey = '';
let stations = [];

function authenticate() {
    adminKey = document.getElementById('adminKey').value;
    if (!adminKey) {
        showMessage('Please enter admin key', 'error');
        return;
    }
    
    // Test authentication by making an API call
    fetch('/api/admin/status', {
        headers: { 'X-Admin-Key': adminKey }
    })
    .then(response => {
        if (response.ok) {
            document.getElementById('authSection').classList.add('hidden');
            document.getElementById('adminContent').classList.remove('hidden');
            loadDashboard();
        } else {
            showMessage('Invalid admin key', 'error');
        }
    })
    .catch(error => {
        showMessage('Authentication failed: ' + error.message, 'error');
    });
}

function loadDashboard() {
    refreshData();
    loadStations();
}

function refreshData() {
    fetch('/api/admin/status', {
        headers: { 'X-Admin-Key': adminKey }
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('totalStations').textContent = data.total_stations || 0;
        document.getElementById('activeStations').textContent = data.active_stations || 0;
        document.getElementById('totalCities').textContent = data.cities || 0;
        document.getElementById('dbStatus').textContent = data.database_connected ? '✅' : '❌';
    })
    .catch(error => {
        showMessage('Failed to load system status: ' + error.message, 'error');
    });
}

function loadStations() {
    fetch('/api/admin/stations', {
        headers: { 'X-Admin-Key': adminKey }
    })
    .then(response => response.json())
    .then(data => {
        stations = data.stations || [];
        renderStations();
    })
    .catch(error => {
        showMessage('Failed to load stations: ' + error.message, 'error');
    });
}

function renderStations() {
    const container = document.getElementById('stationsList');
    
    if (stations.length === 0) {
        container.innerHTML = '<p>No stations configured yet.</p>';
        return;
    }
    
    container.innerHTML = stations.map(station => `
        <div class="station-item">
            <div class="station-info">
                <div class="station-name">
                    ${station.name} 
                    <span class="${station.active ? 'status-active' : 'status-inactive'}">
                        ${station.active ? '🟢 Active' : '🔴 Inactive'}
                    </span>
                </div>
                <div class="station-details">
                    ID: ${station.station_id} | ${station.city} | 
                    ${station.latitude.toFixed(4)}, ${station.longitude.toFixed(4)}
                </div>
            </div>
            <div class="station-actions">
                <button class="btn btn-secondary" onclick="toggleStation('${station.station_id}', ${!station.active})">
                    ${station.active ? 'Deactivate' : 'Activate'}
                </button>
                <button class="btn btn-danger" onclick="deleteStation('${station.station_id}', '${station.name}')">
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

function toggleStation(stationId, newStatus) {
    if (!confirm(`${newStatus ? 'Activate' : 'Deactivate'} station ${stationId}?`)) return;
    
    fetch(`/api/admin/stations/${stationId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey
        },
        body: JSON.stringify({ active: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage('Error: ' + data.error, 'error');
        } else {
            showMessage('Station updated successfully', 'success');
            loadStations();
            refreshData();
        }
    })
    .catch(error => {
        showMessage('Failed to update station: ' + error.message, 'error');
    });
}

function deleteStation(stationId, stationName) {
    if (!confirm(`Delete station "${stationName}" (${stationId})? This cannot be undone.`)) return;
    
    fetch(`/api/admin/stations/${stationId}`, {
        method: 'DELETE',
        headers: { 'X-Admin-Key': adminKey }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage('Error: ' + data.error, 'error');
        } else {
            showMessage('Station deleted successfully', 'success');
            loadStations();
            refreshData();
        }
    })
    .catch(error => {
        showMessage('Failed to delete station: ' + error.message, 'error');
    });
}

function showMessage(message, type) {
    const container = document.getElementById('messageContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    container.innerHTML = '';
    container.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Form submission
document.getElementById('addStationForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const stationData = {
        station_id: formData.get('stationId'),
        name: formData.get('stationName'),
        city: formData.get('stationCity'),
        latitude: parseFloat(formData.get('stationLat')),
        longitude: parseFloat(formData.get('stationLon')),
        active: formData.get('stationActive') === 'true'
    };
    
    fetch('/api/admin/stations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey
        },
        body: JSON.stringify(stationData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage('Error: ' + data.error, 'error');
        } else {
            showMessage('Station added successfully!', 'success');
            e.target.reset();
            loadStations();
            refreshData();
        }
    })
    .catch(error => {
        showMessage('Failed to add station: ' + error.message, 'error');
    });
});

// Auto-auth if admin key is in URL
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('admin_key')) {
    document.getElementById('adminKey').value = urlParams.get('admin_key');
    authenticate();
}
        '''
    
    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Run the admin API server"""
        logger.info(f"Starting Admin API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)