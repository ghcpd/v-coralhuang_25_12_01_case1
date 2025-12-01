import os
import pytest

from flask_caching import Cache

from data_service_improved import (
    DataServiceImproved,
    aggregate_by_date,
    get_cached_sales_data,
)


data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sales_data.csv')
data_service = DataServiceImproved(data_path)


def test_filter_by_region_product():
    filters = {"regions": ["Beijing"], "products": ["Laptop"]}
    chart = data_service.chart_data(filters)
    assert chart["summary"]["total_records"] > 0
    # All labels/datasets belong to Beijing - Laptop
    for ds in chart["datasets"]:
        assert "Beijing" in ds["label"]
        assert "Laptop" in ds["label"]


def test_date_range_filter():
    filters = {"start_date": "2024-11-01", "end_date": "2024-11-02"}
    chart = data_service.chart_data(filters)
    # labels should all be within range
    for label in chart["labels"]:
        assert "2024-11-01" <= label <= "2024-11-02"


def test_aggregate_by_week():
    records = data_service.load_data()
    weekly = aggregate_by_date(records, group_by="week")
    assert len(weekly) > 0
    # Date format is YYYY-MM-DD
    for entry in weekly:
        assert "date" in entry
        assert len(entry["date"]) == 10


def test_preview_in_chart_data():
    chart = data_service.chart_data({})
    preview = chart.get("preview", [])
    assert len(preview) <= 10
    if preview:
        assert {"date", "region", "product", "sales_amount", "quantity"}.issubset(preview[0].keys())


def test_get_cached_sales_data():
    class SimpleCache:
        def __init__(self):
            self.store = {}

        def get(self, key):
            return self.store.get(key)

        def set(self, key, value, timeout=None):
            self.store[key] = value

    cache = SimpleCache()
    counter = {"count": 0}

    def compute():
        counter["count"] += 1
        return {"foo": "bar"}

    filters = {"regions": ["Beijing"], "products": []}
    first = get_cached_sales_data(cache, filters, compute)
    second = get_cached_sales_data(cache, filters, compute)
    assert first == second == {"foo": "bar"}
    assert counter["count"] == 1
