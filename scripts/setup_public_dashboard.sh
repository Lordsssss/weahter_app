#!/bin/bash

# Wait for Grafana to be ready
echo "Waiting for Grafana to be ready..."
until curl -s http://localhost:3000/api/health > /dev/null; do
    echo "Waiting for Grafana..."
    sleep 2
done

echo "Grafana is ready. Setting up public dashboard access..."

# Login to get session
SESSION=$(curl -s -X POST -H "Content-Type: application/json" -d '{"user":"admin","password":"admin123"}' http://localhost:3000/login -c /tmp/grafana_cookies.txt)

# Create service account
echo "Creating service account for kiosk mode..."
SA_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -b /tmp/grafana_cookies.txt \
  -d '{"name":"kiosk-viewer","role":"Viewer","isDisabled":false}' \
  http://localhost:3000/api/serviceaccounts)

SA_ID=$(echo $SA_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*')

if [ -n "$SA_ID" ]; then
    echo "Service account created with ID: $SA_ID"
    
    # Create service account token
    TOKEN_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -b /tmp/grafana_cookies.txt \
      -d '{"name":"kiosk-token","role":"Viewer"}' \
      http://localhost:3000/api/serviceaccounts/$SA_ID/tokens)
    
    TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"key":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        echo "Service account token created: $TOKEN"
        echo "Token saved to /tmp/kiosk_token.txt"
        echo $TOKEN > /tmp/kiosk_token.txt
    fi
fi

echo "Setup complete!"