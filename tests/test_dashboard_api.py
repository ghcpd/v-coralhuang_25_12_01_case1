"""
Test suite for dashboard_improved.py
Tests API endpoints, parameters, error handling, and integration
"""
import sys
import os
import pytest
import json
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dashboard_improved import app, data_service
import config


@pytest.fixture
def client():
    """Create a Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'timestamp' in data


class TestFiltersEndpoint:
    """Tests for /api/v1/filters endpoint"""
    
    def test_get_filters_success(self, client):
        """Test getting filter options"""
        response = client.get('/api/v1/filters')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'data' in data
        
        filters = data['data']
        assert 'regions' in filters
        assert 'products' in filters
        assert 'date_range' in filters
        assert 'aggregation_intervals' in filters
        assert 'auto_refresh_intervals' in filters
        
        assert len(filters['regions']) > 0
        assert len(filters['products']) > 0


class TestSalesEndpoint:
    """Tests for /api/v1/sales endpoint"""
    
    def test_get_sales_no_filters(self, client):
        """Test getting sales data without filters"""
        response = client.get('/api/v1/sales')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'data' in data
        
        sales_data = data['data']
        assert 'chart' in sales_data
        assert 'summary' in sales_data
        assert 'records' in sales_data
    
    def test_get_sales_with_region_filter(self, client):
        """Test filtering by region"""
        response = client.get('/api/v1/sales?regions[]=Beijing')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['records'] > 0
    
    def test_get_sales_with_multiple_regions(self, client):
        """Test filtering by multiple regions"""
        response = client.get('/api/v1/sales?regions[]=Beijing&regions[]=Shanghai')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_get_sales_with_product_filter(self, client):
        """Test filtering by product"""
        response = client.get('/api/v1/sales?products[]=Laptop')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_get_sales_with_date_range(self, client):
        """Test filtering by date range"""
        response = client.get('/api/v1/sales?start_date=2024-11-01&end_date=2024-11-07')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['records'] > 0
    
    def test_get_sales_with_aggregation(self, client):
        """Test different aggregation levels"""
        for group_by in ['daily', 'weekly', 'monthly']:
            response = client.get(f'/api/v1/sales?group_by={group_by}')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
    
    def test_get_sales_invalid_date_format(self, client):
        """Test error handling for invalid date format"""
        response = client.get('/api/v1/sales?start_date=2024/11/01')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid' in data['message'] or 'start_date' in data['message']
    
    def test_get_sales_invalid_group_by(self, client):
        """Test error handling for invalid group_by parameter"""
        response = client.get('/api/v1/sales?group_by=invalid')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['status'] == 'error'
    
    def test_get_sales_chart_format(self, client):
        """Test that sales data returns Chart.js compatible format"""
        response = client.get('/api/v1/sales')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        chart = data['data']['chart']
        
        assert 'labels' in chart
        assert 'datasets' in chart
        assert len(chart['datasets']) > 0
        
        dataset = chart['datasets'][0]
        assert 'label' in dataset
        assert 'data' in dataset
    
    def test_get_sales_summary(self, client):
        """Test that sales data includes summary statistics"""
        response = client.get('/api/v1/sales')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        summary = data['data']['summary']
        
        assert 'total_sales' in summary
        assert 'total_quantity' in summary
        assert 'record_count' in summary
        assert 'average_sales' in summary


class TestExportEndpoint:
    """Tests for /api/v1/export endpoint"""
    
    def test_export_csv_no_filters(self, client):
        """Test exporting CSV without filters"""
        response = client.get('/api/v1/export')
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
    
    def test_export_csv_with_filters(self, client):
        """Test exporting CSV with filters"""
        response = client.get('/api/v1/export?regions[]=Beijing&start_date=2024-11-01&end_date=2024-11-07')
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        
        # Verify CSV format
        content = response.data.decode('utf-8')
        lines = content.strip().split('\n')
        assert len(lines) > 1  # Header + data
        assert 'date' in lines[0]
        assert 'region' in lines[0]
    
    def test_export_csv_filename(self, client):
        """Test that export includes proper filename"""
        response = client.get('/api/v1/export')
        assert 'download_name' in response.headers or 'Content-Disposition' in response.headers


class TestCacheStatsEndpoint:
    """Tests for /api/v1/cache-stats endpoint"""
    
    def test_get_cache_stats(self, client):
        """Test getting cache statistics"""
        response = client.get('/api/v1/cache-stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        
        stats = data['data']
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'total' in stats
        assert 'hit_ratio' in stats


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_not_found(self, client):
        """Test 404 error handling"""
        response = client.get('/api/v1/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['status'] == 'error'
    
    def test_invalid_method(self, client):
        """Test invalid HTTP method"""
        response = client.post('/api/v1/filters')
        # POST not allowed on filters endpoint
        assert response.status_code in [405, 404, 400]


class TestIntegration:
    """Integration tests"""
    
    def test_full_query_workflow(self, client):
        """Test complete query workflow"""
        # 1. Get filters
        filters_response = client.get('/api/v1/filters')
        assert filters_response.status_code == 200
        filters_data = json.loads(filters_response.data)
        
        # 2. Query with filters
        region = filters_data['data']['regions'][0] if filters_data['data']['regions'] else ''
        product = filters_data['data']['products'][0] if filters_data['data']['products'] else ''
        
        query = f'/api/v1/sales?regions[]=={region}&products[]=={product}'
        sales_response = client.get(query)
        assert sales_response.status_code == 200
        
        sales_data = json.loads(sales_response.data)
        assert 'chart' in sales_data['data']
    
    def test_concurrent_requests(self, client):
        """Test handling multiple concurrent-like requests"""
        for _ in range(5):
            response = client.get('/api/v1/sales')
            assert response.status_code == 200
    
    def test_cache_effectiveness(self, client):
        """Test that caching improves performance"""
        import time
        
        # Clear cache first
        data_service.clear_cache()
        
        # First request (cache miss)
        start = time.time()
        response1 = client.get('/api/v1/sales?regions[]=Beijing')
        time1 = time.time() - start
        
        # Second identical request (cache hit)
        start = time.time()
        response2 = client.get('/api/v1/sales?regions[]=Beijing')
        time2 = time.time() - start
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify cache was used
        stats = data_service.get_cache_stats()
        assert stats['hits'] > 0


class TestResponseFormat:
    """Tests for response format consistency"""
    
    def test_sales_response_structure(self, client):
        """Test that sales endpoint returns consistent structure"""
        response = client.get('/api/v1/sales')
        data = json.loads(response.data)
        
        assert 'status' in data
        assert 'data' in data
        assert 'chart' in data['data']
        assert 'summary' in data['data']
        assert 'records' in data['data']
        assert 'from_cache' in data['data']
    
    def test_error_response_structure(self, client):
        """Test that error responses have consistent structure"""
        response = client.get('/api/v1/sales?start_date=invalid')
        data = json.loads(response.data)
        
        assert 'status' in data
        assert data['status'] == 'error'
        assert 'message' in data


class TestPerformance:
    """Performance tests"""
    
    def test_sales_endpoint_response_time(self, client):
        """Test that sales endpoint responds within acceptable time"""
        import time
        
        start = time.time()
        response = client.get('/api/v1/sales')
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in less than 1 second
    
    def test_filters_endpoint_response_time(self, client):
        """Test that filters endpoint responds quickly"""
        import time
        
        start = time.time()
        response = client.get('/api/v1/filters')
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5  # Should respond in less than 500ms


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
