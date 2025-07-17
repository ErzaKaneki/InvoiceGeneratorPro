# File: models.py
# Location: InvoiceGeneratorPro/database/models.py

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
import json

@dataclass
class Client:
    """Client/Customer data model"""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = ""
    created_date: Optional[datetime] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.now()
    
    @property
    def full_address(self) -> str:
        """Returns formatted full address"""
        address_parts = []
        if self.address:
            address_parts.append(self.address)
        
        city_state_zip = []
        if self.city:
            city_state_zip.append(self.city)
        if self.state:
            city_state_zip.append(self.state)
        if self.zip_code:
            city_state_zip.append(self.zip_code)
        
        if city_state_zip:
            address_parts.append(", ".join(city_state_zip))
        
        if self.country:
            address_parts.append(self.country)
        
        return "\n".join(address_parts)
    
    def to_dict(self) -> dict:
        """Convert client to dictionary for database storage"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'country': self.country,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Client':
        """Create client from dictionary"""
        client = cls(**{k: v for k, v in data.items() if k != 'created_date'})
        if data.get('created_date'):
            client.created_date = datetime.fromisoformat(data['created_date'])
        return client

@dataclass
class InvoiceItem:
    """Individual line item on an invoice"""
    id: Optional[int] = None
    description: str = ""
    quantity: float = 1.0
    rate: float = 0.0
    amount: float = 0.0
    
    def __post_init__(self):
        # Auto-calculate amount if not provided
        if self.amount == 0.0:
            self.amount = self.quantity * self.rate
    
    @property
    def total(self) -> float:
        """Calculate total for this line item"""
        return round(self.quantity * self.rate, 2)
    
    def to_dict(self) -> dict:
        """Convert item to dictionary"""
        return {
            'id': self.id,
            'description': self.description,
            'quantity': self.quantity,
            'rate': self.rate,
            'amount': self.total
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'InvoiceItem':
        """Create item from dictionary"""
        return cls(**data)

@dataclass
class Invoice:
    """Main invoice data model"""
    id: Optional[int] = None
    invoice_number: str = ""
    client_id: int = 0
    client: Optional[Client] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: str = "Draft"
    items: List[InvoiceItem] = field(default_factory=list)
    subtotal: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    notes: str = ""
    payment_terms: str = "Net 30"
    currency: str = "USD"
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    
    # Company information (can be overridden per invoice)
    company_name: str = ""
    company_address: str = ""
    company_phone: str = ""
    company_email: str = ""
    company_website: str = ""
    
    def __post_init__(self):
        if self.invoice_date is None:
            self.invoice_date = datetime.now()
        if self.due_date is None:
            self.due_date = self.invoice_date + timedelta(days=30)
        if self.created_date is None:
            self.created_date = datetime.now()
        self.updated_date = datetime.now()
        
        # Calculate totals if items exist
        if self.items:
            self.calculate_totals()
    
    def add_item(self, item: InvoiceItem):
        """Add an item to the invoice"""
        self.items.append(item)
        self.calculate_totals()
    
    def remove_item(self, item_index: int):
        """Remove an item from the invoice"""
        if 0 <= item_index < len(self.items):
            self.items.pop(item_index)
            self.calculate_totals()
    
    def calculate_totals(self):
        """Calculate subtotal, tax, and total amounts"""
        self.subtotal = round(sum(item.total for item in self.items), 2)
        self.tax_amount = round(self.subtotal * self.tax_rate, 2)
        self.total = round(self.subtotal + self.tax_amount, 2)
        self.updated_date = datetime.now()
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        return (self.status == "Sent" and 
                self.due_date is not None and 
                datetime.now().date() > self.due_date.date())
    
    @property
    def days_until_due(self) -> int:
        """Calculate days until due (negative if overdue)"""
        if not self.due_date:
            return 0
        delta = self.due_date.date() - datetime.now().date()
        return delta.days
    
    @property
    def formatted_invoice_number(self) -> str:
        """Return formatted invoice number"""
        return self.invoice_number if self.invoice_number else f"INV-{self.id:04d}"
    
    def to_dict(self) -> dict:
        """Convert invoice to dictionary for database storage"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'client_id': self.client_id,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'items': json.dumps([item.to_dict() for item in self.items]),
            'subtotal': self.subtotal,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'total': self.total,
            'notes': self.notes,
            'payment_terms': self.payment_terms,
            'currency': self.currency,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'company_name': self.company_name,
            'company_address': self.company_address,
            'company_phone': self.company_phone,
            'company_email': self.company_email,
            'company_website': self.company_website
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Invoice':
        """Create invoice from dictionary"""
        # Handle datetime fields
        datetime_fields = ['invoice_date', 'due_date', 'created_date', 'updated_date']
        for field_name in datetime_fields:
            if data.get(field_name):
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        # Handle items JSON
        items_data = data.pop('items', '[]')
        if isinstance(items_data, str):
            items_list = json.loads(items_data)
        else:
            items_list = items_data
        
        invoice = cls(**data)
        invoice.items = [InvoiceItem.from_dict(item) for item in items_list]
        
        return invoice

@dataclass
class AppSettings:
    """Application settings model"""
    id: Optional[int] = None
    company_name: str = ""
    company_address: str = ""
    company_phone: str = ""
    company_email: str = ""
    company_website: str = ""
    default_currency: str = "USD"
    default_tax_rate: float = 0.0
    default_payment_terms: str = "Net 30"
    invoice_number_format: str = "INV-{:04d}"
    next_invoice_number: int = 1
    auto_backup: bool = True
    backup_frequency: int = 7
    last_backup: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'company_address': self.company_address,
            'company_phone': self.company_phone,
            'company_email': self.company_email,
            'company_website': self.company_website,
            'default_currency': self.default_currency,
            'default_tax_rate': self.default_tax_rate,
            'default_payment_terms': self.default_payment_terms,
            'invoice_number_format': self.invoice_number_format,
            'next_invoice_number': self.next_invoice_number,
            'auto_backup': self.auto_backup,
            'backup_frequency': self.backup_frequency,
            'last_backup': self.last_backup.isoformat() if self.last_backup else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppSettings':
        """Create settings from dictionary"""
        if data.get('last_backup'):
            data['last_backup'] = datetime.fromisoformat(data['last_backup'])
        return cls(**data)
    
    def get_next_invoice_number(self) -> str:
        """Generate next invoice number and increment counter"""
        number = self.invoice_number_format.format(self.next_invoice_number)
        self.next_invoice_number += 1
        return number