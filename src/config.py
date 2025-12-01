"""
Configuration settings for the enhanced dashboard application
Handles caching, CORS, and API settings
"""
import os
from datetime import timedelta

# Flask Configuration
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
TESTING = os.getenv('TESTING', 'False').lower() == 'true'
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 5000))

# Cache Configuration (Flask-Caching)
CACHE_TYPE = 'simple'  # simple in-memory cache
CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default TTL
CACHE_CONFIG = {
    'CACHE_TYPE': CACHE_TYPE,
    'CACHE_DEFAULT_TIMEOUT': CACHE_DEFAULT_TIMEOUT,
}

# Cache keys for different data types
CACHE_REGIONS_KEY = 'regions'
CACHE_PRODUCTS_KEY = 'products'
CACHE_DATE_RANGES_KEY = 'date_ranges'
CACHE_SALES_DATA_KEY = 'sales_data:{regions}:{products}:{start}:{end}:{group_by}'

# CORS Configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
CORS_ALLOW_HEADERS = ['Content-Type', 'Accept']
CORS_METHODS = ['GET', 'POST', 'OPTIONS']

# API Configuration
API_VERSION = 'v1'
API_RESPONSE_TIMEOUT = 10  # seconds
API_MAX_RECORDS = 10000  # Maximum records per API response

# Data Aggregation Settings
AGGREGATION_INTERVALS = ['daily', 'weekly', 'monthly']
DEFAULT_AGGREGATION = 'daily'

# Performance Settings
DEBOUNCE_DELAY = 300  # milliseconds (300ms)
AUTO_REFRESH_INTERVALS = [30, 60, 300]  # seconds (30s, 1min, 5min)
DEFAULT_AUTO_REFRESH = 60  # Default 1 minute

# Export Settings
EXPORT_FORMATS = ['csv', 'json']
DEFAULT_EXPORT_FORMAT = 'csv'
EXPORT_MAX_ROWS = 50000

# Data Service Settings
DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sales_data.csv')
CACHE_HIT_RATIO_TARGET = 0.70  # 70% cache hit ratio target
CACHE_EXPIRATION_SECONDS = 300  # 5 minutes

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
