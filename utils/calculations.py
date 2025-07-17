# File: calculations.py
# Location: InvoiceGeneratorPro/utils/calculations.py

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Union, List, Optional
from datetime import datetime, timedelta

from config import CURRENCY_SYMBOLS, DEFAULT_TAX_RATES, MIN_AMOUNT, MAX_AMOUNT

class CalculationEngine:
    """Handles all financial calculations for invoices"""
    
    @staticmethod
    def calculate_line_total(quantity: float, rate: float) -> float:
        """Calculate total for a single line item"""
        try:
            # Use Decimal for precise financial calculations
            qty_decimal = Decimal(str(quantity))
            rate_decimal = Decimal(str(rate))
            total = qty_decimal * rate_decimal
            
            # Round to 2 decimal places
            return float(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def calculate_subtotal(line_totals: List[float]) -> float:
        """Calculate subtotal from list of line item totals"""
        try:
            subtotal = Decimal('0.00')
            for total in line_totals:
                subtotal += Decimal(str(total))
            
            return float(subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def calculate_tax_amount(subtotal: float, tax_rate: float) -> float:
        """Calculate tax amount from subtotal and tax rate"""
        try:
            subtotal_decimal = Decimal(str(subtotal))
            tax_rate_decimal = Decimal(str(tax_rate))
            tax_amount = subtotal_decimal * tax_rate_decimal
            
            return float(tax_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def calculate_total(subtotal: float, tax_amount: float) -> float:
        """Calculate final total"""
        try:
            subtotal_decimal = Decimal(str(subtotal))
            tax_decimal = Decimal(str(tax_amount))
            total = subtotal_decimal + tax_decimal
            
            return float(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def calculate_invoice_totals(items: List[dict]) -> dict:
        """Calculate all totals for an invoice given list of items"""
        line_totals = []
        
        for item in items:
            quantity = item.get('quantity', 0)
            rate = item.get('rate', 0)
            line_total = CalculationEngine.calculate_line_total(quantity, rate)
            line_totals.append(line_total)
        
        subtotal = CalculationEngine.calculate_subtotal(line_totals)
        
        return {
            'line_totals': line_totals,
            'subtotal': subtotal
        }

class CurrencyFormatter:
    """Handles currency formatting and display"""
    
    @staticmethod
    def format_currency(amount: float, currency: str = "USD") -> str:
        """Format amount as currency string"""
        try:
            symbol = CURRENCY_SYMBOLS.get(currency, "$")
            
            # Handle negative amounts
            if amount < 0:
                return f"-{symbol}{abs(amount):,.2f}"
            else:
                return f"{symbol}{amount:,.2f}"
        except (ValueError, TypeError):
            return f"{CURRENCY_SYMBOLS.get(currency, '$')}0.00"
    
    @staticmethod
    def format_percentage(rate: float) -> str:
        """Format decimal rate as percentage"""
        try:
            return f"{rate * 100:.2f}%"
        except (ValueError, TypeError):
            return "0.00%"
    
    @staticmethod
    def parse_currency_input(input_str: str) -> float:
        """Parse user input string to float amount"""
        if not input_str:
            return 0.0
        
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[^\d.-]', '', str(input_str))
        
        try:
            amount = float(cleaned)
            return round(amount, 2)
        except ValueError:
            return 0.0
    
    @staticmethod
    def parse_percentage_input(input_str: str) -> float:
        """Parse percentage input to decimal rate"""
        if not input_str:
            return 0.0
        
        # Remove % symbol and whitespace
        cleaned = re.sub(r'[^\d.-]', '', str(input_str))
        
        try:
            percentage = float(cleaned)
            # Convert percentage to decimal (e.g., 7.5% -> 0.075)
            return round(percentage / 100, 4)
        except ValueError:
            return 0.0

class DateCalculator:
    """Handles date calculations for invoices"""
    
    @staticmethod
    def calculate_due_date(invoice_date: datetime, payment_terms: str) -> datetime:
        """Calculate due date based on payment terms"""
        if not invoice_date:
            invoice_date = datetime.now()
        
        # Parse payment terms
        if payment_terms.startswith("Net "):
            try:
                days = int(payment_terms.split()[1])
                return invoice_date + timedelta(days=days)
            except (ValueError, IndexError):
                return invoice_date + timedelta(days=30)  # Default to 30 days
        elif payment_terms == "Due on Receipt":
            return invoice_date
        else:
            return invoice_date + timedelta(days=30)  # Default
    
    @staticmethod
    def days_between(start_date: datetime, end_date: datetime) -> int:
        """Calculate days between two dates"""
        if not start_date or not end_date:
            return 0
        
        delta = end_date.date() - start_date.date()
        return delta.days
    
    @staticmethod
    def is_overdue(due_date: datetime) -> bool:
        """Check if a date is overdue"""
        if not due_date:
            return False
        
        return datetime.now().date() > due_date.date()
    
    @staticmethod
    def format_date_for_display(date_obj: Optional[datetime], format_str: str = "%B %d, %Y") -> str:
        """Format date for display"""
        if not date_obj:
            return ""
        
        try:
            return date_obj.strftime(format_str)
        except (ValueError, AttributeError):
            return ""

class ValidationEngine:
    """Validates financial inputs and calculations"""
    
    @staticmethod
    def validate_amount(amount: Union[str, float]) -> tuple[bool, str]:
        """Validate monetary amount"""
        try:
            if isinstance(amount, str):
                parsed_amount = CurrencyFormatter.parse_currency_input(amount)
            else:
                parsed_amount = float(amount)
            
            if parsed_amount < MIN_AMOUNT:
                return False, f"Amount must be at least ${MIN_AMOUNT:.2f}"
            
            if parsed_amount > MAX_AMOUNT:
                return False, f"Amount cannot exceed ${MAX_AMOUNT:,.2f}"
            
            return True, ""
        except (ValueError, TypeError):
            return False, "Invalid amount format"
    
    @staticmethod
    def validate_quantity(quantity: Union[str, float]) -> tuple[bool, str]:
        """Validate quantity input"""
        try:
            qty = float(quantity) if isinstance(quantity, str) else quantity
            
            if qty <= 0:
                return False, "Quantity must be greater than 0"
            
            if qty > 10000:
                return False, "Quantity cannot exceed 10,000"
            
            return True, ""
        except (ValueError, TypeError):
            return False, "Invalid quantity format"
    
    @staticmethod
    def validate_tax_rate(tax_rate: Union[str, float]) -> tuple[bool, str]:
        """Validate tax rate input"""
        try:
            if isinstance(tax_rate, str):
                rate = CurrencyFormatter.parse_percentage_input(tax_rate)
            else:
                rate = float(tax_rate)
            
            if rate < 0:
                return False, "Tax rate cannot be negative"
            
            if rate > 1:  # 100%
                return False, "Tax rate cannot exceed 100%"
            
            return True, ""
        except (ValueError, TypeError):
            return False, "Invalid tax rate format"
    
    @staticmethod
    def validate_invoice_items(items: List[dict]) -> tuple[bool, str]:
        """Validate all items in an invoice"""
        if not items:
            return False, "Invoice must contain at least one item"
        
        for i, item in enumerate(items, 1):
            # Validate description
            if not item.get('description', '').strip():
                return False, f"Item {i}: Description is required"
            
            # Validate quantity
            is_valid, error = ValidationEngine.validate_quantity(item.get('quantity', 0))
            if not is_valid:
                return False, f"Item {i}: {error}"
            
            # Validate rate
            is_valid, error = ValidationEngine.validate_amount(item.get('rate', 0))
            if not is_valid:
                return False, f"Item {i}: {error}"
        
        return True, ""

class TaxCalculator:
    """Specialized tax calculations"""
    
    @staticmethod
    def get_tax_rate_by_name(tax_name: str) -> float:
        """Get tax rate decimal from tax name"""
        return DEFAULT_TAX_RATES.get(tax_name, 0.0)
    
    @staticmethod
    def get_available_tax_rates() -> dict:
        """Get all available tax rates"""
        return DEFAULT_TAX_RATES.copy()
    
    @staticmethod
    def calculate_tax_breakdown(subtotal: float, tax_rate: float) -> dict:
        """Calculate detailed tax breakdown"""
        tax_amount = CalculationEngine.calculate_tax_amount(subtotal, tax_rate)
        total = CalculationEngine.calculate_total(subtotal, tax_amount)
        
        return {
            'subtotal': subtotal,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total': total,
            'tax_percentage': tax_rate * 100
        }

# Utility functions for quick access
def format_money(amount: float, currency: str = "USD") -> str:
    """Quick money formatting function"""
    return CurrencyFormatter.format_currency(amount, currency)

def parse_money(input_str: str) -> float:
    """Quick money parsing function"""
    return CurrencyFormatter.parse_currency_input(input_str)

def validate_money(amount: Union[str, float]) -> bool:
    """Quick money validation function"""
    is_valid, _ = ValidationEngine.validate_amount(amount)
    return is_valid

def calculate_invoice_total(items: List[dict], tax_rate: float = 0.0) -> dict:
    """Quick invoice total calculation"""
    totals = CalculationEngine.calculate_invoice_totals(items)
    subtotal = totals['subtotal']
    tax_amount = CalculationEngine.calculate_tax_amount(subtotal, tax_rate)
    total = CalculationEngine.calculate_total(subtotal, tax_amount)
    
    return {
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'total': total,
        'line_totals': totals['line_totals']
    }