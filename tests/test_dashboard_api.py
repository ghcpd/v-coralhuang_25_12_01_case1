import io
import csv
from datetime import datetime


def test_api_filters(client):
    res = client.get('/api/filters')
    assert res.status_code == 200
    body = res.get_json()
    assert 'regions' in body and 'products' in body


def test_api_sales_basic(client):
    res = client.get('/api/sales')
    assert res.status_code == 200
    data = res.get_json()
    assert 'labels' in data and 'datasets' in data
    # Re-request to exercise caching
    res2 = client.get('/api/sales')
    assert res2.status_code == 200
    assert res2.get_json() == data


def test_api_performance(client):
    import time
    start = time.perf_counter()
    res = client.get('/api/sales')
    elapsed = time.perf_counter() - start
    assert res.status_code == 200
    # Soft performance check: assert not excessively slow in test env
    assert elapsed < 2.0


def test_api_sales_with_params(client):
    # get filters
    res = client.get('/api/filters')
    filters = res.get_json()
    regions = filters.get('regions', [])[:2]
    params = []
    for r in regions:
        params.append(('regions[]', r))
    params.append(('group_by', 'region'))
    res = client.get('/api/sales', query_string=params)
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data.get('labels'), list)
    assert isinstance(data.get('datasets'), list)


def test_api_export_csv(client):
    res = client.get('/api/export')
    assert res.status_code == 200
    # Should return CSV content
    text = res.data.decode('utf-8')
    # If not empty, first line should contain header
    if text:
        hdr = text.splitlines()[0]
        assert 'date' in hdr or 'region' in hdr
