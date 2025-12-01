"""
Sales Dashboard Flask Application
Current version issues:
1. Uses traditional form submission, refreshes entire page each time
2. Only supports single selection filtering, cannot do multi-dimension comparison
3. Returns static HTML, cannot interact dynamically
4. No API endpoint for frontend calls
"""
from flask import Flask, render_template, request
from datetime import datetime, timedelta
from data_service import DataService, FilterCriteria

app = Flask(__name__)
data_service = DataService('data/sales_data.csv')


@app.route('/')
def index():
    """
    Main page route
    Issue: Uses traditional approach, needs full page refresh for each filter
    """
    # Issue 1: Can only get single filter value from form
    region = request.args.get('region', '')
    product = request.args.get('product', '')
    time_range = request.args.get('time_range', '7days')
    
    # Issue 2: Does not support multi-select
    criteria = FilterCriteria(
        regions=[region] if region else [],
        products=[product] if product else []
    )
    
    # Set time range
    if time_range == '7days':
        criteria.start_date = datetime.now() - timedelta(days=7)
    elif time_range == '30days':
        criteria.start_date = datetime.now() - timedelta(days=30)
    
    criteria.end_date = datetime.now()
    
    # Get data
    data = data_service.get_chart_data(criteria)
    
    # Get filter options
    regions = data_service.get_available_regions()
    products = data_service.get_available_products()
    
    # Issue 3: Returns complete HTML page, cannot implement partial refresh
    return render_template('dashboard.html',
                         data=data,
                         regions=regions,
                         products=products,
                         selected_region=region,
                         selected_product=product,
                         selected_time=time_range)


@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok'}


if __name__ == '__main__':
    print("Starting sales dashboard...")
    print("Visit http://localhost:5000")
    print("Current issue: Each filter requires full page refresh, poor experience")
    app.run(debug=True, port=5000)
