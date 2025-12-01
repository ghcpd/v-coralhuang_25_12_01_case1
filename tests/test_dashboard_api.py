import pytest
from src.dashboard_improved import app as dashboard_app


@pytest.fixture
def client():
    dashboard_app.testing = True
    with dashboard_app.test_client() as client:
        yield client


def test_get_filters(client):
    resp = client.get('/api/filters')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'regions' in data and 'products' in data


def test_get_sales_endpoint_basic(client):
    resp = client.get('/api/sales')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'labels' in data and 'datasets' in data and 'summary' in data


def test_export_csv(client):
    resp = client.get('/api/export')
    assert resp.status_code == 200
    assert 'text/csv' in resp.content_type
