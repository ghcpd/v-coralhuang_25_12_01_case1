"""
Test suite for Data Service
Tests: multi-select filtering, date ranges, edge cases, cache functionality
"""
import pytest
from datetime import datetime, timedelta
import sys
import os
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_service_improved import DataServiceImproved
from models import SalesRecord, FilterCriteria


@pytest.fixture
def data_service():
    """Create data service instance"""
    data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'sales_data.csv')
    return DataServiceImproved(data_file)


@pytest.fixture
def mock_cache():
    """Create mock cache instance"""
    cache = Mock()
    cache.get = Mock(return_value=None)
    cache.set = Mock()
    return cache


@pytest.fixture
def sample_date_range():
    """Sample date range for testing"""
    return {
        'start': datetime(2024, 11, 1),
        'end': datetime(2024, 11, 30)
    }


class TestDataLoading:
    """Tests for data loading functionality"""
    
    def test_load_data(self, data_service):
        """Test loading data from CSV"""
        records = data_service._load_data_cached()
        
        assert len(records) > 0
        assert all(isinstance(r, SalesRecord) for r in records)
    
    def test_data_caching(self, data_service):
        """Test that data is cached in memory"""
        # First load
        records1 = data_service._load_data_cached()
        
        # Second load (should use cache)
        records2 = data_service._load_data_cached()
        
        # Should be the same objects (cached)
        assert records1 is records2
    
    def test_get_available_regions(self, data_service):
        """Test getting list of available regions"""
        regions = data_service.get_available_regions()
        
        assert isinstance(regions, list)
        assert len(regions) > 0
        assert all(isinstance(r, str) for r in regions)
        # Should be sorted
        assert regions == sorted(regions)
    
    def test_get_available_products(self, data_service):
        """Test getting list of available products"""
        products = data_service.get_available_products()
        
        assert isinstance(products, list)
        assert len(products) > 0
        assert all(isinstance(p, str) for p in products)
        # Should be sorted
        assert products == sorted(products)
    
    def test_get_date_range(self, data_service):
        """Test getting date range of data"""
        min_date, max_date = data_service.get_date_range()
        
        assert isinstance(min_date, datetime)
        assert isinstance(max_date, datetime)
        assert min_date <= max_date


class TestFiltering:
    """Tests for data filtering functionality"""
    
    def test_filter_by_single_region(self, data_service):
        """Test filtering by single region"""
        records = data_service.get_sales_data_filtered(regions=['Beijing'])
        
        assert len(records) > 0
        assert all(r.region == 'Beijing' for r in records)
    
    def test_filter_by_multiple_regions(self, data_service):
        """Test filtering by multiple regions"""
        target_regions = ['Beijing', 'Shanghai']
        records = data_service.get_sales_data_filtered(regions=target_regions)
        
        assert len(records) > 0
        assert all(r.region in target_regions for r in records)
    
    def test_filter_by_single_product(self, data_service):
        """Test filtering by single product"""
        records = data_service.get_sales_data_filtered(products=['Laptop'])
        
        assert len(records) > 0
        assert all(r.product == 'Laptop' for r in records)
    
    def test_filter_by_multiple_products(self, data_service):
        """Test filtering by multiple products"""
        target_products = ['Laptop', 'Smartphone']
        records = data_service.get_sales_data_filtered(products=target_products)
        
        assert len(records) > 0
        assert all(r.product in target_products for r in records)
    
    def test_filter_by_date_range(self, data_service, sample_date_range):
        """Test filtering by date range"""
        records = data_service.get_sales_data_filtered(
            start_date=sample_date_range['start'],
            end_date=sample_date_range['end']
        )
        
        assert len(records) > 0
        assert all(
            sample_date_range['start'] <= r.date <= sample_date_range['end']
            for r in records
        )
    
    def test_filter_multi_dimension(self, data_service, sample_date_range):
        """Test filtering by multiple dimensions simultaneously"""
        records = data_service.get_sales_data_filtered(
            regions=['Beijing', 'Shanghai'],
            products=['Laptop'],
            start_date=sample_date_range['start'],
            end_date=sample_date_range['end']
        )
        
        for record in records:
            assert record.region in ['Beijing', 'Shanghai']
            assert record.product == 'Laptop'
            assert sample_date_range['start'] <= record.date <= sample_date_range['end']
    
    def test_filter_no_results(self, data_service):
        """Test filtering with no matching results"""
        # Use impossible date range
        future_date = datetime(2099, 1, 1)
        records = data_service.get_sales_data_filtered(
            start_date=future_date,
            end_date=future_date
        )
        
        assert len(records) == 0
    
    def test_filter_empty_filters(self, data_service):
        """Test with no filters (should return all data)"""
        all_records = data_service._load_data_cached()
        filtered_records = data_service.get_sales_data_filtered()
        
        assert len(filtered_records) == len(all_records)


class TestAggregation:
    """Tests for data aggregation functionality"""
    
    def test_aggregate_by_day(self, data_service, sample_date_range):
        """Test daily aggregation"""
        records = data_service.get_sales_data_filtered(
            start_date=sample_date_range['start'],
            end_date=sample_date_range['end']
        )
        
        aggregated = data_service.aggregate_by_date(records, group_by='day')
        
        assert isinstance(aggregated, dict)
        assert len(aggregated) > 0
        
        # Check data structure
        for date_key, metrics in aggregated.items():
            assert 'sales_amount' in metrics
            assert 'quantity' in metrics
            assert metrics['sales_amount'] >= 0
            assert metrics['quantity'] >= 0
    
    def test_aggregate_by_week(self, data_service, sample_date_range):
        """Test weekly aggregation"""
        records = data_service.get_sales_data_filtered(
            start_date=sample_date_range['start'],
            end_date=sample_date_range['end']
        )
        
        aggregated = data_service.aggregate_by_date(records, group_by='week')
        
        assert isinstance(aggregated, dict)
        # Weekly should have fewer entries than daily
        daily = data_service.aggregate_by_date(records, group_by='day')
        assert len(aggregated) <= len(daily)
    
    def test_aggregate_by_month(self, data_service, sample_date_range):
        """Test monthly aggregation"""
        records = data_service.get_sales_data_filtered(
            start_date=sample_date_range['start'],
            end_date=sample_date_range['end']
        )
        
        aggregated = data_service.aggregate_by_date(records, group_by='month')
        
        assert isinstance(aggregated, dict)
        # Monthly should have fewest entries
        daily = data_service.aggregate_by_date(records, group_by='day')
        assert len(aggregated) <= len(daily)
    
    def test_aggregate_empty_records(self, data_service):
        """Test aggregation with empty records"""
        aggregated = data_service.aggregate_by_date([], group_by='day')
        
        assert isinstance(aggregated, dict)
        assert len(aggregated) == 0


class TestComparison:
    """Tests for comparison data functionality"""
    
    def test_comparison_by_region(self, data_service, sample_date_range):
        """Test comparison by region"""
        chart_data = data_service.get_comparison_data(
            regions=['Beijing', 'Shanghai'],
            start_date=sample_date_range['start'],
            end_date=sample_date_range['end'],
            compare_by='region'
        )
        
        assert len(chart_data.labels) > 0
        assert len(chart_data.datasets) > 0
        
        # Should have one dataset per region
        dataset_labels = [ds['label'] for ds in chart_data.datasets]
        assert 'Beijing' in dataset_labels or 'Shanghai' in dataset_labels
    
    def test_comparison_by_product(self, data_service, sample_date_range):
        """Test comparison by product"""
        chart_data = data_service.get_comparison_data(
            products=['Laptop', 'Smartphone'],
            start_date=sample_date_range['start'],
            end_date=sample_date_range['end'],
            compare_by='product'
        )
        
        assert len(chart_data.labels) > 0
        assert len(chart_data.datasets) > 0
        
        # Should have one dataset per product
        dataset_labels = [ds['label'] for ds in chart_data.datasets]
        assert 'Laptop' in dataset_labels or 'Smartphone' in dataset_labels
    
    def test_comparison_dataset_structure(self, data_service, sample_date_range):
        """Test that comparison datasets have correct structure"""
        chart_data = data_service.get_comparison_data(
            regions=['Beijing'],
            start_date=sample_date_range['start'],
            end_date=sample_date_range['end'],
            compare_by='region'
        )
        
        for dataset in chart_data.datasets:
            assert 'label' in dataset
            assert 'data' in dataset
            assert 'backgroundColor' in dataset
            assert 'borderColor' in dataset
            assert isinstance(dataset['data'], list)


class TestCaching:
    """Tests for caching functionality"""
    
    def test_cache_key_generation(self, data_service):
        """Test that cache keys are generated consistently"""
        key1 = data_service._generate_cache_key(
            regions=['Beijing'],
            products=['Laptop'],
            start_date=datetime(2024, 11, 1),
            group_by='day'
        )
        
        key2 = data_service._generate_cache_key(
            regions=['Beijing'],
            products=['Laptop'],
            start_date=datetime(2024, 11, 1),
            group_by='day'
        )
        
        # Same parameters should generate same key
        assert key1 == key2
    
    def test_cache_key_uniqueness(self, data_service):
        """Test that different parameters generate different keys"""
        key1 = data_service._generate_cache_key(regions=['Beijing'])
        key2 = data_service._generate_cache_key(regions=['Shanghai'])
        
        assert key1 != key2
    
    def test_get_cached_sales_data(self, mock_cache):
        """Test getting cached sales data"""
        data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'sales_data.csv')
        service = DataServiceImproved(data_file, cache=mock_cache)
        
        result = service.get_cached_sales_data(
            regions=['Beijing'],
            start_date=datetime(2024, 11, 1),
            end_date=datetime(2024, 11, 30)
        )
        
        # Check result structure
        assert 'chart' in result
        assert 'summary' in result
        assert 'metadata' in result
        
        # Verify cache.set was called
        assert mock_cache.set.called
    
    def test_cache_hit(self, mock_cache):
        """Test cache hit scenario"""
        cached_data = {
            'chart': {'labels': [], 'datasets': []},
            'summary': {'total_sales': 1000},
            'metadata': {}
        }
        mock_cache.get = Mock(return_value=cached_data)
        
        data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'sales_data.csv')
        service = DataServiceImproved(data_file, cache=mock_cache)
        
        result = service.get_cached_sales_data(regions=['Beijing'])
        
        # Should return cached data
        assert result == cached_data
        assert mock_cache.get.called


class TestSummaryStatistics:
    """Tests for summary statistics calculation"""
    
    def test_calculate_summary(self, data_service, sample_date_range):
        """Test summary statistics calculation"""
        records = data_service.get_sales_data_filtered(
            start_date=sample_date_range['start'],
            end_date=sample_date_range['end']
        )
        
        summary = data_service._calculate_summary(records)
        
        assert 'total_sales' in summary
        assert 'total_quantity' in summary
        assert 'average_sale' in summary
        assert 'record_count' in summary
        
        assert summary['total_sales'] >= 0
        assert summary['total_quantity'] >= 0
        assert summary['average_sale'] >= 0
        assert summary['record_count'] == len(records)
    
    def test_summary_empty_records(self, data_service):
        """Test summary with empty records"""
        summary = data_service._calculate_summary([])
        
        assert summary['total_sales'] == 0
        assert summary['total_quantity'] == 0
        assert summary['average_sale'] == 0
        assert summary['record_count'] == 0


class TestExport:
    """Tests for CSV export functionality"""
    
    def test_export_to_csv(self, data_service, sample_date_range):
        """Test CSV export"""
        csv_data = data_service.export_to_csv(
            regions=['Beijing'],
            start_date=sample_date_range['start'],
            end_date=sample_date_range['end']
        )
        
        assert isinstance(csv_data, list)
        assert len(csv_data) > 0
        
        # Check data structure
        for row in csv_data:
            assert 'date' in row
            assert 'region' in row
            assert 'product' in row
            assert 'sales_amount' in row
            assert 'quantity' in row
    
    def test_export_with_filters(self, data_service):
        """Test export with various filters"""
        csv_data = data_service.export_to_csv(
            regions=['Beijing', 'Shanghai'],
            products=['Laptop']
        )
        
        assert len(csv_data) > 0
        
        # Verify filtering
        for row in csv_data:
            assert row['region'] in ['Beijing', 'Shanghai']
            assert row['product'] == 'Laptop'


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_invalid_date_range(self, data_service):
        """Test with start_date after end_date"""
        records = data_service.get_sales_data_filtered(
            start_date=datetime(2024, 12, 31),
            end_date=datetime(2024, 1, 1)
        )
        
        # Should return empty results
        assert len(records) == 0
    
    def test_nonexistent_region(self, data_service):
        """Test filtering by non-existent region"""
        records = data_service.get_sales_data_filtered(regions=['NonExistent'])
        
        assert len(records) == 0
    
    def test_nonexistent_product(self, data_service):
        """Test filtering by non-existent product"""
        records = data_service.get_sales_data_filtered(products=['NonExistent'])
        
        assert len(records) == 0


class TestPerformance:
    """Performance tests"""
    
    def test_filter_performance(self, data_service):
        """Test filtering performance"""
        import time
        
        start = time.time()
        records = data_service.get_sales_data_filtered(
            regions=['Beijing', 'Shanghai'],
            products=['Laptop', 'Smartphone']
        )
        elapsed = time.time() - start
        
        assert len(records) >= 0
        print(f"\nFilter operation: {elapsed*1000:.2f}ms")
    
    def test_aggregation_performance(self, data_service):
        """Test aggregation performance"""
        import time
        
        records = data_service.get_sales_data_filtered()
        
        start = time.time()
        aggregated = data_service.aggregate_by_date(records, group_by='day')
        elapsed = time.time() - start
        
        assert len(aggregated) >= 0
        print(f"\nAggregation operation: {elapsed*1000:.2f}ms")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
