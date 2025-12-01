# Quick Start Guide

## 🎯 Get Started in 5 Minutes

### Option A: Fastest Way (Automated)

#### Windows PowerShell
```powershell
# Run once - sets up everything and runs tests
.\run_tests.ps1
```

#### Linux/Mac Bash
```bash
# Make executable and run
chmod +x run_tests.sh
./run_tests.sh
```

**What this does:**
- ✓ Checks Python version (3.8+)
- ✓ Creates virtual environment
- ✓ Installs all dependencies
- ✓ Runs complete test suite
- ✓ Generates coverage report

---

### Option B: Manual Setup

#### Step 1: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 3: Run the Dashboard

```bash
python src/dashboard_improved.py
```

#### Step 4: Open in Browser

Visit: http://localhost:5000

---

## 📊 First-Time Usage

1. **Wait for page to load** (~2 seconds initially)
2. **See the dashboard** with:
   - Summary cards showing stats
   - Interactive chart
   - Filter controls on top
   - Data table below

3. **Try the filters**:
   - Click "Beijing" in regions → Chart updates instantly
   - Select multiple regions → Comparison view
   - Click "Last 7 Days" preset → Quick date range
   - Adjust aggregation to "Weekly" → See weekly totals

4. **Interact with chart**:
   - Hover over lines → See tooltips
   - Drag to pan → Explore time periods
   - Scroll to zoom → Focus on specific dates

5. **Export data**:
   - Click "Export CSV" → Download filtered data
   - Click "Download" → Save chart as PNG image

---

## 🔧 Configuration

### Change Default Port

Edit `src/config.py`:
```python
PORT = 5001  # Change from 5000 to 5001
```

### Adjust Cache Time

Edit `src/config.py`:
```python
CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes instead of 5
```

### Change Auto-Refresh Interval

Edit `src/config.py`:
```python
AUTO_REFRESH_INTERVALS = [60, 300, 600]  # 1min, 5min, 10min
```

---

## 🧪 Running Tests

### Full Test Suite with Coverage

```bash
python -m pytest tests/ -v --cov=src
```

### Specific Test Category

```bash
# API tests only
python -m pytest tests/test_dashboard_api.py -v

# Data service tests only
python -m pytest tests/test_data_service.py -v

# Filtering tests only
python -m pytest tests/test_data_service.py::TestBasicFiltering -v
```

### View Coverage Report

```bash
# Generate HTML report
python -m pytest tests/ --cov=src --cov-report=html

# Open in browser:
# Windows: start htmlcov/index.html
# Linux/Mac: open htmlcov/index.html
```

---

## 🐛 Troubleshooting

### Issue: Port 5000 Already in Use

**Solution:**
```python
# In src/config.py, change:
PORT = 5001
```

Or run with environment variable:
```bash
set PORT=5001  # Windows
python src/dashboard_improved.py

# Or Linux/Mac:
PORT=5001 python src/dashboard_improved.py
```

### Issue: Import Errors for Flask

**Solution:** Verify dependencies installed:
```bash
pip install Flask==3.0.0
pip install Flask-CORS==4.0.0
pip install pandas==2.1.0
```

### Issue: Tests Won't Run

**Solution:** Install test dependencies:
```bash
pip install -r requirements-dev.txt
```

### Issue: Virtual Environment Won't Activate

**Windows:**
```powershell
# Try:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
# Try:
source venv/bin/activate
```

---

## 📱 Testing the API Directly

### Using cURL

```bash
# Get filter options
curl http://localhost:5000/api/v1/filters

# Get sales data
curl "http://localhost:5000/api/v1/sales?regions[]=Beijing&start_date=2024-11-01"

# Export CSV
curl "http://localhost:5000/api/v1/export?regions[]=Beijing" -o export.csv

# Cache stats
curl http://localhost:5000/api/v1/cache-stats
```

### Using Python

```python
import requests

# Get sales data
response = requests.get('http://localhost:5000/api/v1/sales', params={
    'regions[]': 'Beijing',
    'start_date': '2024-11-01',
    'end_date': '2024-11-30'
})

data = response.json()
print(data['data']['summary'])
```

---

## 📊 Sample API Response

```json
{
  "status": "success",
  "data": {
    "chart": {
      "labels": ["2024-11-01", "2024-11-02", ...],
      "datasets": [
        {
          "label": "Total Sales (USD)",
          "data": [250000, 320000, ...],
          "borderColor": "#007bff"
        }
      ]
    },
    "summary": {
      "total_sales": 5250000.00,
      "total_quantity": 1250,
      "record_count": 32,
      "average_sales": 164062.50
    },
    "from_cache": false
  }
}
```

---

## 🎓 Key Differences from Original

### Original Dashboard
- Requires page reload for filter changes
- Single selection only
- Static table view
- 3-5 second wait time

### Enhanced Dashboard
- Instant updates with AJAX
- Multi-select filters
- Interactive charts
- < 1 second response time
- Auto-refresh capability
- CSV export
- Cache performance metrics

---

## 📚 Learn More

See **README.md** for:
- Complete API documentation
- Configuration guide
- Advanced features
- Performance optimization tips
- Troubleshooting guide

---

## ✅ Checklist

- [ ] Python 3.8+ installed
- [ ] Project directory accessible
- [ ] Dependencies installed
- [ ] Dashboard running on http://localhost:5000
- [ ] Can interact with filters
- [ ] Charts render correctly
- [ ] Tests passing

---

## 🚀 You're Ready!

The enhanced dashboard is now running and ready for use.

**Next steps:**
1. Explore the interactive features
2. Review the comprehensive README.md
3. Check out the test suite
4. Customize configuration as needed

**Questions?** See README.md or check IMPLEMENTATION_SUMMARY.md for complete details.

---

**Version**: 2.0 (Enhanced)  
**Status**: Ready to Use  
**Last Updated**: December 2024
