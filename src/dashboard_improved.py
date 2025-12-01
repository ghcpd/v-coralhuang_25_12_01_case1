"""
Enhanced Sales Dashboard Flask Application with API endpoints
Features:
- REST API endpoints for AJAX-based frontend
- Multi-dimension filtering via API
- CSV export functionality
- CORS support for frontend requests
- Caching to reduce response time (< 200ms target)
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
from data_service_improved import DataService
from models import FilterCriteria
import io
import csv as csv_module
import config
import logging

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Load configuration
app.config.from_object(config)

# Enable CORS
CORS(app, origins=config.CORS_ORIGINS, 
     allow_headers=config.CORS_ALLOW_HEADERS,
     methods=config.CORS_METHODS)

# Initialize data service
data_service = DataService(config.DATA_FILE_PATH, cache_ttl=config.CACHE_EXPIRATION_SECONDS)


@app.route('/')
def index():
    """Serve the improved dashboard HTML"""
    return render_template('dashboard_improved.html')


@app.route('/api/v1/filters', methods=['GET'])
def get_filters():
    """
    API Endpoint: Get available filter options
    Returns: JSON with regions, products, and date range
    Response Time Target: < 200ms
    """
    try:
        filters = {
            'regions': data_service.get_available_regions(),
            'products': data_service.get_available_products(),
            'date_range': data_service.get_date_range(),
            'aggregation_intervals': config.AGGREGATION_INTERVALS,
            'auto_refresh_intervals': config.AUTO_REFRESH_INTERVALS
        }
        return jsonify({
            'status': 'success',
            'data': filters
        }), 200
    except Exception as e:
        logger.error(f"Error fetching filters: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch filter options'
        }), 500


@app.route('/api/v1/sales', methods=['GET'])
def get_sales():
    """
    API Endpoint: Get filtered sales data in Chart.js format
    
    Query Parameters:
    - regions: comma-separated region names (or regions[]=region1&regions[]=region2)
    - products: comma-separated product names (or products[]=prod1&products[]=prod2)
    - start_date: YYYY-MM-DD format
    - end_date: YYYY-MM-DD format
    - group_by: 'daily', 'weekly', or 'monthly' (default: 'daily')
    
    Returns: JSON with Chart.js compatible format
    Response Time Target: < 200ms
    """
    try:
        # Parse filter parameters
        regions = _parse_array_param(request.args, 'regions')
        products = _parse_array_param(request.args, 'products')
        
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        group_by = request.args.get('group_by', config.DEFAULT_AGGREGATION)
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid start_date format. Use YYYY-MM-DD'
                }), 400
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid end_date format. Use YYYY-MM-DD'
                }), 400
        
        # Validate group_by parameter
        if group_by not in config.AGGREGATION_INTERVALS:
            return jsonify({
                'status': 'error',
                'message': f'Invalid group_by. Must be one of: {config.AGGREGATION_INTERVALS}'
            }), 400
        
        # Build filter criteria
        criteria = FilterCriteria(
            regions=regions if regions else None,
            products=products if products else None,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get data with caching
        records, from_cache = data_service.get_cached_sales_data(criteria)
        
        # Check record limit
        if len(records) > config.API_MAX_RECORDS:
            logger.warning(f"Result set exceeds limit: {len(records)} > {config.API_MAX_RECORDS}")
            records = records[:config.API_MAX_RECORDS]
        
        # Aggregate data
        aggregated = data_service.aggregate_by_date(records, group_by)
        
        # Format for Chart.js
        chart_data = _format_chart_data(aggregated)
        
        # Calculate summary statistics
        summary = {
            'total_sales': sum(agg['total_sales'] for agg in aggregated.values()),
            'total_quantity': sum(agg['total_quantity'] for agg in aggregated.values()),
            'record_count': len(records),
            'average_sales': round(sum(agg['total_sales'] for agg in aggregated.values()) / len(aggregated) if aggregated else 0, 2)
        }
        
        response_data = {
            'status': 'success',
            'data': {
                'chart': chart_data,
                'summary': summary,
                'records': len(records),
                'from_cache': from_cache
            }
        }
        
        logger.info(f"Sales query: regions={regions}, products={products}, records={len(records)}, cached={from_cache}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error fetching sales data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch sales data'
        }), 500


@app.route('/api/v1/export', methods=['GET'])
def export_sales():
    """
    API Endpoint: Export filtered sales data as CSV
    
    Query Parameters: Same as /api/v1/sales
    
    Returns: CSV file download
    """
    try:
        # Parse filter parameters (same as get_sales)
        regions = _parse_array_param(request.args, 'regions')
        products = _parse_array_param(request.args, 'products')
        
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # Build filter criteria
        criteria = FilterCriteria(
            regions=regions if regions else None,
            products=products if products else None,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get data
        records, _ = data_service.get_cached_sales_data(criteria)
        
        # Check export limit
        if len(records) > config.EXPORT_MAX_ROWS:
            logger.warning(f"Export exceeds limit: {len(records)} > {config.EXPORT_MAX_ROWS}")
            records = records[:config.EXPORT_MAX_ROWS]
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv_module.writer(output)
        
        # Write header
        writer.writerow(['date', 'region', 'product', 'sales_amount', 'quantity'])
        
        # Write data
        for record in records:
            writer.writerow([
                record.date.strftime('%Y-%m-%d'),
                record.region,
                record.product,
                record.sales_amount,
                record.quantity
            ])
        
        # Convert to BytesIO for download
        output.seek(0)
        bytes_output = io.BytesIO(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)
        
        logger.info(f"Export: {len(records)} records exported")
        
        return send_file(
            bytes_output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'sales_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting sales data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to export sales data'
        }), 500


@app.route('/api/v1/cache-stats', methods=['GET'])
def get_cache_stats():
    """Get cache performance statistics"""
    stats = data_service.get_cache_stats()
    return jsonify({
        'status': 'success',
        'data': stats
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    }), 200


def _parse_array_param(request_args, param_name):
    """
    Parse array parameter from request args
    Supports both: param[]=val1&param[]=val2 and param=val1,val2
    """
    # Try array format first (e.g., regions[]=Beijing&regions[]=Shanghai)
    array_values = request_args.getlist(param_name)
    if array_values:
        return array_values
    
    # Try comma-separated format (e.g., regions=Beijing,Shanghai)
    csv_value = request_args.get(param_name, '')
    if csv_value:
        return [v.strip() for v in csv_value.split(',') if v.strip()]
    
    return []


def _format_chart_data(aggregated):
    """Format aggregated data for Chart.js"""
    labels = sorted(aggregated.keys())
    sales_data = [aggregated[label]['total_sales'] for label in labels]
    quantity_data = [aggregated[label]['total_quantity'] for label in labels]
    
    return {
        'labels': labels,
        'datasets': [
            {
                'label': 'Total Sales (USD)',
                'data': sales_data,
                'borderColor': '#007bff',
                'backgroundColor': 'rgba(0, 123, 255, 0.1)',
                'borderWidth': 2,
                'fill': True,
                'tension': 0.3,
                'yAxisID': 'y'
            },
            {
                'label': 'Total Quantity',
                'data': quantity_data,
                'borderColor': '#28a745',
                'backgroundColor': 'rgba(40, 167, 69, 0.1)',
                'borderWidth': 2,
                'fill': True,
                'tension': 0.3,
                'yAxisID': 'y1'
            }
        ]
    }


@app.before_request
def before_request():
    """Log incoming requests"""
    if not request.path.startswith('/static'):
        logger.debug(f"{request.method} {request.path}")


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(e)}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    logger.info("Starting enhanced sales dashboard...")
    logger.info(f"Server: http://{config.HOST}:{config.PORT}")
    logger.info(f"API Base: http://{config.HOST}:{config.PORT}/api/v1")
    
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT,
        use_reloader=config.DEBUG
    )
