import os
import sys
import pytest

THIS_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(THIS_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

@pytest.fixture
def client():
    try:
        from dashboard_improved import app as dashboard_app
    except ModuleNotFoundError as e:
        pytest.skip(f"Missing dependency {e.name}. Run: pip install -r requirements.txt")
    dashboard_app.config['TESTING'] = True
    with dashboard_app.test_client() as client:
        yield client
