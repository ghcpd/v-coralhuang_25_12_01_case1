"""
Improved Flask application with API endpoints and interactive dashboard support.
"""
from __future__ import annotations

import io
import os
from datetime import datetime
from flask import Flask, jsonify, render_template, request, send_file
from flask_caching import Cache
from flask_cors import CORS

from config import Config
from data_service_improved import (
    DataServiceImproved,
    _normalize_filters,
    get_cached_sales_data,
)


def create_app(config_class=Config) -> Flask:
    base_dir = os.path.dirname(__file__)
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )
    app.config.from_object(config_class)

    cache = Cache(app)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    data_service = DataServiceImproved(app.config["CSV_PATH"])

    def parse_filters(args) -> dict:
        # Support both regions[] and regions
        regions = args.getlist("regions[]") or args.getlist("regions")
        products = args.getlist("products[]") or args.getlist("products")
        # Also support comma-separated values
        if len(regions) == 1 and "," in regions[0]:
            regions = [r.strip() for r in regions[0].split(",") if r.strip()]
        if len(products) == 1 and "," in products[0]:
            products = [p.strip() for p in products[0].split(",") if p.strip()]

        start_date = args.get("start_date")
        end_date = args.get("end_date")
        group_by = args.get("group_by", "day")
        # Basic validation of dates
        for d in (start_date, end_date):
            if d:
                try:
                    datetime.fromisoformat(d)
                except ValueError:
                    return None, ("Invalid date format. Use YYYY-MM-DD.", 400)
        filters = _normalize_filters(
            regions=regions,
            products=products,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
        )
        return filters, None

    @app.route("/")
    def index():
        return render_template("dashboard_improved.html")

    @app.route("/api/filters")
    def api_filters():
        options = data_service.get_filter_options()
        return jsonify(options)

    @app.route("/api/sales")
    def api_sales():
        filters, error = parse_filters(request.args)
        if error:
            msg, code = error
            return jsonify({"error": msg}), code

        def compute():
            return data_service.chart_data(filters)

        data = get_cached_sales_data(
            cache=cache, filters=filters, compute_fn=compute, timeout=app.config.get("CACHE_DEFAULT_TIMEOUT")
        )
        return jsonify(data)

    @app.route("/api/export")
    def api_export():
        filters, error = parse_filters(request.args)
        if error:
            msg, code = error
            return jsonify({"error": msg}), code
        csv_str = data_service.export_csv(filters)
        return send_file(
            io.BytesIO(csv_str.encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name="sales_export.csv",
        )

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
