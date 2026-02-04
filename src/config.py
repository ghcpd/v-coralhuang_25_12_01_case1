"""
Configuration for improved dashboard
"""
from datetime import timedelta

DEBUG = True
CACHE_TYPE = 'SimpleCache'  # For demo/testing
CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
CORS_ORIGINS = ['*']
DATA_CSV_PATH = 'data/sales_data.csv'

# API pagination/limits
MAX_RECORDS = 10000

# Debounce constant (frontend)
AJAX_DEBOUNCE_MS = 300
