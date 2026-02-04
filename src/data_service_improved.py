"""
Improved Data Service - supports multi-dimension filtering, caching, and aggregation
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import hashlib
import csv
import io
try:
    import pandas as pd
except Exception:
    pd = None  # fallback to csv-based processing for restricted environments
from flask_caching import Cache
from src.models import SalesRecord, FilterCriteria, ChartData


def _df_to_sales_records(df: Any) -> List[SalesRecord]:
    records = []
    for _, row in df.iterrows():
        records.append(SalesRecord(
            date=row['date'].to_pydatetime(),
            region=row['region'],
            product=row['product'],
            sales_amount=float(row['sales_amount']),
            quantity=int(row['quantity'])
        ))
    return records


class DataServiceImproved:
    def __init__(self, csv_path: str, cache: Optional[Cache] = None):
        self.csv_path = csv_path
        self.cache = cache
        self._df = None

    def _load_dataframe(self) -> Any:
        if self._df is None:
            if pd is not None:
                df = pd.read_csv(self.csv_path, parse_dates=['date'])
                df['date'] = pd.to_datetime(df['date']).dt.normalize()
                self._df = df
            else:
                # fallback: load into a pandas-like structure (list of dicts)
                rows = []
                with open(self.csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        rows.append({
                            'date': datetime.strptime(r['date'], '%Y-%m-%d'),
                            'region': r['region'],
                            'product': r['product'],
                            'sales_amount': float(r['sales_amount']),
                            'quantity': int(r['quantity'])
                        })
                self._df = rows
        return self._df

    def _criteria_key(self, criteria: FilterCriteria, group_by: str) -> str:
        key = {
            'regions': criteria.regions,
            'products': criteria.products,
            'start_date': criteria.start_date.strftime('%Y-%m-%d') if criteria.start_date else None,
            'end_date': criteria.end_date.strftime('%Y-%m-%d') if criteria.end_date else None,
            'group_by': group_by
        }
        key_str = str(key)
        return hashlib.sha256(key_str.encode('utf-8')).hexdigest()

    def get_cached_sales_data(self, criteria: FilterCriteria, group_by: str = 'date') -> Dict:
        """Return cached chart data if available, otherwise compute & cache."""
        key = self._criteria_key(criteria, group_by)
        if self.cache:
            cached = self.cache.get(key)
            if cached is not None:
                return cached
        data = self.get_comparison_data(criteria, group_by)
        if self.cache:
            self.cache.set(key, data)
        return data

    def get_sales_data_filtered(self, criteria: FilterCriteria) -> Any:
        """Return filtered DataFrame based on criteria. Supports multi-select filters."""
        df = self._load_dataframe()
        if pd is None:
            # df is list of dicts
            filtered = []
            for row in df:
                if criteria.regions and row['region'] not in criteria.regions:
                    continue
                if criteria.products and row['product'] not in criteria.products:
                    continue
                if criteria.start_date and row['date'] < criteria.start_date:
                    continue
                if criteria.end_date and row['date'] > criteria.end_date:
                    continue
                filtered.append(row)
            # convert to minimal DataFrame-like list
            return filtered
        else:
            mask = pd.Series(True, index=df.index)
            if criteria.regions:
                mask &= df['region'].isin(criteria.regions)
            if criteria.products:
                mask &= df['product'].isin(criteria.products)
            if criteria.start_date:
                mask &= df['date'] >= pd.to_datetime(criteria.start_date)
            if criteria.end_date:
                mask &= df['date'] <= pd.to_datetime(criteria.end_date)
            return df[mask].copy()

    def aggregate_by_date(self, df: Any, group_by: str = 'date') -> Any:
        """Aggregate a DataFrame by date or region or product and return time series for Chart.js"""
        if (pd is not None and df.empty) or (pd is None and not df):
            return []
        df = df.copy()
        if group_by == 'date':
            if pd is None:
                # list of dicts
                sums = {}
                for row in df:
                    d = row['date'].strftime('%Y-%m-%d')
                    sums[d] = sums.get(d, 0) + row['sales_amount']
                return [{'label': k, 'sales': v} for k, v in sorted(sums.items())]
            grouped = df.groupby('date', as_index=False)['sales_amount'].sum().rename(columns={'sales_amount': 'sales'})
            grouped['label'] = grouped['date'].dt.strftime('%Y-%m-%d')
            return grouped[['label', 'sales']]
        elif group_by == 'product':
            grouped = df.groupby(['product', 'date'], as_index=False)['sales_amount'].sum().rename(columns={'sales_amount': 'sales'})
            grouped['label'] = grouped['date'].dt.strftime('%Y-%m-%d')
            return grouped[['product', 'label', 'sales']]
        elif group_by == 'region':
            grouped = df.groupby(['region', 'date'], as_index=False)['sales_amount'].sum().rename(columns={'sales_amount': 'sales'})
            grouped['label'] = grouped['date'].dt.strftime('%Y-%m-%d')
            return grouped[['region', 'label', 'sales']]
        else:
            raise ValueError('Unsupported group_by')

    def get_comparison_data(self, criteria: FilterCriteria, group_by: str = 'date') -> Dict:
        """Return Chart.js compatible data (labels, datasets) based on filtering and grouping"""
        df = self.get_sales_data_filtered(criteria)
        if (pd is not None and (df is None or df.empty)) or (pd is None and not df):
            return {'labels': [], 'datasets': [], 'summary': {'total_sales': 0, 'count': 0}}

        if group_by == 'date':
            agg = self.aggregate_by_date(df, 'date')
            if pd is None:
                labels = [r['label'] for r in agg]
                sales = [r['sales'] for r in agg]
            else:
                labels = agg['label'].tolist()
                sales = agg['sales'].tolist()
            datasets = [{
                'label': 'Sales',
                'data': sales,
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)'
            }]
            return {'labels': labels, 'datasets': datasets, 'summary': {'total_sales': sum(sales), 'count': len(sales)}}

        elif group_by in ('product', 'region'):
            # Create a time series per product/region
            if pd is None:
                # df is list of dicts
                grouped = {}
                labels_set = set()
                for row in df:
                    cat = row[group_by]
                    label = row['date'].strftime('%Y-%m-%d')
                    labels_set.add(label)
                    grouped.setdefault(cat, {}).setdefault(label, 0)
                    grouped[cat][label] += row['sales_amount']
                labels = sorted(labels_set)
                datasets = []
                total = 0
                for cat, series in grouped.items():
                    data = [series.get(l, 0) for l in labels]
                    datasets.append({'label': cat, 'data': data})
                    total += sum(series.values())
                return {'labels': labels, 'datasets': datasets, 'summary': {'total_sales': total, 'count': sum(len(v) for v in grouped.values())}}
            grouped = df.groupby([group_by, 'date'], as_index=False)['sales_amount'].sum().rename(columns={'sales_amount': 'sales'})
            grouped['label'] = grouped['date'].dt.strftime('%Y-%m-%d')
            categories = grouped[group_by].unique().tolist()
            labels = sorted(grouped['label'].unique())
            series = []
            for cat in categories:
                subset = grouped[grouped[group_by] == cat]
                sales_map = dict(zip(subset['label'], subset['sales']))
                data = [sales_map.get(l, 0) for l in labels]
                series.append({'label': cat, 'data': data})
            return {'labels': labels, 'datasets': series, 'summary': {'total_sales': sum(grouped['sales']), 'count': len(grouped)}}

        else:
            raise ValueError('Unsupported group_by')


if __name__ == '__main__':
    # Sample usage
    from config import DATA_CSV_PATH
    svc = DataServiceImproved(DATA_CSV_PATH)
    crit = FilterCriteria(regions=['Beijing'], products=['Widget'])
    crit.start_date = datetime.now() - pd.Timedelta(days=30)
    crit.end_date = datetime.now()
    print(svc.get_comparison_data(crit))
