#!/bin/bash

# Export Grafana dashboards to local filesystem for git versioning
# Usage: ./scripts/export_dashboards.sh

cd "$(dirname "$0")/.."

echo "Exporting Grafana dashboards..."

# Check if Grafana is running
if ! curl -s http://localhost:3002/api/health > /dev/null; then
    echo "Error: Grafana is not accessible on port 3002"
    echo "Make sure the containers are running: docker-compose up -d"
    exit 1
fi

# Run the Python export script
python3 scripts/export_dashboards.py

echo ""
echo "Dashboard export complete!"
echo ""
echo "To commit dashboard changes:"
echo "  git add grafana/dashboards/"
echo "  git commit -m 'Update Grafana dashboards'"
echo "  git push"