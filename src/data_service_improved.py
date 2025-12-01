"""
Improved Data Service with multi-dimension filtering, aggregation and caching
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import csv
import io
try:
    import pandas as pd
except Exception:
    pd = None
import threading
import time

from models import SalesRecord, FilterCriteria, ChartData


class SimpleTTLCache:
    """A tiny thread-safe key->(value, expires_at) cache for tests and local use."""
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.lock = threading.RLock()
        self._store = {}

    def get(self, key: str):
        with self.lock:
            entry = self._store.get(key)
            if not entry:
                return None
            value, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value):
        with self.lock:
            self._store[key] = (value, time.time() + self.ttl)

    def clear(self):
        with self.lock:
            self._store.clear()


class DataServiceImproved:
    """Data service optimized to use pandas and support multi-select, aggregations.

    Public API methods:
    - get_sales_data_filtered(criteria)
    - aggregate_by_date(criteria, group_by='date')
    - get_comparison_data(criteria, compare_by='region')
    - get_cached_sales_data(criteria)
    - get_available_filters()
    - export_csv(criteria)
    """

    def __init__(self, csv_file_path: str, cache_ttl: int = 300):
        self.csv_file_path = csv_file_path
        self.cache = SimpleTTLCache(ttl_seconds=cache_ttl)
        self._df = None
        self._rows = None
        self._load_dataframe()

    def _load_dataframe(self) -> None:
        """Load CSV into pandas DataFrame and do light normalization."""
        if self._df is not None:
            return
        try:
            import pandas as pd
        except Exception:
            pd = None
        # Use pandas for fast ops when available
        if pd is not None:
            self._df = pd.read_csv(self.csv_file_path, parse_dates=['date'])
            # Ensure types
            self._df['product'] = self._df['product'].astype(str)
            self._df['region'] = self._df['region'].astype(str)
            self._df['sales_amount'] = self._df['sales_amount'].astype(float)
            self._df['quantity'] = self._df['quantity'].astype(int)
            return
        # Fallback: simple list of dicts
        rows = []
        with open(self.csv_file_path, 'r', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                # Normalize
                rows.append({
                    'date': datetime.strptime(row['date'], '%Y-%m-%d'),
                    'region': row['region'],
                    'product': row['product'],
                    'sales_amount': float(row['sales_amount']),
                    'quantity': int(row['quantity'])
                })
        self._rows = rows
        # End of fallback. pandas types already set above when pandas available.

    def _criteria_key(self, criteria: FilterCriteria) -> str:
        # Key used for caching - deterministic
        r = ','.join(sorted(criteria.regions)) if criteria.regions else ''
        p = ','.join(sorted(criteria.products)) if criteria.products else ''
        s = criteria.start_date.strftime('%Y-%m-%d') if criteria.start_date else ''
        e = criteria.end_date.strftime('%Y-%m-%d') if criteria.end_date else ''
        return f"r={r}|p={p}|s={s}|e={e}"

    def get_sales_data_filtered(self, criteria: FilterCriteria) -> pd.DataFrame:
        """Return a pandas DataFrame filtered by multi-select criteria and date range."""
        if pd is not None and self._df is not None:
            df = self._df.copy()
            if criteria.regions:
                df = df[df['region'].isin(criteria.regions)]
            if criteria.products:
                df = df[df['product'].isin(criteria.products)]
            if criteria.start_date:
                df = df[df['date'] >= pd.to_datetime(criteria.start_date)]
            if criteria.end_date:
                df = df[df['date'] <= pd.to_datetime(criteria.end_date)]
            return df
        # Fallback filtering on list of dicts
        rows = self._rows or []
        def in_range(dt):
            if criteria.start_date and dt < criteria.start_date:
                return False
            if criteria.end_date and dt > criteria.end_date:
                return False
            return True
        out = [r for r in rows if (not criteria.regions or r['region'] in criteria.regions) and (not criteria.products or r['product'] in criteria.products) and in_range(r['date'])]
        return out
        if criteria.regions:
            df = df[df['region'].isin(criteria.regions)]
        if criteria.products:
            df = df[df['product'].isin(criteria.products)]
        if criteria.start_date:
            df = df[df['date'] >= pd.to_datetime(criteria.start_date)]
        if criteria.end_date:
            df = df[df['date'] <= pd.to_datetime(criteria.end_date)]
        return df

    def aggregate_by_date(self, criteria: FilterCriteria, group_by: str = 'date') -> Dict:
        """Aggregate filtered data by date or other group_by (region/product) for chart datasets."""
        if pd is not None and self._df is not None:
            df = self.get_sales_data_filtered(criteria)
            if df.empty:
                return {'labels': [], 'datasets': [], 'summary': {}}
        else:
            rows = self.get_sales_data_filtered(criteria)
            if not rows:
                return {'labels': [], 'datasets': [], 'summary': {}}

        # Group by time-series labels (date) default
        if group_by == 'date':
            if pd is not None:
                series = df.groupby(df['date'].dt.strftime('%Y-%m-%d')).agg({'sales_amount': 'sum'}).reset_index()
                labels = list(series['date'])
                data = list(series['sales_amount'])
                return {'labels': labels, 'datasets': [{'label': 'Sales Amount', 'data': data}], 'summary': {'total_sales': float(df['sales_amount'].sum()), 'records': int(len(df))}}
            # fallback
            mapping = {}
            for r in rows:
                key = r['date'].strftime('%Y-%m-%d')
                mapping[key] = mapping.get(key, 0.0) + float(r['sales_amount'])
                labels = sorted(mapping.keys())
                data = [mapping[k] for k in labels]
                return {'labels': labels, 'datasets': [{'label': 'Sales Amount', 'data': data}], 'summary': {'total_sales': sum(mapping.values()), 'records': len(rows)}}

        # Example: group by region or product to compare series
        if group_by in ('region', 'product'):
            if pd is not None:
                series = df.groupby([group_by, df['date'].dt.strftime('%Y-%m-%d')])['sales_amount'].sum().reset_index()
                labels = sorted(series['date'].unique())
                datasets = []
                for name, group in series.groupby(group_by):
                    map_dates = {d: 0.0 for d in labels}
                    for _, row in group.iterrows():
                        map_dates[row['date']] = row['sales_amount']
                    datasets.append({'label': str(name), 'data': [map_dates[d] for d in labels]})
                return {'labels': labels, 'datasets': datasets, 'summary': {'total_sales': float(df['sales_amount'].sum()), 'records': int(len(df))}}
            # fallback
            mapping = {}
            dates_set = set()
            for r in rows:
                date_key = r['date'].strftime('%Y-%m-%d')
                name = r[group_by]
                dates_set.add(date_key)
                mapping.setdefault(name, {}).setdefault(date_key, 0.0)
                mapping[name][date_key] += float(r['sales_amount'])
            labels = sorted(dates_set)
            datasets = []
            for name, mp in mapping.items():
                datasets.append({'label': str(name), 'data': [mp.get(d, 0.0) for d in labels]})
            total_sales = sum(sum(v.values()) for v in mapping.values())
            return {'labels': labels, 'datasets': datasets, 'summary': {'total_sales': float(total_sales), 'records': len(rows)}}

        # Fallback
        return {'labels': [], 'datasets': [], 'summary': {}}

    def get_comparison_data(self, criteria: FilterCriteria, compare_by: str = 'region') -> Dict:
        """Return data suitable for comparison charts where each compare_by is a dataset"""
        return self.aggregate_by_date(criteria, group_by=compare_by)

    def get_cached_sales_data(self, criteria: FilterCriteria, group_by: str = 'date') -> Dict:
        key = self._criteria_key(criteria) + f"|g={group_by}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        result = self.aggregate_by_date(criteria, group_by=group_by)
        self.cache.set(key, result)
        return result

    def get_available_filters(self) -> Dict[str, List[str]]:
        """Return available regions, products, and date ranges from dataset."""
        if pd is not None and self._df is not None:
            df = self._df
            min_date = df['date'].min().strftime('%Y-%m-%d')
            max_date = df['date'].max().strftime('%Y-%m-%d')
            return {
                'regions': sorted(df['region'].unique().tolist()),
                'products': sorted(df['product'].unique().tolist()),
                'min_date': min_date,
                'max_date': max_date
            }
        rows = self._rows or []
        if not rows:
            return {'regions': [], 'products': [], 'min_date': None, 'max_date': None}
        regions = sorted(set(r['region'] for r in rows))
        products = sorted(set(r['product'] for r in rows))
        min_date = min(r['date'] for r in rows).strftime('%Y-%m-%d')
        max_date = max(r['date'] for r in rows).strftime('%Y-%m-%d')
        return {'regions': regions, 'products': products, 'min_date': min_date, 'max_date': max_date}
        min_date = df['date'].min().strftime('%Y-%m-%d')
        max_date = df['date'].max().strftime('%Y-%m-%d')
        return {
            'regions': sorted(df['region'].unique().tolist()),
            'products': sorted(df['product'].unique().tolist()),
            'min_date': min_date,
            'max_date': max_date
        }

    def export_csv(self, criteria: FilterCriteria) -> Tuple[io.BytesIO, str]:
        """Export filtered rows to CSV bytes and return buffer and filename"""
        if pd is not None and self._df is not None:
            df = self.get_sales_data_filtered(criteria)
            buf = io.StringIO()
            if df.empty:
                buf.write('')
                return io.BytesIO(buf.getvalue().encode('utf-8')), 'empty.csv'
            df.to_csv(buf, index=False)
            return io.BytesIO(buf.getvalue().encode('utf-8')), 'sales_export.csv'
        # fallback: rows list
        rows = self.get_sales_data_filtered(criteria)
        buf = io.StringIO()
        if not rows:
            return io.BytesIO(buf.getvalue().encode('utf-8')), 'empty.csv'
        writer = csv.DictWriter(buf, fieldnames=['date', 'region', 'product', 'sales_amount', 'quantity'])
        writer.writeheader()
        for r in rows:
            writer.writerow({'date': r['date'].strftime('%Y-%m-%d'), 'region': r['region'], 'product': r['product'], 'sales_amount': r['sales_amount'], 'quantity': r['quantity']})
        return io.BytesIO(buf.getvalue().encode('utf-8')), 'sales_export.csv'


if __name__ == '__main__':
    # Simple local smoke test
    svc = DataServiceImproved('data/sales_data.csv')
    c = FilterCriteria(regions=['Beijing'], products=[], start_date=datetime.now() - timedelta(days=365), end_date=datetime.now())
    print(svc.get_cached_sales_data(c, group_by='date'))
