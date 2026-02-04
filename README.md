# Sales Dashboard - Improved

This project modernizes the Sales Dashboard to support interactive filters, AJAX updates, and Chart.js visualizations.

## Setup
- Python 3.8+
- Install requirements:
  - pip install -r requirements.txt -r requirements-dev.txt

## Run app (dev)
- python -m src.dashboard_improved

## Tests
- PowerShell: ./run_tests.ps1
- Bash: ./run_tests.sh

## API
- GET /api/filters -> returns regions, products, start/end date
- GET /api/sales -> params: regions[], products[], start_date, end_date, group_by
- GET /api/export -> CSV download

## Notes
- Backward compatible: old files untouched
- Caching: SimpleCache (5 minutes) by default
- Frontend uses CDN for Chart.js, Choices.js, Flatpickr for demo
