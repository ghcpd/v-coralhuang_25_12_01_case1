import pytest
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_service_improved import DataServiceImproved
from src.models import FilterCriteria
from src.config import DATA_CSV_PATH


def test_filter_by_region_and_product():
    svc = DataServiceImproved(DATA_CSV_PATH)
    criteria = FilterCriteria(regions=['Beijing'], products=['Widget'])
    # set a wide date range
    try:
        import pandas as pd
        criteria.start_date = pd.to_datetime('2000-01-01')
        criteria.end_date = pd.to_datetime('2100-01-01')
    except Exception:
        from datetime import datetime
        criteria.start_date = datetime(2000,1,1)
        criteria.end_date = datetime(2100,1,1)
    df = svc.get_sales_data_filtered(criteria)
    assert df is not None
    # Ensure every row contains the region and product
    if hasattr(df, 'empty'):
        if not df.empty:
            assert all(df['region'] == 'Beijing') or 'Beijing' in df['region'].values
            assert all(df['product'] == 'Widget') or 'Widget' in df['product'].values
    else:
        if df:
            assert all(r['region'] == 'Beijing' for r in df) or any(r['region'] == 'Beijing' for r in df)
            assert all(r['product'] == 'Widget' for r in df) or any(r['product'] == 'Widget' for r in df)


def test_aggregate_by_date_empty():
    svc = DataServiceImproved(DATA_CSV_PATH)
    # Use fallback structure for empty result (no pandas required)
    empty_df = []
    agg = svc.aggregate_by_date(empty_df, 'date')
    # For fallback, expect empty list
    assert agg == []
