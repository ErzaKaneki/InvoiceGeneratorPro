# File: config.py
# Location: InvoiceGeneratorPro/config.py

import os

# Application Information
APP_NAME = "Invoice Generator Pro"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Your Business Name"

# Database Configuration
DATABASE_NAME = "invoices.db"
DATABASE_PATH = os.path.join(os.path.expanduser("~"), "Documents", "InvoiceGeneratorPro", DATABASE_NAME)

# Ensure database directory exists
DATABASE_DIR = os.path.dirname(DATABASE_PATH)
os.makedirs(DATABASE_DIR, exist_ok=True)

# File Paths
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
DEFAULT_LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "InvoiceGeneratorPro", "Exports")

# Ensure export directory exists
os.makedirs(EXPORT_DIR, exist_ok=True)

# GUI Configuration
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600

# Colors (Professional Blue Theme)
PRIMARY_COLOR = "#2E86AB"
SECONDARY_COLOR = "#A23B72"
ACCENT_COLOR = "#F18F01"
BACKGROUND_COLOR = "#F8F9FA"
TEXT_COLOR = "#2C3E50"
SUCCESS_COLOR = "#27AE60"
WARNING_COLOR = "#F39C12"
ERROR_COLOR = "#E74C3C"

# Font Configuration
DEFAULT_FONT = ("Arial", 10)
HEADER_FONT = ("Arial", 12, "bold")
TITLE_FONT = ("Arial", 14, "bold")
BUTTON_FONT = ("Arial", 9)

# Tax Configuration (Default US rates - user can modify)
DEFAULT_TAX_RATES = {
    "None": 0.0,
    "Sales Tax (7%)": 0.07,
    "Sales Tax (8.5%)": 0.085,
    "Sales Tax (10%)": 0.10,
    "VAT (20%)": 0.20,
    "Custom": 0.0
}

# Invoice Configuration
INVOICE_NUMBER_PREFIX = "INV"
INVOICE_STATUSES = ["Draft", "Sent", "Paid", "Overdue", "Cancelled"]
PAYMENT_TERMS = ["Net 15", "Net 30", "Net 45", "Due on Receipt", "Custom"]

# PDF Configuration
PDF_MARGIN = 72  # 1 inch in points
PDF_FONT_SIZE = 10
PDF_HEADER_FONT_SIZE = 16
PDF_TITLE_FONT_SIZE = 24

# Validation Rules
MAX_CLIENT_NAME_LENGTH = 100
MAX_INVOICE_ITEMS = 50
MAX_DESCRIPTION_LENGTH = 500
MIN_AMOUNT = 0.01
MAX_AMOUNT = 999999.99

# Date Formats
DATE_FORMAT = "%Y-%m-%d"
DISPLAY_DATE_FORMAT = "%B %d, %Y"
FILE_DATE_FORMAT = "%Y%m%d"

# Currency Configuration
DEFAULT_CURRENCY = "USD"
CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "CAD": "C$",
    "AUD": "A$"
}

# Application Settings (Can be modified by user)
USER_SETTINGS = {
    "company_name": "",
    "company_address": "",
    "company_phone": "",
    "company_email": "",
    "company_website": "",
    "default_currency": DEFAULT_CURRENCY,
    "default_tax_rate": 0.0,
    "default_payment_terms": "Net 30",
    "invoice_number_format": f"{INVOICE_NUMBER_PREFIX}-{{:04d}}",
    "auto_backup": True,
    "backup_frequency": 7  # days
}

# Error Messages
ERROR_MESSAGES = {
    "database_error": "Database connection error. Please restart the application.",
    "invalid_email": "Please enter a valid email address.",
    "invalid_amount": "Please enter a valid amount (0.01 - 999,999.99).",
    "required_field": "This field is required.",
    "duplicate_client": "A client with this name already exists.",
    "invoice_not_found": "Invoice not found.",
    "export_error": "Error exporting file. Please check permissions.",
    "pdf_generation_error": "Error generating PDF. Please try again."
}

# Success Messages
SUCCESS_MESSAGES = {
    "client_saved": "Client information saved successfully.",
    "invoice_created": "Invoice created successfully.",
    "invoice_updated": "Invoice updated successfully.",
    "invoice_deleted": "Invoice deleted successfully.",
    "pdf_exported": "PDF exported successfully.",
    "settings_saved": "Settings saved successfully."
}