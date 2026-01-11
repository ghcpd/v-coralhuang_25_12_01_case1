"""
Configuration for improved sales dashboard
"""
import os


class Config:
    CSV_PATH = os.environ.get("SALES_CSV_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "sales_data.csv"))
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "300"))
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    JSON_SORT_KEYS = False


# Optional test configuration
class TestConfig(Config):
    TESTING = True
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 60
