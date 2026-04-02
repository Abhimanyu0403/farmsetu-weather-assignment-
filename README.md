# FarmSetu Weather Assignment

A Django-based application that ingests, parses, stores, and serves UK Met Office climate datasets through REST APIs and a simple visualization dashboard.

---

## Overview

This project fetches summarized climate data from the UK Met Office, processes both date-based and ranked datasets, stores them in a PostgreSQL database, and exposes them via APIs and a frontend dashboard.

---

## Features

- Import datasets from UK Met Office
- Parse structured climate data (date and ranked formats)
- Store data in PostgreSQL
- REST APIs using Django REST Framework
- Dashboard for data visualization (charts and tables)
- Docker-based local development setup
- Unit tests for parser, importer, and APIs

---

## Tech Stack

- Backend: Django, Django REST Framework
- Database: PostgreSQL
- Frontend: Django Templates, Vanilla JavaScript
- Charts: Chart.js
- Containerization: Docker, Docker Compose

---

## Project Structure


config/ Django project configuration
climate/ Core application
├── api.py API endpoints
├── models.py Database models
├── services/ Parsing and import logic
├── serializers.py DRF serializers
├── constants.py Region and parameter definitions
├── templates/ Dashboard HTML
├── static/ Frontend JavaScript
├── tests/ Test suite


---

## Setup Instructions

### 1. Clone the repository


git clone <repository-url>
cd farmsetu-weather-assignment


### 2. Configure environment variables


cp .env.example .env


Update values if required.

### 3. Start services


docker compose up --build


### 4. Apply migrations


docker compose exec web python manage.py migrate


### 5. Access the application

- Dashboard: http://127.0.0.1:8000/
- API: http://127.0.0.1:8000/api/

---

## API Endpoints

### Load Dataset

POST /api/datasets/load/

Example request:


{
"region_code": "UK",
"region_name": "United Kingdom",
"parameter_code": "Tmean",
"parameter_name": "Mean Temperature",
"order_type": "date"
}


---

### List Datasets

GET /api/datasets/

---

### Observations

GET /api/observations/?dataset_id=1&from_year=2000&to_year=2010

---

### Rankings

GET /api/rankings/?dataset_id=2&period_code=ann&limit=10

---

### Options

GET /api/options/

---

## Dashboard

The dashboard allows:

- Importing datasets
- Viewing time-series data for date-based datasets
- Viewing ranked statistics
- Switching between periods
- Visualizing data using charts and tables

---

## Notes

- Some region and parameter combinations are not available from the Met Office source.
- In such cases, the system returns a user-friendly error message.

---

## Running Tests


docker compose exec web python manage.py test


---

## Docker Services

- web: Django application
- db: PostgreSQL database

---

## Design Decisions

- Bulk insertion used for efficient dataset imports
- Clear separation between parsing, import logic, and API layers
- Function-based API views for simplicity
- Frontend interacts exclusively through API endpoints
- Graceful handling of missing upstream datasets

---

## Author

Pranav Sonawane