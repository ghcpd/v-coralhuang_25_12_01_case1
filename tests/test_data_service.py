import pytest
from datetime import datetime
from src.data_service_improved import DataServiceImproved
from src.models import FilterCriteria


def test_get_sales_data_filtered_basic():
    svc = DataServiceImproved('data/sales_data.csv')
    criteria = FilterCriteria(regions=['Beijing'])
    df = svc.get_sales_data_filtered(criteria)
    assert not df.empty
    assert all(df['region'] == 'Beijing')


def test_aggregate_by_date_and_summary():
    svc = DataServiceImproved('data/sales_data.csv')
    # use a small sample by date
    criteria = FilterCriteria()
    criteria.start_date = datetime(2024, 11, 1)
    criteria.end_date = datetime(2024, 11, 5)
    res = svc.get_cached_sales_data(criteria)
    assert 'labels' in res and isinstance(res['labels'], list)
    assert 'datasets' in res and isinstance(res['datasets'], list)
    assert 'summary' in res and 'total_sales' in res['summary']


def test_cache_hit():
    svc = DataServiceImproved('data/sales_data.csv')
    criteria = FilterCriteria(regions=['Beijing'])
    # first call should populate cache
    first = svc.get_cached_sales_data(criteria)
    second = svc.get_cached_sales_data(criteria)
    assert first == second
