"""
Improved Data Service implementing multi-dimension filtering, aggregation and caching
"""
from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import hashlib
import json
import time

from .models import FilterCriteria, SalesRecord
from .config import CSV_DATA_PATH, CACHE_DEFAULT_TIMEOUT


def _to_cache_key(criteria: FilterCriteria, group_by: str = 'date') -> str:
    obj = {
        'regions': sorted(criteria.regions or []),
        'products': sorted(criteria.products or []),
        'start_date': criteria.start_date.strftime('%Y-%m-%d') if criteria.start_date else None,
        'end_date': criteria.end_date.strftime('%Y-%m-%d') if criteria.end_date else None,
        'group_by': group_by
    }
    s = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


class SimpleCache:
    """A minimal TTL cache used by the data service for cross-request caching in-process."""

    def __init__(self, default_ttl: int = CACHE_DEFAULT_TIMEOUT):
        self._store: Dict[str, Any] = {}
        self._ttl = default_ttl

    def set(self, key: str, value: Any):
        self._store[key] = (time.time() + self._ttl, value)

    def get(self, key: str):
        found = self._store.get(key)
        if not found:
            return None
        expires, value = found
        if time.time() > expires:
            # expire
            del self._store[key]
            return None
        return value

    def clear(self):
        self._store.clear()


class DataServiceImproved:
    """Improved data service using pandas for efficient filtering and aggregation."""

    def __init__(self, csv_file_path: str = CSV_DATA_PATH):
        self.csv_file_path = csv_file_path
        self._df = None
        self._cache = SimpleCache()

    def _load_df(self):
        if self._df is None:
            self._df = pd.read_csv(self.csv_file_path, parse_dates=['date'])
        return self._df

    def get_sales_data_filtered(self, criteria: FilterCriteria) -> pd.DataFrame:
        """Return a pandas DataFrame filtered by the provided criteria."""
        df = self._load_df()
        mask = pd.Series([True] * len(df))

        if criteria.regions:
            mask &= df['region'].isin(criteria.regions)
        if criteria.products:
            mask &= df['product'].isin(criteria.products)
        if criteria.start_date:
            mask &= df['date'] >= pd.to_datetime(criteria.start_date)
        if criteria.end_date:
            mask &= df['date'] <= pd.to_datetime(criteria.end_date)

        return df[mask].copy()

    def aggregate_by_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate provided DataFrame by date summing sales_amount and quantity."""
        if df.empty:
            return df
        out = (df.groupby('date')
                .agg({'sales_amount': 'sum', 'quantity': 'sum'})
                .reset_index()
                .sort_values('date'))
        return out

    def get_comparison_data(self, criteria: FilterCriteria, group_by: str = 'date') -> Dict[str, Any]:
        """Build a Chart.js compatible response structure.

        group_by is currently only supporting 'date'.
        """
        key = _to_cache_key(criteria, group_by)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        df_filtered = self.get_sales_data_filtered(criteria)
        # If empty, return empty structure
        if df_filtered.empty:
            resp = {'labels': [], 'datasets': [], 'summary': {'total_sales': 0, 'total_quantity': 0}}
            self._cache.set(key, resp)
            return resp

        agg = self.aggregate_by_date(df_filtered)
        labels = [d.strftime('%Y-%m-%d') for d in agg['date'].tolist()]
        # Build one dataset for total sales and one for quantity to simplify visualization
        datasets = [
            {
                'label': 'Sales Amount',
                'data': agg['sales_amount'].round(2).tolist(),
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)'
            },
            {
                'label': 'Quantity',
                'data': agg['quantity'].tolist(),
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderColor': 'rgba(255, 99, 132, 1)'
            }
        ]

        summary = {
            'total_sales': float(df_filtered['sales_amount'].sum()),
            'total_quantity': int(df_filtered['quantity'].sum())
        }

        resp = {'labels': labels, 'datasets': datasets, 'summary': summary}
        self._cache.set(key, resp)
        return resp

    def get_cached_sales_data(self, criteria: FilterCriteria, group_by: str = 'date') -> Dict[str, Any]:
        """Public API, currently identical to get_comparison_data but separate for clarity."""
        return self.get_comparison_data(criteria, group_by)


def _to_records(df: pd.DataFrame) -> List[dict]:
    records = []
    for _, r in df.iterrows():
        records.append({
            'date': r['date'].strftime('%Y-%m-%d'),
            'region': r['region'],
            'product': r['product'],
            'sales_amount': float(r['sales_amount']),
            'quantity': int(r['quantity'])
        })
    return records


if __name__ == '__main__':
    # Quick manual test
    service = DataServiceImproved()
    criteria = FilterCriteria(regions=['Beijing'], products=['Laptop'])
    criteria.start_date = datetime.now() - timedelta(days=365)
    criteria.end_date = datetime.now()
    data = service.get_cached_sales_data(criteria)
    print(data)
