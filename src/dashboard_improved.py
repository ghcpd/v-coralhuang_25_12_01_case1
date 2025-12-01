"""
Flask App - Improved Dashboard with API endpoints for AJAX
"""
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from io import BytesIO
import pandas as pd
from .models import FilterCriteria
from .data_service_improved import DataServiceImproved
from .config import ALLOWED_ORIGINS
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})
service = DataServiceImproved()


@app.route('/')
def index():
    return render_template('dashboard_improved.html')


@app.route('/api/filters')
def api_filters():
    df = service._load_df()
    regions = sorted(df['region'].unique().tolist())
    products = sorted(df['product'].unique().tolist())
    min_date = df['date'].min().strftime('%Y-%m-%d')
    max_date = df['date'].max().strftime('%Y-%m-%d')
    return jsonify({'regions': regions, 'products': products, 'min_date': min_date, 'max_date': max_date})


def _parse_list_param(name: str):
    # Accept either csv param or multiple params like ?regions=A&regions=B
    value = request.args.getlist(name)
    if not value:
        single = request.args.get(name)
        if single:
            return [v.strip() for v in single.split(',') if v.strip()]
    return value


def _parse_date_param(name: str):
    v = request.args.get(name)
    if not v:
        return None
    try:
        return datetime.strptime(v, '%Y-%m-%d')
    except Exception:
        return None


@app.route('/api/sales')
def api_sales():
    regions = _parse_list_param('regions')
    products = _parse_list_param('products')
    start_date = _parse_date_param('start_date')
    end_date = _parse_date_param('end_date')
    group_by = request.args.get('group_by', 'date')

    criteria = FilterCriteria(regions=regions or [], products=products or [])
    criteria.start_date = start_date
    criteria.end_date = end_date

    try:
        resp = service.get_cached_sales_data(criteria, group_by=group_by)
        return jsonify(resp)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export')
def api_export():
    regions = _parse_list_param('regions')
    products = _parse_list_param('products')
    start_date = _parse_date_param('start_date')
    end_date = _parse_date_param('end_date')

    criteria = FilterCriteria(regions=regions or [], products=products or [])
    criteria.start_date = start_date
    criteria.end_date = end_date
    df = service.get_sales_data_filtered(criteria)
    csv_str = df.to_csv(index=False)
    bio = BytesIO(csv_str.encode('utf-8'))
    bio.seek(0)
    return send_file(bio, mimetype='text/csv', download_name='export.csv', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
