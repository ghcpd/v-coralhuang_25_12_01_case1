import pytest
import sys
from pathlib import Path
# Ensure project root is in sys.path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.dashboard_improved import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_filters_endpoint(client):
    res = client.get('/api/filters')
    assert res.status_code == 200
    data = res.get_json()
    assert 'regions' in data and 'products' in data


def test_sales_endpoint_basic(client):
    res = client.get('/api/sales')
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, dict)
    assert 'labels' in data and 'datasets' in data


def test_export_endpoint(client):
    res = client.get('/api/export')
    assert res.status_code == 200
    assert res.content_type.startswith('text/csv')
