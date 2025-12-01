# Sales Dashboard (Improved)

This repository contains an improved sales dashboard with interactive features, AJAX endpoints, multi-select filters, and an export API.

Quick start
- Ensure Python 3.8+
- Create and activate a virtual environment
- Install dependencies: pip install -r requirements.txt -r requirements-dev.txt
- Run the Flask app: python -m src.dashboard_improved
- Run tests: ./run_tests.sh (or .\run_tests.ps1)

API
- GET /api/filters - returns available regions/products and min/max dates
- GET /api/sales - returns Chart.js formatted data with query params regions[], products[], start_date, end_date
- GET /api/export - returns CSV of filtered records
