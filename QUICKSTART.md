# 🚀 Quick Start Guide

Get the interactive sales dashboard running in 3 simple steps!

## Step 1: Install Dependencies

### Windows (PowerShell)
```powershell
# From project root directory
pip install -r requirements.txt
```

### Linux/Mac
```bash
# From project root directory
pip install -r requirements.txt
```

## Step 2: Run the Application

```bash
# Navigate to src directory
cd src

# Start the Flask server
python dashboard_improved.py
```

You should see:
```
🚀 Starting Improved Sales Dashboard
================================================================================
Environment: development
Cache Type: SimpleCache
...
 * Running on http://127.0.0.1:5000
```

## Step 3: Open Your Browser

Navigate to: **http://localhost:5000**

## 🎉 You're Done!

The interactive dashboard should now be running. Try these features:

1. **Multi-Select Filters** - Select multiple regions or products
2. **Date Range Picker** - Choose custom date ranges
3. **Compare Mode** - Compare by region or product
4. **Auto-Refresh** - Enable automatic data updates
5. **Export CSV** - Download filtered data
6. **Interactive Charts** - Zoom, pan, and hover on the chart

## 🧪 Run Tests (Optional)

### Windows
```powershell
.\run_tests.ps1
```

### Linux/Mac
```bash
chmod +x run_tests.sh
./run_tests.sh
```

## 📚 Need More Help?

- Read the full [README.md](README.md)
- Check API documentation in README
- View code comments in source files

## 🐛 Troubleshooting

**Port already in use?**
```python
# Edit src/dashboard_improved.py, line ~300
app.run(debug=True, port=5001)  # Change port
```

**Module not found?**
```bash
pip install -r requirements.txt
```

**Template not found?**
```bash
# Make sure you're in the src directory
cd src
python dashboard_improved.py
```

---

**Enjoy your new interactive dashboard! 🎊**
