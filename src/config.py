"""
Configuration for the improved dashboard application
Includes cache, API, and CORS settings
"""
import os
from datetime import timedelta


class Config:
    """Base configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Cache settings
    CACHE_TYPE = 'SimpleCache'  # Use SimpleCache for development, Redis for production
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default cache timeout
    CACHE_KEY_PREFIX = 'sales_dashboard_'
    
    # API settings
    API_RATE_LIMIT = '100/hour'  # Rate limiting for API endpoints
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    
    # Data settings
    DATA_FILE_PATH = os.path.join('data', 'sales_data.csv')
    
    # Export settings
    EXPORT_MAX_ROWS = 10000  # Maximum rows for CSV export
    
    # Auto-refresh settings
    AUTO_REFRESH_INTERVALS = [30, 60, 300]  # Available intervals in seconds: 30s, 1min, 5min
    DEFAULT_AUTO_REFRESH = 60  # Default: 1 minute
    
    # Performance settings
    API_RESPONSE_TIMEOUT = 200  # Target response time in milliseconds
    CACHE_HIT_TARGET = 0.7  # Target 70%+ cache hit rate
    
    # Pagination
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 1000


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    CACHE_TYPE = 'SimpleCache'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    CACHE_REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    CACHE_REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 1  # Short timeout for tests
    DATA_FILE_PATH = os.path.join('tests', 'fixtures', 'test_sales_data.csv')


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
