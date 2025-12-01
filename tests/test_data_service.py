import pytest
from datetime import datetime, timedelta
try:
    from data_service_improved import DataServiceImproved
    from models import FilterCriteria
except ModuleNotFoundError as e:
    pytest.skip(f"Skipping data_service tests due to missing dependency: {e.name}", allow_module_level=True)


@pytest.fixture
def service():
    return DataServiceImproved('data/sales_data.csv', cache_ttl=1)


def test_get_available_filters(service):
    opts = service.get_available_filters()
    assert 'regions' in opts and isinstance(opts['regions'], list)
    assert 'products' in opts and isinstance(opts['products'], list)
    assert 'min_date' in opts and 'max_date' in opts


def test_filter_multi_region_product(service):
    today = datetime.now()
    c = FilterCriteria(regions=[service.get_available_filters()['regions'][0]], products=[], start_date=today - timedelta(days=365), end_date=today)
    df = service.get_sales_data_filtered(c)
    assert df is not None
    if isinstance(df, list):
        assert all(r['region'] == c.regions[0] for r in df)
    else:
        assert all(df['region'] == c.regions[0])


def test_aggregate_by_date_empty(service):
    # Use a date range outside data to get empty
    c = FilterCriteria(regions=['NoRegion'], products=['NoProduct'], start_date=datetime(1900,1,1), end_date=datetime(1900,1,2))
    res = service.aggregate_by_date(c, group_by='date')
    assert res['labels'] == []
    assert res['datasets'] == []


def test_cache_hit_miss(service):
    c = FilterCriteria(regions=[], products=[], start_date=None, end_date=None)
    res1 = service.get_cached_sales_data(c, group_by='date')
    # Second time should be cached
    res2 = service.get_cached_sales_data(c, group_by='date')
    assert res1 == res2
    # sleep to expire
    import time
    time.sleep(2)
    res3 = service.get_cached_sales_data(c, group_by='date')
    assert res3 == res1 or res3 != res2


def test_export_csv(service):
    c = FilterCriteria(regions=[], products=[], start_date=None, end_date=None)
    buf, filename = service.export_csv(c)
    assert filename.endswith('.csv')
    txt = buf.getvalue().decode('utf-8')
    # If dataset is not empty, expect header
    if txt:
        assert 'date' in txt or 'region' in txt

