import os
import time

from data_service_improved import DataServiceImproved

data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sales_data.csv')
expected_service = DataServiceImproved(data_path)


def test_filters_endpoint(client):
    resp = client.get('/api/filters')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'regions' in data and 'products' in data and 'date_range' in data
    assert isinstance(data['regions'], list)
    assert isinstance(data['products'], list)


def test_sales_endpoint_default(client):
    start = time.perf_counter()
    resp = client.get('/api/sales')
    duration = time.perf_counter() - start
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'labels' in data and 'datasets' in data and 'summary' in data
    assert duration < 1.0  # basic performance check


def test_sales_filter_region(client):
    resp = client.get('/api/sales?regions=Beijing')
    assert resp.status_code == 200
    data = resp.get_json()
    summary = data['summary']

    expected = expected_service.chart_data({'regions': ['Beijing']})['summary']
    assert summary['total_records'] == expected['total_records']
    assert summary['total_sales'] == expected['total_sales']


def test_export_endpoint(client):
    resp = client.get('/api/export?products=Laptop')
    assert resp.status_code == 200
    assert resp.mimetype == 'text/csv'
    content = resp.data.decode('utf-8').splitlines()
    assert content[0].startswith('date,region,product')


def test_invalid_date_returns_400(client):
    resp = client.get('/api/sales?start_date=2024-13-01')
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data
