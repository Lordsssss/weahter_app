.PHONY: help install dev-install test start stop logs clean migrate

help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  test         - Test database connection"
	@echo "  start        - Start all services with Docker Compose"
	@echo "  stop         - Stop all services"
	@echo "  logs         - Show logs"
	@echo "  clean        - Clean up containers and volumes"
	@echo "  migrate      - Import CSV data to InfluxDB"
	@echo "  local-run    - Run weather monitor locally"

install:
	pip install -r requirements.txt

dev-install: install
	pip install -e .

test:
	python -m weather_monitor.cli test

start:
	docker-compose up -d

stop:
	docker-compose down

logs:
	docker-compose logs -f weather-monitor

clean:
	docker-compose down -v
	docker system prune -f

migrate:
	python scripts/import_csv_data.py weather_log.csv

local-run:
	export PYTHONPATH=src && python -m weather_monitor.cli start

build:
	docker-compose build

restart:
	docker-compose restart

status:
	docker-compose ps