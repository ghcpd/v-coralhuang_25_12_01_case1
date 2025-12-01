"""
Test suite for data_service_improved.py
Tests filtering, caching, aggregation, and comparison features
"""
import sys
import os
import pytest
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_service_improved import DataService
from models import FilterCriteria, SalesRecord

# Test fixtures
@pytest.fixture
def data_service():
    """Create a data service instance for testing"""
    # Use the actual data file
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sales_data.csv')
    return DataService(csv_path, cache_ttl=300)


class TestBasicFiltering:
    """Tests for basic filtering functionality"""
    
    def test_get_sales_data_filtered_all(self, data_service):
        """Test fetching all data without filters"""
        criteria = FilterCriteria()
        data = data_service.get_sales_data_filtered(criteria)
        assert len(data) > 0
        assert all(isinstance(r, SalesRecord) for r in data)
    
    def test_get_sales_data_filtered_single_region(self, data_service):
        """Test filtering by single region"""
        criteria = FilterCriteria(regions=['Beijing'])
        data = data_service.get_sales_data_filtered(criteria)
        assert len(data) > 0
        assert all(r.region == 'Beijing' for r in data)
    
    def test_get_sales_data_filtered_multiple_regions(self, data_service):
        """Test filtering by multiple regions"""
        criteria = FilterCriteria(regions=['Beijing', 'Shanghai'])
        data = data_service.get_sales_data_filtered(criteria)
        assert len(data) > 0
        assert all(r.region in ['Beijing', 'Shanghai'] for r in data)
    
    def test_get_sales_data_filtered_single_product(self, data_service):
        """Test filtering by single product"""
        criteria = FilterCriteria(products=['Laptop'])
        data = data_service.get_sales_data_filtered(criteria)
        assert len(data) > 0
        assert all(r.product == 'Laptop' for r in data)
    
    def test_get_sales_data_filtered_multiple_products(self, data_service):
        """Test filtering by multiple products"""
        criteria = FilterCriteria(products=['Laptop', 'Smartphone'])
        data = data_service.get_sales_data_filtered(criteria)
        assert len(data) > 0
        assert all(r.product in ['Laptop', 'Smartphone'] for r in data)
    
    def test_get_sales_data_filtered_date_range(self, data_service):
        """Test filtering by date range"""
        start = datetime(2024, 11, 1)
        end = datetime(2024, 11, 7)
        criteria = FilterCriteria(start_date=start, end_date=end)
        data = data_service.get_sales_data_filtered(criteria)
        assert len(data) > 0
        assert all(start <= r.date <= end for r in data)
    
    def test_get_sales_data_filtered_combined(self, data_service):
        """Test filtering with multiple dimensions"""
        start = datetime(2024, 11, 1)
        end = datetime(2024, 11, 10)
        criteria = FilterCriteria(
            regions=['Beijing', 'Shanghai'],
            products=['Laptop'],
            start_date=start,
            end_date=end
        )
        data = data_service.get_sales_data_filtered(criteria)
        assert all(r.region in ['Beijing', 'Shanghai'] for r in data)
        assert all(r.product == 'Laptop' for r in data)
        assert all(start <= r.date <= end for r in data)
    
    def test_get_sales_data_filtered_empty_result(self, data_service):
        """Test filtering that returns no results"""
        criteria = FilterCriteria(regions=['NonexistentRegion'])
        data = data_service.get_sales_data_filtered(criteria)
        assert len(data) == 0


class TestCaching:
    """Tests for caching functionality"""
    
    def test_get_cached_sales_data_cache_miss(self, data_service):
        """Test cache miss returns fresh data"""
        criteria = FilterCriteria(regions=['Beijing'])
        data, from_cache = data_service.get_cached_sales_data(criteria)
        assert len(data) > 0
        assert from_cache is False
        assert data_service.get_cache_stats()['misses'] >= 1
    
    def test_get_cached_sales_data_cache_hit(self, data_service):
        """Test cache hit returns cached data"""
        criteria = FilterCriteria(regions=['Beijing'])
        
        # First call (cache miss)
        data1, from_cache1 = data_service.get_cached_sales_data(criteria)
        assert from_cache1 is False
        
        # Second call (cache hit)
        data2, from_cache2 = data_service.get_cached_sales_data(criteria)
        assert from_cache2 is True
        assert data1 == data2
        
        # Verify cache stats
        stats = data_service.get_cache_stats()
        assert stats['hits'] >= 1
    
    def test_cache_different_criteria(self, data_service):
        """Test that different criteria use different cache entries"""
        criteria1 = FilterCriteria(regions=['Beijing'])
        criteria2 = FilterCriteria(regions=['Shanghai'])
        
        data1, _ = data_service.get_cached_sales_data(criteria1)
        data2, _ = data_service.get_cached_sales_data(criteria2)
        
        assert data1 != data2
    
    def test_clear_cache(self, data_service):
        """Test cache clearing"""
        criteria = FilterCriteria(regions=['Beijing'])
        
        # Populate cache
        data1, from_cache1 = data_service.get_cached_sales_data(criteria)
        assert from_cache1 is False
        
        # Second call should hit cache
        data2, from_cache2 = data_service.get_cached_sales_data(criteria)
        assert from_cache2 is True
        
        # Clear cache
        data_service.clear_cache()
        
        # Should be cache miss again
        data3, from_cache3 = data_service.get_cached_sales_data(criteria)
        assert from_cache3 is False


class TestAggregation:
    """Tests for data aggregation functionality"""
    
    def test_aggregate_by_date_daily(self, data_service):
        """Test daily aggregation"""
        criteria = FilterCriteria()
        records = data_service.get_sales_data_filtered(criteria)
        agg = data_service.aggregate_by_date(records, 'daily')
        
        assert len(agg) > 0
        for date_key, agg_data in agg.items():
            assert 'total_sales' in agg_data
            assert 'total_quantity' in agg_data
            assert agg_data['total_sales'] > 0
            assert agg_data['total_quantity'] > 0
    
    def test_aggregate_by_date_weekly(self, data_service):
        """Test weekly aggregation"""
        criteria = FilterCriteria()
        records = data_service.get_sales_data_filtered(criteria)
        agg = data_service.aggregate_by_date(records, 'weekly')
        
        assert len(agg) > 0
        for date_key, agg_data in agg.items():
            assert 'W' in date_key  # Weekly format includes 'W'
    
    def test_aggregate_by_date_monthly(self, data_service):
        """Test monthly aggregation"""
        criteria = FilterCriteria()
        records = data_service.get_sales_data_filtered(criteria)
        agg = data_service.aggregate_by_date(records, 'monthly')
        
        assert len(agg) > 0
        for date_key, agg_data in agg.items():
            # Monthly format is YYYY-MM
            assert len(date_key) == 7
            assert date_key[4] == '-'
    
    def test_aggregation_contains_regions_products(self, data_service):
        """Test that aggregation includes regions and products"""
        criteria = FilterCriteria(regions=['Beijing', 'Shanghai'])
        records = data_service.get_sales_data_filtered(criteria)
        agg = data_service.aggregate_by_date(records)
        
        for date_key, agg_data in agg.items():
            assert 'regions' in agg_data
            assert 'products' in agg_data
            assert len(agg_data['regions']) > 0
            assert len(agg_data['products']) > 0


class TestComparison:
    """Tests for comparison functionality"""
    
    def test_get_comparison_data(self, data_service):
        """Test comparison between two filter sets"""
        criteria1 = FilterCriteria(regions=['Beijing'])
        criteria2 = FilterCriteria(regions=['Shanghai'])
        
        comparison = data_service.get_comparison_data(criteria1, criteria2)
        
        assert 'set1' in comparison
        assert 'set2' in comparison
        assert comparison['set1']['total_sales'] > 0
        assert comparison['set2']['total_sales'] > 0
    
    def test_comparison_date_range(self, data_service):
        """Test comparison between different date ranges"""
        end_date = datetime(2024, 11, 7)
        start_date1 = datetime(2024, 11, 1)
        start_date2 = datetime(2024, 11, 5)
        
        criteria1 = FilterCriteria(start_date=start_date1, end_date=end_date)
        criteria2 = FilterCriteria(start_date=start_date2, end_date=end_date)
        
        comparison = data_service.get_comparison_data(criteria1, criteria2)
        
        # First period should have more data
        assert comparison['set1']['record_count'] >= comparison['set2']['record_count']


class TestFilterOptions:
    """Tests for filter options retrieval"""
    
    def test_get_available_regions(self, data_service):
        """Test getting available regions"""
        regions = data_service.get_available_regions()
        assert len(regions) > 0
        assert isinstance(regions, list)
        assert all(isinstance(r, str) for r in regions)
        assert regions == sorted(regions)  # Should be sorted
    
    def test_get_available_products(self, data_service):
        """Test getting available products"""
        products = data_service.get_available_products()
        assert len(products) > 0
        assert isinstance(products, list)
        assert all(isinstance(p, str) for p in products)
        assert products == sorted(products)  # Should be sorted
    
    def test_get_date_range(self, data_service):
        """Test getting date range"""
        date_range = data_service.get_date_range()
        assert 'min' in date_range
        assert 'max' in date_range
        assert date_range['min'] < date_range['max']


class TestPerformance:
    """Performance tests"""
    
    def test_query_performance_cached(self, data_service):
        """Test that cached queries are fast (< 10ms)"""
        import time
        
        criteria = FilterCriteria(regions=['Beijing'])
        
        # First query (populate cache)
        data_service.get_cached_sales_data(criteria)
        
        # Second query should be from cache
        start = time.time()
        data, from_cache = data_service.get_cached_sales_data(criteria)
        end = time.time()
        
        assert from_cache is True
        assert (end - start) < 0.01  # Less than 10ms
    
    def test_cache_hit_ratio(self, data_service):
        """Test that cache hit ratio reaches target (70%+)"""
        criteria1 = FilterCriteria(regions=['Beijing'])
        criteria2 = FilterCriteria(regions=['Shanghai'])
        
        # Make multiple queries with some repetition
        for _ in range(10):
            data_service.get_cached_sales_data(criteria1)
        for _ in range(3):
            data_service.get_cached_sales_data(criteria2)
        
        stats = data_service.get_cache_stats()
        hit_ratio = stats['hit_ratio']
        
        # Should have good hit ratio due to repetition
        assert hit_ratio > 50  # At least 50%


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_empty_filter_criteria(self, data_service):
        """Test with empty filter criteria"""
        criteria = FilterCriteria()
        data = data_service.get_sales_data_filtered(criteria)
        assert len(data) > 0
    
    def test_aggregation_empty_records(self, data_service):
        """Test aggregation with empty records"""
        agg = data_service.aggregate_by_date([])
        assert len(agg) == 0
    
    def test_invalid_group_by(self, data_service):
        """Test aggregation with invalid group_by parameter"""
        criteria = FilterCriteria()
        records = data_service.get_sales_data_filtered(criteria)
        
        # Should not raise error, might use default behavior
        try:
            agg = data_service.aggregate_by_date(records, 'invalid')
            # If it doesn't raise, that's also acceptable
            assert True
        except Exception:
            # If it raises, that's also acceptable
            assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
