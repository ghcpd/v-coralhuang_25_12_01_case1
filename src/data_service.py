"""
Data Service - Query and process sales data
Current version issues:
1. Does not support multi-dimension filtering
2. Only returns raw data, no aggregation support
3. No caching mechanism
4. Chart data format needs frontend processing
"""
import csv
from datetime import datetime, timedelta
from typing import List, Dict
from models import SalesRecord, FilterCriteria


class DataService:
    """Data query service"""
    
    def __init__(self, csv_file_path: str):
        self.data_file = csv_file_path
        self._cache = {}  # Simple memory cache
    
    def get_sales_data(self, criteria: FilterCriteria) -> List[SalesRecord]:
        """
        Get sales data based on filter criteria
        Issue: Only supports single region or product filtering
        """
        all_records = self._load_data()
        
        # Issue 1: Filter logic not flexible enough, only supports single selection
        filtered = []
        for record in all_records:
            # Simple single condition filtering
            if criteria.regions and record.region not in criteria.regions:
                continue
            if criteria.products and record.product not in criteria.products:
                continue
            filtered.append(record)
        
        return filtered
    
    def get_chart_data(self, criteria: FilterCriteria) -> dict:
        """
        Get chart data
        Issue: Returns raw data, frontend needs to aggregate and format
        """
        records = self.get_sales_data(criteria)
        
        # Issue 2: Simply returns raw data, frontend needs complex processing
        return {
            'records': [r.to_dict() for r in records],
            'total': len(records)
        }
    
    def _load_data(self) -> List[SalesRecord]:
        """Load data from CSV"""
        # Issue 3: Re-reads file every time, no caching
        records = []
        with open(self.data_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                records.append(SalesRecord(
                    date=datetime.strptime(row['date'], '%Y-%m-%d'),
                    region=row['region'],
                    product=row['product'],
                    sales_amount=float(row['sales_amount']),
                    quantity=int(row['quantity'])
                ))
        return records
    
    def get_available_regions(self) -> List[str]:
        """Get all available regions"""
        records = self._load_data()
        return sorted(set(r.region for r in records))
    
    def get_available_products(self) -> List[str]:
        """Get all available products"""
        records = self._load_data()
        return sorted(set(r.product for r in records))


def main():
    """Test function"""
    service = DataService('data/sales_data.csv')
    
    # Simple query test
    criteria = FilterCriteria(regions=['Beijing'])
    data = service.get_sales_data(criteria)
    print(f"Found {len(data)} records")
    
    print(f"Available regions: {service.get_available_regions()}")
    print(f"Available products: {service.get_available_products()}")


if __name__ == "__main__":
    main()
