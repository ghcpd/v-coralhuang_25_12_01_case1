import os
import sys
import pytest

# Add src to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_PATH = os.path.join(PROJECT_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from config import TestConfig  # noqa: E402
from dashboard_improved import create_app  # noqa: E402


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()
