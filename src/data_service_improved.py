"""
Improved Data Service - supports multi-dimension filtering, aggregation, caching.
"""
from __future__ import annotations

import hashlib
import json
import csv
from io import StringIO
from datetime import datetime, timedelta
from typing import Callable, Dict, Iterable, List, Optional


def _normalize_filters(
    regions: Optional[Iterable[str]] = None,
    products: Optional[Iterable[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = "day",
) -> Dict:
    return {
        "regions": sorted(set(regions)) if regions else [],
        "products": sorted(set(products)) if products else [],
        "start_date": start_date,
        "end_date": end_date,
        "group_by": group_by.lower() if group_by else "day",
    }


def _cache_key_from_filters(prefix: str, filters: Dict) -> str:
    """Create a deterministic cache key from filters."""
    # Ensure deterministic ordering
    key_json = json.dumps(filters, sort_keys=True)
    digest = hashlib.md5(key_json.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def get_sales_data_filtered(
    records: List[Dict],
    regions: Optional[Iterable[str]] = None,
    products: Optional[Iterable[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict]:
    """Filter sales data by regions, products, and date range."""
    filtered: List[Dict] = []
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    for rec in records:
        if regions and rec["region"] not in regions:
            continue
        if products and rec["product"] not in products:
            continue
        if start_dt and rec["date"] < start_dt:
            continue
        if end_dt and rec["date"] > end_dt:
            continue
        filtered.append(rec)
    return filtered


def _label_for_group(date_obj: datetime, group_by: str) -> str:
    if group_by == "week":
        week_start = date_obj - timedelta(days=date_obj.weekday())
        return week_start.strftime("%Y-%m-%d")
    if group_by == "month":
        return date_obj.strftime("%Y-%m-01")
    return date_obj.strftime("%Y-%m-%d")


def aggregate_by_date(records: List[Dict], group_by: str = "day") -> List[Dict]:
    """Aggregate data by date with given granularity: day, week, month."""
    if not records:
        return []
    group_by = group_by.lower()
    agg: Dict[str, Dict[str, float]] = {}
    for rec in records:
        label = _label_for_group(rec["date"], group_by)
        entry = agg.setdefault(label, {"sales_amount": 0.0, "quantity": 0})
        entry["sales_amount"] += rec["sales_amount"]
        entry["quantity"] += rec["quantity"]
    # Sort labels chronologically
    def parse_label(label: str) -> datetime:
        return datetime.fromisoformat(label)

    return [
        {
            "date": label,
            "sales_amount": round(values["sales_amount"], 2),
            "quantity": values["quantity"],
        }
        for label, values in sorted(agg.items(), key=lambda kv: parse_label(kv[0]))
    ]


def get_comparison_data(records: List[Dict], group_by: str = "day") -> Dict:
    """Return Chart.js datasets for each region-product combination."""
    if not records:
        return {"labels": [], "datasets": []}

    # Gather all labels across groups
    all_labels = set()
    grouped: Dict[tuple, List[Dict]] = {}
    for rec in records:
        key = (rec["region"], rec["product"])
        grouped.setdefault(key, []).append(rec)
    for rec in records:
        all_labels.add(_label_for_group(rec["date"], group_by))

    sorted_labels = sorted(all_labels, key=lambda d: datetime.fromisoformat(d))

    datasets = []
    for (region, product), recs in grouped.items():
        agg = aggregate_by_date(recs, group_by)
        # Map label -> sales amount
        agg_map = {a["date"]: a["sales_amount"] for a in agg}
        series = [round(agg_map.get(label, 0.0), 2) for label in sorted_labels]
        datasets.append({"label": f"{region} - {product}", "data": series})
    return {"labels": sorted_labels, "datasets": datasets}


def summarize(records: List[Dict]) -> Dict:
    if not records:
        return {
            "total_records": 0,
            "total_sales": 0.0,
            "total_quantity": 0,
            "avg_order_value": 0.0,
        }
    total_sales = sum(rec["sales_amount"] for rec in records)
    total_quantity = sum(rec["quantity"] for rec in records)
    avg_order_value = total_sales / len(records) if records else 0.0
    return {
        "total_records": len(records),
        "total_sales": round(total_sales, 2),
        "total_quantity": int(total_quantity),
        "avg_order_value": round(avg_order_value, 2),
    }


def get_cached_sales_data(
    cache,
    filters: Dict,
    compute_fn: Callable[[], Dict],
    timeout: Optional[int] = None,
) -> Dict:
    key = _cache_key_from_filters("sales", filters)
    cached = cache.get(key)
    if cached is not None:
        return cached
    data = compute_fn()
    cache.set(key, data, timeout=timeout)
    return data


class DataServiceImproved:
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self._records: Optional[List[Dict]] = None

    def load_data(self) -> List[Dict]:
        if self._records is None:
            records: List[Dict] = []
            with open(self.csv_file_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(
                        {
                            "date": datetime.fromisoformat(row["date"]),
                            "region": row["region"],
                            "product": row["product"],
                            "sales_amount": float(row["sales_amount"]),
                            "quantity": int(row["quantity"]),
                        }
                    )
            self._records = records
        # Return a shallow copy
        return list(self._records)

    def get_filter_options(self) -> Dict:
        records = self.load_data()
        regions = sorted({r["region"] for r in records}) if records else []
        products = sorted({r["product"] for r in records}) if records else []
        dates = [r["date"] for r in records]
        return {
            "regions": regions,
            "products": products,
            "date_range": {
                "min": min(dates).strftime("%Y-%m-%d") if dates else None,
                "max": max(dates).strftime("%Y-%m-%d") if dates else None,
            },
            "group_by_options": ["day", "week", "month"],
        }

    def chart_data(self, filters: Dict) -> Dict:
        records = self.load_data()
        filtered = get_sales_data_filtered(
            records,
            regions=filters.get("regions"),
            products=filters.get("products"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
        )
        chart = get_comparison_data(filtered, filters.get("group_by", "day"))
        preview = sorted(filtered, key=lambda r: r["date"], reverse=True)[:10]
        # Convert dates to string for output
        preview_out = [
            {
                **rec,
                "date": rec["date"].strftime("%Y-%m-%d"),
            }
            for rec in preview
        ]
        return {
            **chart,
            "summary": summarize(filtered),
            "preview": preview_out,
        }

    def export_csv(self, filters: Dict) -> str:
        records = self.load_data()
        filtered = get_sales_data_filtered(
            records,
            regions=filters.get("regions"),
            products=filters.get("products"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
        )
        output = StringIO()
        fieldnames = ["date", "region", "product", "sales_amount", "quantity"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for rec in filtered:
            writer.writerow(
                {
                    "date": rec["date"].strftime("%Y-%m-%d"),
                    "region": rec["region"],
                    "product": rec["product"],
                    "sales_amount": rec["sales_amount"],
                    "quantity": rec["quantity"],
                }
            )
        return output.getvalue()
