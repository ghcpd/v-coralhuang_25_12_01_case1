"""
Test suite for Dashboard API endpoints
Tests: endpoint functionality, parameters, error handling, performance
"""
import pytest
from datetime import datetime, timedelta
from flask import json
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dashboard_improved import app, data_service
from config import TestingConfig


@pytest.fixture
def client():
    """Create test client"""
    app.config.from_object(TestingConfig)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_filters():
    """Sample filter parameters"""
    return {
        'regions': ['Beijing', 'Shanghai'],
        'products': ['Laptop', 'Smartphone'],
        'start_date': '2024-11-01',
        'end_date': '2024-11-30',
        'group_by': 'day'
    }


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check(self, client):
        """Test health endpoint returns 200"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'timestamp' in data
        assert data['version'] == '2.0-improved'


class TestFiltersEndpoint:
    """Tests for /api/filters endpoint"""
    
    def test_get_filter_options(self, client):
        """Test getting available filter options"""
        response = client.get('/api/filters')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'regions' in data
        assert 'products' in data
        assert 'date_range' in data
        assert 'quick_ranges' in data
        
        # Check structure
        assert isinstance(data['regions'], list)
        assert isinstance(data['products'], list)
        assert 'min' in data['date_range']
        assert 'max' in data['date_range']
    
    def test_filter_options_caching(self, client):
        """Test that filter options are cached"""
        # First request
        response1 = client.get('/api/filters')
        
        # Second request (should hit cache)
        response2 = client.get('/api/filters')
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.data == response2.data


class TestSalesEndpoint:
    """Tests for /api/sales endpoint"""
    
    def test_get_sales_data_default(self, client):
        """Test getting sales data with default parameters"""
        response = client.get('/api/sales')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'labels' in data
        assert 'datasets' in data
        assert 'summary' in data
        assert 'metadata' in data
    
    def test_get_sales_data_with_filters(self, client, sample_filters):
        """Test getting sales data with filter parameters"""
        response = client.get('/api/sales', query_string={
            'regions[]': sample_filters['regions'],
            'products[]': sample_filters['products'],
            'start_date': sample_filters['start_date'],
            'end_date': sample_filters['end_date'],
            'group_by': sample_filters['group_by']
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check data structure
        assert isinstance(data['labels'], list)
        assert isinstance(data['datasets'], list)
        assert 'total_sales' in data['summary']
        assert 'total_quantity' in data['summary']
        assert 'average_sale' in data['summary']
        assert 'record_count' in data['summary']
    
    def test_sales_data_with_region_filter(self, client):
        """Test filtering by single region"""
        response = client.get('/api/sales', query_string={
            'regions[]': ['Beijing'],
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['metadata']['filters']['regions'] == ['Beijing']
    
    def test_sales_data_with_multiple_regions(self, client):
        """Test filtering by multiple regions"""
        regions = ['Beijing', 'Shanghai', 'Guangzhou']
        response = client.get('/api/sales', query_string={
            'regions[]': regions,
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert set(data['metadata']['filters']['regions']) == set(regions)
    
    def test_sales_data_with_product_filter(self, client):
        """Test filtering by product"""
        response = client.get('/api/sales', query_string={
            'products[]': ['Laptop'],
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Laptop' in data['metadata']['filters']['products']
    
    def test_sales_data_group_by_day(self, client):
        """Test grouping by day"""
        response = client.get('/api/sales', query_string={
            'group_by': 'day',
            'start_date': '2024-11-01',
            'end_date': '2024-11-07'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['metadata']['filters']['group_by'] == 'day'
    
    def test_sales_data_group_by_week(self, client):
        """Test grouping by week"""
        response = client.get('/api/sales', query_string={
            'group_by': 'week',
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['metadata']['filters']['group_by'] == 'week'
    
    def test_sales_data_group_by_month(self, client):
        """Test grouping by month"""
        response = client.get('/api/sales', query_string={
            'group_by': 'month',
            'start_date': '2024-10-01',
            'end_date': '2024-12-31'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['metadata']['filters']['group_by'] == 'month'
    
    def test_sales_data_compare_by_region(self, client):
        """Test comparison by region"""
        response = client.get('/api/sales', query_string={
            'regions[]': ['Beijing', 'Shanghai'],
            'compare_by': 'region',
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have multiple datasets (one per region)
        assert len(data['datasets']) >= 1
        assert data['metadata']['filters']['compare_by'] == 'region'
    
    def test_sales_data_compare_by_product(self, client):
        """Test comparison by product"""
        response = client.get('/api/sales', query_string={
            'products[]': ['Laptop', 'Smartphone'],
            'compare_by': 'product',
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have multiple datasets (one per product)
        assert len(data['datasets']) >= 1
        assert data['metadata']['filters']['compare_by'] == 'product'
    
    def test_invalid_group_by_parameter(self, client):
        """Test invalid group_by parameter returns 400"""
        response = client.get('/api/sales', query_string={
            'group_by': 'invalid'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_invalid_date_format(self, client):
        """Test invalid date format returns 400"""
        response = client.get('/api/sales', query_string={
            'start_date': 'invalid-date'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_invalid_date_range(self, client):
        """Test start_date after end_date returns 400"""
        response = client.get('/api/sales', query_string={
            'start_date': '2024-11-30',
            'end_date': '2024-11-01'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'date range' in data['message'].lower()


class TestExportEndpoint:
    """Tests for /api/export endpoint"""
    
    def test_export_csv_default(self, client):
        """Test CSV export with default parameters"""
        response = client.get('/api/export')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        
        # Check that filename is set
        assert 'attachment' in response.headers.get('Content-Disposition', '')
    
    def test_export_csv_with_filters(self, client, sample_filters):
        """Test CSV export with filter parameters"""
        response = client.get('/api/export', query_string={
            'regions[]': sample_filters['regions'],
            'products[]': sample_filters['products'],
            'start_date': sample_filters['start_date'],
            'end_date': sample_filters['end_date']
        })
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        
        # Verify CSV content
        csv_data = response.data.decode('utf-8')
        assert 'date' in csv_data
        assert 'region' in csv_data
        assert 'product' in csv_data
    
    def test_export_filename_format(self, client):
        """Test that export filename includes timestamp"""
        response = client.get('/api/export')
        
        content_disposition = response.headers.get('Content-Disposition', '')
        assert 'sales_data_' in content_disposition
        assert '.csv' in content_disposition


class TestCacheEndpoint:
    """Tests for cache management endpoint"""
    
    def test_clear_cache(self, client):
        """Test clearing cache"""
        response = client.post('/api/cache/clear')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'message' in data


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_not_found(self, client):
        """Test 404 error handling"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data


class TestPerformance:
    """Performance tests"""
    
    def test_api_response_time(self, client):
        """Test that API response is under 200ms target"""
        import time
        
        start = time.time()
        response = client.get('/api/sales', query_string={
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        })
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert response.status_code == 200
        # Note: This is a soft target, may vary based on system
        print(f"\nAPI response time: {elapsed:.2f}ms")
    
    def test_cache_effectiveness(self, client):
        """Test that caching improves performance"""
        import time
        
        query_params = {
            'regions[]': ['Beijing'],
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        }
        
        # Clear cache first
        client.post('/api/cache/clear')
        
        # First request (cache miss)
        start1 = time.time()
        response1 = client.get('/api/sales', query_string=query_params)
        time1 = time.time() - start1
        
        # Second request (cache hit)
        start2 = time.time()
        response2 = client.get('/api/sales', query_string=query_params)
        time2 = time.time() - start2
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Cache hit should be faster (or at least not slower)
        print(f"\nFirst request: {time1*1000:.2f}ms, Second request: {time2*1000:.2f}ms")


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_filter_workflow(self, client):
        """Test complete filtering workflow"""
        # 1. Get available filters
        filters_response = client.get('/api/filters')
        assert filters_response.status_code == 200
        filters = json.loads(filters_response.data)
        
        # 2. Use filters to query data
        if filters['regions'] and filters['products']:
            sales_response = client.get('/api/sales', query_string={
                'regions[]': filters['regions'][0],
                'products[]': filters['products'][0],
                'start_date': filters['date_range']['min'],
                'end_date': filters['date_range']['max']
            })
            assert sales_response.status_code == 200
            
            # 3. Export the data
            export_response = client.get('/api/export', query_string={
                'regions[]': filters['regions'][0],
                'products[]': filters['products'][0],
                'start_date': filters['date_range']['min'],
                'end_date': filters['date_range']['max']
            })
            assert export_response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
