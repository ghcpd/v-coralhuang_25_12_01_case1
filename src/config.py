"""
Config file for improved dashboard
"""
from datetime import timedelta

DEBUG = True
CACHE_TYPE = 'SimpleCache'  # Fallback if Flask-Caching not configured
CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
CORS_ORIGINS = '*'
EXPORT_CSV_FILENAME = 'sales_export.csv'


def get_cache_config():
    return {
        'CACHE_TYPE': CACHE_TYPE,
        'CACHE_DEFAULT_TIMEOUT': CACHE_DEFAULT_TIMEOUT,
    }
