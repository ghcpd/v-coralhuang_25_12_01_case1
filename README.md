# Interactive Sales Dashboard (Improved)

Modernized sales dashboard with multi-select filters, custom date ranges, interactive Chart.js visualizations, AJAX updates, caching, and auto-refresh.

## 🚀 Features
- Multi-region & multi-product filtering (Choices.js)
- Custom date range picker (Flatpickr)
- Interactive Chart.js line chart with zoom/pan & tooltips
- Debounced AJAX updates (<300ms) with loading indicator
- Auto-refresh (30s/1m/5m) with pause on tab blur
- CSV export for current filters
- Flask-Caching (in-memory) for faster responses

## 📁 Project Structure
```
src/
  dashboard.py                # Legacy (unchanged)
  data_service.py             # Legacy (unchanged)
  dashboard_improved.py       # NEW Flask app & APIs
  data_service_improved.py    # NEW filtering/aggregation/caching
  config.py                   # NEW config
  templates/dashboard_improved.html
  static/js/dashboard.js
  static/css/style.css
 tests/
  test_dashboard_api.py
  test_data_service.py
run_tests.ps1 / run_tests.sh  # Test runner
requirements.txt / requirements-dev.txt
```

## 🧩 Setup & Run
```powershell
# from repo root
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# run improved app
$env:FLASK_APP="src/dashboard_improved.py"; flask run
# open http://localhost:5000
```
> On Unix: `export FLASK_APP=src/dashboard_improved.py && flask run`

## 🔌 API
- `GET /api/filters` → `{ regions, products, date_range:{min,max}, group_by_options }`
- `GET /api/sales` params: `regions[]`, `products[]`, `start_date`, `end_date`, `group_by=day|week|month`
  - Returns `{ labels, datasets, summary, preview }` (Chart.js format)
- `GET /api/export` same params → CSV download

## 🧪 Tests
```powershell
powershell -ExecutionPolicy Bypass -File run_tests.ps1
# or
./run_tests.sh
```
- Coverage (improved modules): **93%**

## Notes
- Uses pure-Python aggregation (no pandas) for compatibility
- Legacy endpoints/files remain untouched for backward compatibility
- CORS is open (`*`) by default; adjust in `config.py`
