"""
Enhanced Data Service with multi-dimension filtering, caching, and aggregation
Features:
- Multi-dimension filtering (regions, products, date ranges)
- Data caching with 5-minute TTL
- Time-based aggregation (daily, weekly, monthly)
- Comparison data retrieval
- Performance optimization
"""
import csv
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from models import SalesRecord, FilterCriteria
import json


class DataService:
    """Enhanced data query service with caching and aggregation"""
    
    def __init__(self, csv_file_path: str, cache_ttl: int = 300):
        self.data_file = csv_file_path
        self.cache_ttl = cache_ttl
        self._data_cache = {}
        self._cache_timestamps = {}
        self._filter_cache = {}
        self._cache_stats = {'hits': 0, 'misses': 0}
    
    def get_cached_sales_data(self, criteria: FilterCriteria) -> Tuple[List[SalesRecord], bool]:
        """
        Get sales data with caching support
        Returns: (data, is_from_cache)
        """
        cache_key = self._generate_cache_key(criteria)
        
        # Check if in cache and not expired
        if cache_key in self._data_cache:
            if self._is_cache_valid(cache_key):
                self._cache_stats['hits'] += 1
                return self._data_cache[cache_key], True
        
        # Cache miss or expired, fetch fresh data
        self._cache_stats['misses'] += 1
        data = self.get_sales_data_filtered(criteria)
        
        # Store in cache
        self._data_cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now()
        
        return data, False
    
    def get_sales_data_filtered(self, criteria: FilterCriteria) -> List[SalesRecord]:
        """
        Get sales data based on multi-dimension filter criteria
        Supports: regions, products, date ranges
        """
        all_records = self._load_data()
        filtered = []
        
        for record in all_records:
            # Multi-dimension filtering
            if criteria.regions and record.region not in criteria.regions:
                continue
            if criteria.products and record.product not in criteria.products:
                continue
            if criteria.start_date and record.date < criteria.start_date:
                continue
            if criteria.end_date and record.date > criteria.end_date:
                continue
            
            filtered.append(record)
        
        return filtered
    
    def aggregate_by_date(self, records: List[SalesRecord], 
                         group_by: str = 'daily') -> Dict[str, Dict]:
        """
        Aggregate sales data by date with specified interval
        group_by options: 'daily', 'weekly', 'monthly'
        Returns: {date: {total_sales, total_quantity, regions, products}}
        """
        aggregated = defaultdict(lambda: {
            'total_sales': 0.0,
            'total_quantity': 0,
            'regions': set(),
            'products': set(),
            'records': []
        })
        
        for record in records:
            date_key = self._get_date_key(record.date, group_by)
            agg = aggregated[date_key]
            
            agg['total_sales'] += record.sales_amount
            agg['total_quantity'] += record.quantity
            agg['regions'].add(record.region)
            agg['products'].add(record.product)
            agg['records'].append(record)
        
        # Convert sets to sorted lists for JSON serialization
        result = {}
        for date_key in sorted(aggregated.keys()):
            agg = aggregated[date_key]
            result[date_key] = {
                'total_sales': round(agg['total_sales'], 2),
                'total_quantity': agg['total_quantity'],
                'regions': sorted(list(agg['regions'])),
                'products': sorted(list(agg['products'])),
                'record_count': len(agg['records'])
            }
        
        return result
    
    def get_comparison_data(self, criteria1: FilterCriteria, 
                           criteria2: FilterCriteria) -> Dict:
        """
        Get comparison data between two filter sets
        Useful for comparing periods, regions, or products
        """
        data1 = self.get_sales_data_filtered(criteria1)
        data2 = self.get_sales_data_filtered(criteria2)
        
        agg1 = self.aggregate_by_date(data1)
        agg2 = self.aggregate_by_date(data2)
        
        return {
            'set1': {
                'criteria': criteria1.to_dict(),
                'total_sales': sum(agg['total_sales'] for agg in agg1.values()),
                'total_quantity': sum(agg['total_quantity'] for agg in agg1.values()),
                'record_count': len(data1),
                'aggregated': agg1
            },
            'set2': {
                'criteria': criteria2.to_dict(),
                'total_sales': sum(agg['total_sales'] for agg in agg2.values()),
                'total_quantity': sum(agg['total_quantity'] for agg in agg2.values()),
                'record_count': len(data2),
                'aggregated': agg2
            }
        }
    
    def get_available_regions(self) -> List[str]:
        """Get all available regions from cache"""
        if 'regions' not in self._filter_cache:
            records = self._load_data()
            regions = sorted(set(r.region for r in records))
            self._filter_cache['regions'] = regions
        
        return self._filter_cache['regions']
    
    def get_available_products(self) -> List[str]:
        """Get all available products from cache"""
        if 'products' not in self._filter_cache:
            records = self._load_data()
            products = sorted(set(r.product for r in records))
            self._filter_cache['products'] = products
        
        return self._filter_cache['products']
    
    def get_date_range(self) -> Dict[str, str]:
        """Get min and max dates from data"""
        if 'date_range' not in self._filter_cache:
            records = self._load_data()
            if records:
                dates = [r.date for r in records]
                self._filter_cache['date_range'] = {
                    'min': min(dates).strftime('%Y-%m-%d'),
                    'max': max(dates).strftime('%Y-%m-%d')
                }
            else:
                self._filter_cache['date_range'] = {
                    'min': datetime.now().strftime('%Y-%m-%d'),
                    'max': datetime.now().strftime('%Y-%m-%d')
                }
        
        return self._filter_cache['date_range']
    
    def clear_cache(self):
        """Clear all caches"""
        self._data_cache.clear()
        self._cache_timestamps.clear()
        self._filter_cache.clear()
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        total = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_ratio = (self._cache_stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self._cache_stats['hits'],
            'misses': self._cache_stats['misses'],
            'total': total,
            'hit_ratio': round(hit_ratio, 2)
        }
    
    def _load_data(self) -> List[SalesRecord]:
        """Load data from CSV"""
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
            print(f"Warning: Data file not found: {self.data_file}")
        
        return records
    
    def _generate_cache_key(self, criteria: FilterCriteria) -> str:
        """Generate cache key from filter criteria"""
        key_parts = [
            'sales',
            '|'.join(sorted(criteria.regions or [])),
            '|'.join(sorted(criteria.products or [])),
            criteria.start_date.strftime('%Y-%m-%d') if criteria.start_date else 'none',
            criteria.end_date.strftime('%Y-%m-%d') if criteria.end_date else 'none'
        ]
        key_string = ':'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return age < self.cache_ttl
    
    def _get_date_key(self, date: datetime, group_by: str) -> str:
        """Get date key for aggregation based on grouping interval"""
        if group_by == 'weekly':
            # Get Monday of the week
            monday = date - timedelta(days=date.weekday())
            return monday.strftime('%Y-W%U')
        elif group_by == 'monthly':
            return date.strftime('%Y-%m')
        else:  # daily
            return date.strftime('%Y-%m-%d')


def main():
    """Test function"""
    service = DataService('data/sales_data.csv')
    
    # Test 1: Single region filter
    criteria = FilterCriteria(regions=['Beijing'])
    data, from_cache = service.get_cached_sales_data(criteria)
    print(f"Test 1 - Beijing records: {len(data)} (from cache: {from_cache})")
    
    # Test 2: Multi-region filter
    criteria = FilterCriteria(regions=['Beijing', 'Shanghai'])
    data, from_cache = service.get_cached_sales_data(criteria)
    print(f"Test 2 - Beijing & Shanghai: {len(data)} (from cache: {from_cache})")
    
    # Test 3: Date range filter
    start = datetime(2024, 11, 1)
    end = datetime(2024, 11, 7)
    criteria = FilterCriteria(start_date=start, end_date=end)
    data, from_cache = service.get_cached_sales_data(criteria)
    print(f"Test 3 - Date range: {len(data)} (from cache: {from_cache})")
    
    # Test 4: Aggregation
    agg = service.aggregate_by_date(data, 'daily')
    print(f"Test 4 - Daily aggregation: {len(agg)} days")
    
    # Test 5: Available options
    print(f"Available regions: {service.get_available_regions()}")
    print(f"Available products: {service.get_available_products()}")
    print(f"Date range: {service.get_date_range()}")
    
    # Test 6: Cache stats
    print(f"Cache stats: {service.get_cache_stats()}")


if __name__ == "__main__":
    main()
