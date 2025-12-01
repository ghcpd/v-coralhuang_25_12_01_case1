"""
Flask-based improved sales dashboard with APIs and caching
"""
from flask import Flask, render_template, request, jsonify, send_file
try:
    from flask_cors import CORS
except Exception:
    # Provide a no-op fallback so tests can run when Flask-Cors is not installed
    def CORS(app, origins=None):
        return None
try:
    from flask_caching import Cache
except Exception:
    Cache = None
from datetime import datetime
import io

from data_service_improved import DataServiceImproved
from config import get_cache_config, CORS_ORIGINS, EXPORT_CSV_FILENAME
from models import FilterCriteria

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app, origins=CORS_ORIGINS)
if Cache is not None:
    cache = Cache(app, config=get_cache_config())
else:
    cache = None

# Instantiate data service
data_service = DataServiceImproved('data/sales_data.csv')


@app.route('/improved')
def improved_ui():
    """Serve the improved interactive dashboard UI"""
    filters = data_service.get_available_filters()
    return render_template('dashboard_improved.html', filters=filters)


def parse_params(req) -> FilterCriteria:
    regions = req.args.getlist('regions[]') or req.args.getlist('regions') or []
    products = req.args.getlist('products[]') or req.args.getlist('products') or []
    start_date = req.args.get('start_date')
    end_date = req.args.get('end_date')
    fc = FilterCriteria(regions=regions, products=products)
    if start_date:
        fc.start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        fc.end_date = datetime.strptime(end_date, '%Y-%m-%d')
    return fc


@app.route('/api/filters', methods=['GET'])
def api_filters():
    """Return filter options for the UI."""
    try:
        available = data_service.get_available_filters()
        return jsonify(available)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sales', methods=['GET'])
def api_sales():
    """Return aggregated sales data in Chart.js format."""
    try:
        group_by = request.args.get('group_by', 'date')
        fc = parse_params(request)
        result = data_service.get_cached_sales_data(fc, group_by=group_by)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export', methods=['GET'])
def api_export():
    """Export filtered data as CSV"""
    try:
        fc = parse_params(request)
        buf, filename = data_service.export_csv(fc)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name=filename or EXPORT_CSV_FILENAME, mimetype='text/csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    return {'status': 'ok'}


if __name__ == '__main__':
    print('Starting improved dashboard at http://localhost:5000/improved')
    app.run(debug=True, port=5000)
