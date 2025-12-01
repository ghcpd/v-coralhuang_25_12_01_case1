"""
Improved Sales Dashboard Flask Application
Adds API endpoints and AJAX-friendly operations.
"""
from flask import Flask, render_template, request, jsonify, send_file, Response
try:
    from flask_cors import CORS
except Exception:
    # Minimal fallback stub
    def CORS(app, origins=None):
        return None

try:
    from flask_caching import Cache
except Exception:
    # Simple in-memory cache fallback
    class Cache:  # type: ignore
        def __init__(self, app=None):
            self._cache = {}
        def init_app(self, app):
            return None
        def get(self, key):
            return self._cache.get(key)
        def set(self, key, value, timeout=None):
            self._cache[key] = value
import io
import csv
from datetime import datetime
from src.config import DEBUG, CACHE_TYPE, CACHE_DEFAULT_TIMEOUT, CORS_ORIGINS, DATA_CSV_PATH
from src.data_service_improved import DataServiceImproved
from src.models import FilterCriteria

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object('src.config')
app.config['CACHE_TYPE'] = CACHE_TYPE
app.config['CACHE_DEFAULT_TIMEOUT'] = CACHE_DEFAULT_TIMEOUT
cache = Cache(app)
CORS(app, origins=CORS_ORIGINS)

# Initialize improved data service with cache
data_service = DataServiceImproved(DATA_CSV_PATH, cache)


@app.route('/')
def index():
    """Render improved dashboard page"""
    return render_template('dashboard_improved.html')


@app.route('/api/filters', methods=['GET'])
def api_filters():
    """Return available filters (regions, products, date range)"""
    df = data_service._load_dataframe()
    # Support both pandas DataFrame and fallback list-of-dicts
    if hasattr(df, 'columns'):
        regions = sorted(df['region'].unique().tolist())
        products = sorted(df['product'].unique().tolist())
        dates = df['date'].sort_values()
        start_date = dates.min().strftime('%Y-%m-%d') if not dates.empty else None
        end_date = dates.max().strftime('%Y-%m-%d') if not dates.empty else None
    else:
        regions = sorted(set(r['region'] for r in df))
        products = sorted(set(r['product'] for r in df))
        dates = sorted(r['date'] for r in df)
        start_date = dates[0].strftime('%Y-%m-%d') if dates else None
        end_date = dates[-1].strftime('%Y-%m-%d') if dates else None
    return jsonify({'regions': regions, 'products': products, 'start_date': start_date, 'end_date': end_date})


@app.route('/api/sales', methods=['GET'])
def api_sales():
    """Return sales data for Chart.js based on filters, supports JSON"""
    # Parse multi-select params
    regions = request.args.getlist('regions[]') or request.args.getlist('regions')
    products = request.args.getlist('products[]') or request.args.getlist('products')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_by = request.args.get('group_by', 'date')

    crit = FilterCriteria(regions=regions, products=products)
    crit.start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    crit.end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

    try:
        data = data_service.get_cached_sales_data(crit, group_by)
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400

    # add a summary
    return jsonify(data)


@app.route('/api/export', methods=['GET'])
def api_export():
    """Export filtered data as CSV"""
    regions = request.args.getlist('regions[]') or request.args.getlist('regions')
    products = request.args.getlist('products[]') or request.args.getlist('products')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    crit = FilterCriteria(regions=regions, products=products)
    crit.start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    crit.end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

    df = data_service.get_sales_data_filtered(crit)

    # Build CSV in-memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['date', 'region', 'product', 'sales_amount', 'quantity'])
    if hasattr(df, 'iterrows'):
        for _, row in df.iterrows():
            writer.writerow([row['date'].strftime('%Y-%m-%d'), row['region'], row['product'], row['sales_amount'], int(row['quantity'])])
    else:
        for row in df:
            writer.writerow([row['date'].strftime('%Y-%m-%d'), row['region'], row['product'], row['sales_amount'], int(row['quantity'])])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename="sales_export.csv"'
    })


@app.route('/health')
def health():
    return {'status': 'ok'}


if __name__ == '__main__':
    app.run(debug=DEBUG, port=5001)
