"""
Improved Sales Dashboard Flask Application
Features:
1. RESTful API endpoints for AJAX calls
2. Multi-dimension filtering support
3. Caching for performance
4. CORS support for cross-origin requests
5. CSV export functionality
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_caching import Cache
from flask_cors import CORS
from datetime import datetime, timedelta
from io import StringIO, BytesIO
import csv

from data_service_improved import DataServiceImproved
from config import get_config

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = 'development'  # Can be set via environment variable
config = get_config(env)
app.config.from_object(config)

# Initialize extensions
cache = Cache(app)
CORS(app, origins=config.CORS_ORIGINS)

# Initialize data service
data_service = DataServiceImproved(app.config['DATA_FILE_PATH'], cache=cache)


@app.route('/')
def index():
    """
    Main dashboard page - serves the improved HTML template
    """
    return render_template('dashboard_improved.html')


@app.route('/api/sales', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_sales_data():
    """
    API endpoint: Get filtered sales data
    
    Query Parameters:
        regions[]: List of regions (can be multiple)
        products[]: List of products (can be multiple)
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        group_by: Grouping level ('day', 'week', 'month')
        compare_by: Comparison dimension ('region', 'product', 'none')
    
    Returns:
        JSON response with chart data and summary statistics
    """
    try:
        # Parse filter parameters
        regions = request.args.getlist('regions[]')
        products = request.args.getlist('products[]')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')
        compare_by = request.args.get('compare_by', 'none')
        
        # Validate group_by parameter
        if group_by not in ['day', 'week', 'month']:
            return jsonify({
                'error': 'Invalid group_by parameter',
                'message': 'group_by must be one of: day, week, month'
            }), 400
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'error': 'Invalid start_date format',
                    'message': 'Date must be in YYYY-MM-DD format'
                }), 400
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'error': 'Invalid end_date format',
                    'message': 'Date must be in YYYY-MM-DD format'
                }), 400
        
        # Set default date range if not provided (last 30 days)
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Validate date range
        if start_date > end_date:
            return jsonify({
                'error': 'Invalid date range',
                'message': 'start_date must be before end_date'
            }), 400
        
        # Get data based on comparison mode
        if compare_by in ['region', 'product']:
            # Comparison mode
            chart_data = data_service.get_comparison_data(
                regions=regions if regions else None,
                products=products if products else None,
                start_date=start_date,
                end_date=end_date,
                group_by=group_by,
                compare_by=compare_by
            )
            
            # Get records for summary
            records = data_service.get_sales_data_filtered(
                regions=regions if regions else None,
                products=products if products else None,
                start_date=start_date,
                end_date=end_date
            )
            summary = data_service._calculate_summary(records)
            
            response = {
                'labels': chart_data.labels,
                'datasets': chart_data.datasets,
                'summary': summary,
                'metadata': {
                    'record_count': len(records),
                    'filters': {
                        'regions': regions,
                        'products': products,
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d'),
                        'group_by': group_by,
                        'compare_by': compare_by
                    }
                }
            }
        else:
            # Standard mode
            result = data_service.get_cached_sales_data(
                regions=regions if regions else None,
                products=products if products else None,
                start_date=start_date,
                end_date=end_date,
                group_by=group_by
            )
            
            response = {
                'labels': result['chart']['labels'],
                'datasets': result['chart']['datasets'],
                'summary': result['summary'],
                'metadata': {
                    **result['metadata'],
                    'filters': {
                        **result['metadata']['filters'],
                        'group_by': group_by
                    }
                }
            }
        
        return jsonify(response), 200
    
    except Exception as e:
        app.logger.error(f"Error in /api/sales: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/api/filters', methods=['GET'])
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_filter_options():
    """
    API endpoint: Get available filter options
    
    Returns:
        JSON response with available regions, products, and date ranges
    """
    try:
        regions = data_service.get_available_regions()
        products = data_service.get_available_products()
        min_date, max_date = data_service.get_date_range()
        
        return jsonify({
            'regions': regions,
            'products': products,
            'date_range': {
                'min': min_date.strftime('%Y-%m-%d'),
                'max': max_date.strftime('%Y-%m-%d')
            },
            'quick_ranges': [
                {'label': 'Last 7 days', 'value': '7days'},
                {'label': 'Last 30 days', 'value': '30days'},
                {'label': 'Last 90 days', 'value': '90days'},
                {'label': 'This month', 'value': 'month'},
                {'label': 'Custom', 'value': 'custom'}
            ]
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error in /api/filters: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/api/export', methods=['GET'])
def export_csv():
    """
    API endpoint: Export filtered data as CSV
    
    Query Parameters:
        Same as /api/sales endpoint
    
    Returns:
        CSV file download
    """
    try:
        # Parse filter parameters (same as /api/sales)
        regions = request.args.getlist('regions[]')
        products = request.args.getlist('products[]')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # Set default date range
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Get export data
        export_data = data_service.export_to_csv(
            regions=regions if regions else None,
            products=products if products else None,
            start_date=start_date,
            end_date=end_date
        )
        
        # Check export limit
        if len(export_data) > app.config['EXPORT_MAX_ROWS']:
            return jsonify({
                'error': 'Export limit exceeded',
                'message': f'Cannot export more than {app.config["EXPORT_MAX_ROWS"]} rows'
            }), 400
        
        # Create CSV in memory
        output = StringIO()
        if export_data:
            fieldnames = export_data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(export_data)
        
        # Convert to bytes for download
        csv_bytes = BytesIO()
        csv_bytes.write(output.getvalue().encode('utf-8'))
        csv_bytes.seek(0)
        
        # Generate filename with timestamp
        filename = f'sales_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        app.logger.error(f"Error in /api/export: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0-improved'
    }), 200


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached data (useful for development/testing)"""
    try:
        cache.clear()
        return jsonify({
            'message': 'Cache cleared successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'Failed to clear cache',
            'message': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Internal error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Improved Sales Dashboard")
    print("=" * 60)
    print(f"Environment: {env}")
    print(f"Cache Type: {app.config['CACHE_TYPE']}")
    print(f"Data File: {app.config['DATA_FILE_PATH']}")
    print()
    print("📊 Available Endpoints:")
    print("  • Dashboard:     http://localhost:5000")
    print("  • API Sales:     http://localhost:5000/api/sales")
    print("  • API Filters:   http://localhost:5000/api/filters")
    print("  • API Export:    http://localhost:5000/api/export")
    print("  • Health Check:  http://localhost:5000/health")
    print()
    print("✨ Features:")
    print("  ✓ Multi-dimension filtering")
    print("  ✓ AJAX partial refresh")
    print("  ✓ Interactive charts")
    print("  ✓ Auto-refresh capability")
    print("  ✓ CSV export")
    print("  ✓ Response caching")
    print("=" * 60)
    
    app.run(debug=True, port=5000)
