"""
Improved Data Service - Multi-dimension filtering, caching, and aggregation
Addresses all issues from the original data_service.py:
1. Multi-dimension filtering support
2. Data aggregation and comparison
3. Caching mechanism for performance
4. Chart.js format output
"""
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from functools import lru_cache
import hashlib
import json

from models import SalesRecord, FilterCriteria, ChartData


class DataServiceImproved:
    """Improved data query service with caching and multi-dimension support"""
    
    def __init__(self, csv_file_path: str, cache=None):
        """
        Initialize data service
        
        Args:
            csv_file_path: Path to CSV data file
            cache: Flask-Caching cache instance (optional)
        """
        self.data_file = csv_file_path
        self.cache = cache
        self._data_cache = None  # In-memory cache for raw data
        self._cache_timestamp = None
    
    def get_sales_data_filtered(
        self, 
        regions: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SalesRecord]:
        """
        Get filtered sales data with multi-dimension support
        
        Args:
            regions: List of regions to filter (supports multiple)
            products: List of products to filter (supports multiple)
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of filtered sales records
        """
        all_records = self._load_data_cached()
        
        filtered = []
        for record in all_records:
            # Multi-dimension filtering
            if regions and record.region not in regions:
                continue
            if products and record.product not in products:
                continue
            if start_date and record.date < start_date:
                continue
            if end_date and record.date > end_date:
                continue
            filtered.append(record)
        
        return filtered
    
    def aggregate_by_date(
        self,
        records: List[SalesRecord],
        group_by: str = 'day'
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate sales data by date
        
        Args:
            records: List of sales records
            group_by: Grouping level ('day', 'week', 'month')
            
        Returns:
            Dictionary with date as key and aggregated metrics
        """
        aggregated = defaultdict(lambda: {'sales_amount': 0.0, 'quantity': 0})
        
        for record in records:
            # Format date based on grouping level
            if group_by == 'day':
                date_key = record.date.strftime('%Y-%m-%d')
            elif group_by == 'week':
                date_key = record.date.strftime('%Y-W%U')
            elif group_by == 'month':
                date_key = record.date.strftime('%Y-%m')
            else:
                date_key = record.date.strftime('%Y-%m-%d')
            
            aggregated[date_key]['sales_amount'] += record.sales_amount
            aggregated[date_key]['quantity'] += record.quantity
        
        return dict(aggregated)
    
    def get_comparison_data(
        self,
        regions: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = 'day',
        compare_by: str = 'region'
    ) -> ChartData:
        """
        Get comparison data for multiple dimensions
        
        Args:
            regions: List of regions
            products: List of products
            start_date: Start date
            end_date: End date
            group_by: Time grouping ('day', 'week', 'month')
            compare_by: Comparison dimension ('region', 'product')
            
        Returns:
            ChartData object formatted for Chart.js
        """
        records = self.get_sales_data_filtered(regions, products, start_date, end_date)
        
        # Group by comparison dimension
        comparison_groups = defaultdict(list)
        for record in records:
            if compare_by == 'region':
                comparison_groups[record.region].append(record)
            elif compare_by == 'product':
                comparison_groups[record.product].append(record)
        
        # Generate datasets for each comparison group
        datasets = []
        all_dates = set()
        
        # Color palette for different groups
        colors = [
            'rgb(54, 162, 235)',   # Blue
            'rgb(255, 99, 132)',   # Red
            'rgb(75, 192, 192)',   # Green
            'rgb(255, 159, 64)',   # Orange
            'rgb(153, 102, 255)',  # Purple
            'rgb(255, 205, 86)',   # Yellow
        ]
        
        for idx, (group_name, group_records) in enumerate(comparison_groups.items()):
            aggregated = self.aggregate_by_date(group_records, group_by)
            all_dates.update(aggregated.keys())
            
            color = colors[idx % len(colors)]
            datasets.append({
                'label': group_name,
                'data': aggregated,
                'backgroundColor': color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
                'borderColor': color,
                'borderWidth': 2,
                'fill': False
            })
        
        # Sort dates
        labels = sorted(list(all_dates))
        
        # Fill in missing dates with 0 for each dataset
        for dataset in datasets:
            data_dict = dataset['data']
            dataset['data'] = [data_dict.get(date, {'sales_amount': 0})['sales_amount'] for date in labels]
        
        return ChartData(labels=labels, datasets=datasets)
    
    def get_cached_sales_data(
        self,
        regions: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = 'day'
    ) -> Dict:
        """
        Get cached sales data with automatic cache management
        
        Args:
            regions: List of regions
            products: List of products
            start_date: Start date
            end_date: End date
            group_by: Grouping level
            
        Returns:
            Dictionary with chart data and summary statistics
        """
        # Generate cache key based on parameters
        cache_key = self._generate_cache_key(
            regions=regions,
            products=products,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        
        # Try to get from cache
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Fetch and process data
        records = self.get_sales_data_filtered(regions, products, start_date, end_date)
        chart_data = self._prepare_chart_data(records, group_by)
        summary = self._calculate_summary(records)
        
        result = {
            'chart': chart_data,
            'summary': summary,
            'metadata': {
                'record_count': len(records),
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d') if start_date else None,
                    'end': end_date.strftime('%Y-%m-%d') if end_date else None
                },
                'filters': {
                    'regions': regions or [],
                    'products': products or []
                }
            }
        }
        
        # Cache the result
        if self.cache:
            self.cache.set(cache_key, result)
        
        return result
    
    def _load_data_cached(self) -> List[SalesRecord]:
        """Load data with in-memory caching"""
        # Check if cache is still valid (5 minutes)
        if self._data_cache and self._cache_timestamp:
            if (datetime.now() - self._cache_timestamp).seconds < 300:
                return self._data_cache
        
        # Load fresh data
        records = []
        try:
            with open(self.data_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    records.append(SalesRecord(
                        date=datetime.strptime(row['date'], '%Y-%m-%d'),
                        region=row['region'],
                        product=row['product'],
                        sales_amount=float(row['sales_amount']),
                        quantity=int(row['quantity'])
                    ))
        except FileNotFoundError:
            raise Exception(f"Data file not found: {self.data_file}")
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
        
        # Update cache
        self._data_cache = records
        self._cache_timestamp = datetime.now()
        
        return records
    
    def _prepare_chart_data(self, records: List[SalesRecord], group_by: str) -> Dict:
        """Prepare data in Chart.js format"""
        aggregated = self.aggregate_by_date(records, group_by)
        labels = sorted(aggregated.keys())
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Sales Amount',
                'data': [aggregated[label]['sales_amount'] for label in labels],
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgb(54, 162, 235)',
                'borderWidth': 2,
                'fill': True
            }]
        }
    
    def _calculate_summary(self, records: List[SalesRecord]) -> Dict:
        """Calculate summary statistics"""
        if not records:
            return {
                'total_sales': 0,
                'total_quantity': 0,
                'average_sale': 0,
                'record_count': 0
            }
        
        total_sales = sum(r.sales_amount for r in records)
        total_quantity = sum(r.quantity for r in records)
        
        return {
            'total_sales': round(total_sales, 2),
            'total_quantity': total_quantity,
            'average_sale': round(total_sales / len(records), 2),
            'record_count': len(records)
        }
    
    def _generate_cache_key(self, **kwargs) -> str:
        """Generate cache key from parameters"""
        # Create a stable string representation
        key_parts = []
        for k, v in sorted(kwargs.items()):
            if isinstance(v, datetime):
                key_parts.append(f"{k}:{v.strftime('%Y-%m-%d')}")
            elif isinstance(v, list):
                key_parts.append(f"{k}:{','.join(sorted(v)) if v else 'all'}")
            else:
                key_parts.append(f"{k}:{v}")
        
        key_string = '|'.join(key_parts)
        return f"sales_data:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def get_available_regions(self) -> List[str]:
        """Get all available regions"""
        records = self._load_data_cached()
        return sorted(set(r.region for r in records))
    
    def get_available_products(self) -> List[str]:
        """Get all available products"""
        records = self._load_data_cached()
        return sorted(set(r.product for r in records))
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """Get the date range of available data"""
        records = self._load_data_cached()
        if not records:
            return datetime.now(), datetime.now()
        
        dates = [r.date for r in records]
        return min(dates), max(dates)
    
    def export_to_csv(
        self,
        regions: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Export filtered data for CSV download
        
        Returns:
            List of dictionaries representing rows
        """
        records = self.get_sales_data_filtered(regions, products, start_date, end_date)
        return [r.to_dict() for r in records]


def main():
    """Test function"""
    service = DataServiceImproved('data/sales_data.csv')
    
    # Test multi-dimension filtering
    print("=== Multi-dimension Filter Test ===")
    regions = ['Beijing', 'Shanghai']
    products = ['Laptop', 'Smartphone']
    data = service.get_sales_data_filtered(regions=regions, products=products)
    print(f"Found {len(data)} records for regions {regions} and products {products}")
    
    # Test aggregation
    print("\n=== Aggregation Test ===")
    aggregated = service.aggregate_by_date(data, group_by='day')
    print(f"Aggregated into {len(aggregated)} days")
    
    # Test comparison
    print("\n=== Comparison Test ===")
    comparison = service.get_comparison_data(
        regions=regions,
        products=products,
        compare_by='region'
    )
    print(f"Comparison chart with {len(comparison.datasets)} datasets")
    
    # Test cache
    print("\n=== Cache Test ===")
    cached = service.get_cached_sales_data(regions=regions, products=products)
    print(f"Summary: {cached['summary']}")
    
    print("\n=== Available Options ===")
    print(f"Regions: {service.get_available_regions()}")
    print(f"Products: {service.get_available_products()}")
    print(f"Date range: {service.get_date_range()}")


if __name__ == "__main__":
    main()
