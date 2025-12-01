"""
Sales Data Models
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SalesRecord:
    """Sales record data class"""
    date: datetime
    region: str
    product: str
    sales_amount: float
    quantity: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'region': self.region,
            'product': self.product,
            'sales_amount': self.sales_amount,
            'quantity': self.quantity
        }


@dataclass
class FilterCriteria:
    """Filter criteria class"""
    regions: Optional[List[str]] = None
    products: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.regions is None:
            self.regions = []
        if self.products is None:
            self.products = []
    
    def is_empty(self) -> bool:
        """Check if filter is empty"""
        return (not self.regions and not self.products and 
                not self.start_date and not self.end_date)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'regions': self.regions,
            'products': self.products,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None
        }


@dataclass
class ChartData:
    """Chart data class"""
    labels: List[str]
    datasets: List[dict]
    
    def to_dict(self) -> dict:
        """Convert to Chart.js format"""
        return {
            'labels': self.labels,
            'datasets': self.datasets
        }
