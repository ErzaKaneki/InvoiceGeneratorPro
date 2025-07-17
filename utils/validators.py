# File: validators.py
# Location: InvoiceGeneratorPro/utils/validators.py

import re
from email_validator import validate_email, EmailNotValidError

from config import (
    MAX_CLIENT_NAME_LENGTH, 
    MAX_DESCRIPTION_LENGTH, 
    ERROR_MESSAGES,
    INVOICE_STATUSES,
    PAYMENT_TERMS
)

class InputValidator:
    """Validates user inputs for forms and data entry"""
    
    @staticmethod
    def validate_required_field(value: str, field_name: str = "Field") -> tuple[bool, str]:
        """Validate that a required field is not empty"""
        if not value or not value.strip():
            return False, f"{field_name} is required"
        return True, ""
    
    @staticmethod
    def validate_client_name(name: str) -> tuple[bool, str]:
        """Validate client name"""
        # Check if required
        is_valid, error = InputValidator.validate_required_field(name, "Client name")
        if not is_valid:
            return False, error
        
        # Check length
        if len(name.strip()) > MAX_CLIENT_NAME_LENGTH:
            return False, f"Client name cannot exceed {MAX_CLIENT_NAME_LENGTH} characters"
        
        # Check for valid characters (letters, numbers, spaces, basic punctuation)
        if not re.match(r'^[a-zA-Z0-9\s\.,\-&\'\"]+$', name.strip()):
            return False, "Client name contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str, required: bool = False) -> tuple[bool, str]:
        """Validate email address"""
        if not email or not email.strip():
            if required:
                return False, "Email address is required"
            return True, ""  # Optional field, empty is OK
        
        try:
            # Use email-validator library for robust validation
            validate_email(email.strip())
            return True, ""
        except EmailNotValidError:
            return False, ERROR_MESSAGES["invalid_email"]
    
    @staticmethod
    def validate_phone(phone: str, required: bool = False) -> tuple[bool, str]:
        """Validate phone number"""
        if not phone or not phone.strip():
            if required:
                return False, "Phone number is required"
            return True, ""
        
        # Remove all non-digit characters for validation
        digits_only = re.sub(r'\D', '', phone)
        
        # Check length (7-15 digits is reasonable for most phone formats)
        if len(digits_only) < 7:
            return False, "Phone number too short"
        if len(digits_only) > 15:
            return False, "Phone number too long"
        
        return True, ""
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """Format phone number for display"""
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Format based on length
        if len(digits_only) == 10:
            # US format: (555) 123-4567
            return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            # US format with country code: +1 (555) 123-4567
            return f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
        else:
            # International or other format: just add spaces every 3-4 digits
            if len(digits_only) <= 7:
                return digits_only
            elif len(digits_only) <= 10:
                return f"{digits_only[:-7]} {digits_only[-7:-4]} {digits_only[-4:]}"
            else:
                return f"+{digits_only[:-10]} {digits_only[-10:-7]} {digits_only[-7:-4]} {digits_only[-4:]}"
    
    @staticmethod
    def validate_website(website: str, required: bool = False) -> tuple[bool, str]:
        """Validate website URL"""
        if not website or not website.strip():
            if required:
                return False, "Website is required"
            return True, ""
        
        url = website.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic URL pattern validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            return False, "Invalid website URL format"
        
        return True, url  # Return formatted URL
    
    @staticmethod
    def validate_postal_code(postal_code: str, country: str = "US", required: bool = False) -> tuple[bool, str]:
        """Validate postal/zip code"""
        if not postal_code or not postal_code.strip():
            if required:
                return False, "Postal code is required"
            return True, ""
        
        code = postal_code.strip().upper()
        
        # US ZIP code validation
        if country.upper() in ["US", "USA", "UNITED STATES"]:
            if not re.match(r'^\d{5}(-\d{4})?$', code):
                return False, "Invalid US ZIP code format (12345 or 12345-6789)"
        
        # Canadian postal code validation
        elif country.upper() in ["CA", "CAN", "CANADA"]:
            if not re.match(r'^[A-Z]\d[A-Z] \d[A-Z]\d$', code):
                return False, "Invalid Canadian postal code format (A1A 1A1)"
        
        # UK postal code validation (basic)
        elif country.upper() in ["GB", "UK", "UNITED KINGDOM"]:
            if not re.match(r'^[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}$', code):
                return False, "Invalid UK postal code format"
        
        # For other countries, just check it's not empty and reasonable length
        else:
            if len(code) > 20:
                return False, "Postal code too long"
        
        return True, ""
    
    @staticmethod
    def validate_invoice_description(description: str) -> tuple[bool, str]:
        """Validate invoice item description"""
        is_valid, error = InputValidator.validate_required_field(description, "Description")
        if not is_valid:
            return False, error
        
        if len(description.strip()) > MAX_DESCRIPTION_LENGTH:
            return False, f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters"
        
        return True, ""
    
    @staticmethod
    def validate_invoice_number(invoice_number: str) -> tuple[bool, str]:
        """Validate invoice number format"""
        is_valid, error = InputValidator.validate_required_field(invoice_number, "Invoice number")
        if not is_valid:
            return False, error
        
        # Check format (letters, numbers, hyphens only)
        if not re.match(r'^[A-Z0-9\-]+$', invoice_number.strip().upper()):
            return False, "Invoice number can only contain letters, numbers, and hyphens"
        
        if len(invoice_number.strip()) > 50:
            return False, "Invoice number too long"
        
        return True, ""
    
    @staticmethod
    def validate_invoice_status(status: str) -> tuple[bool, str]:
        """Validate invoice status"""
        if status not in INVOICE_STATUSES:
            return False, f"Invalid status. Must be one of: {', '.join(INVOICE_STATUSES)}"
        
        return True, ""
    
    @staticmethod
    def validate_payment_terms(terms: str) -> tuple[bool, str]:
        """Validate payment terms"""
        if terms not in PAYMENT_TERMS and not terms.startswith("Net "):
            return False, f"Invalid payment terms. Must be one of: {', '.join(PAYMENT_TERMS)}"
        
        # If it's a custom Net terms, validate the number
        if terms.startswith("Net "):
            try:
                days = int(terms.split()[1])
                if days < 0 or days > 365:
                    return False, "Net payment terms must be between 0 and 365 days"
            except (ValueError, IndexError):
                return False, "Invalid Net payment terms format (use 'Net 30')"
        
        return True, ""

class BusinessValidator:
    """Validates business-specific data"""
    
    @staticmethod
    def validate_company_name(name: str) -> tuple[bool, str]:
        """Validate company name"""
        return InputValidator.validate_client_name(name)  # Same rules as client name
    
    @staticmethod
    def validate_tax_id(tax_id: str, required: bool = False) -> tuple[bool, str]:
        """Validate tax ID/EIN"""
        if not tax_id or not tax_id.strip():
            if required:
                return False, "Tax ID is required"
            return True, ""
        
        # Remove hyphens and spaces
        clean_id = re.sub(r'[\s\-]', '', tax_id)
        
        # US EIN format: 12-3456789 (9 digits)
        if re.match(r'^\d{9}$', clean_id):
            return True, f"{clean_id[:2]}-{clean_id[2:]}"  # Return formatted
        
        # Generic validation for other countries
        if len(clean_id) < 5 or len(clean_id) > 20:
            return False, "Tax ID should be between 5 and 20 characters"
        
        return True, ""

class FormValidator:
    """Validates complete forms"""
    
    @staticmethod
    def validate_client_form(form_data: dict) -> tuple[bool, list]:
        """Validate complete client form"""
        errors = []
        
        # Required fields
        is_valid, error = InputValidator.validate_client_name(form_data.get('name', ''))
        if not is_valid:
            errors.append(error)
        
        # Optional email
        is_valid, error = InputValidator.validate_email(form_data.get('email', ''), required=False)
        if not is_valid:
            errors.append(error)
        
        # Optional phone
        is_valid, error = InputValidator.validate_phone(form_data.get('phone', ''), required=False)
        if not is_valid:
            errors.append(error)
        
        # Optional website
        is_valid, error = InputValidator.validate_website(form_data.get('website', ''), required=False)
        if not is_valid:
            errors.append(error)
        
        # Optional postal code
        is_valid, error = InputValidator.validate_postal_code(
            form_data.get('zip_code', ''), 
            form_data.get('country', 'US'), 
            required=False
        )
        if not is_valid:
            errors.append(error)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_invoice_form(form_data: dict) -> tuple[bool, list]:
        """Validate complete invoice form"""
        errors = []
        
        # Validate invoice number
        is_valid, error = InputValidator.validate_invoice_number(form_data.get('invoice_number', ''))
        if not is_valid:
            errors.append(error)
        
        # Validate client selection
        if not form_data.get('client_id'):
            errors.append("Client selection is required")
        
        # Validate payment terms
        is_valid, error = InputValidator.validate_payment_terms(form_data.get('payment_terms', ''))
        if not is_valid:
            errors.append(error)
        
        # Validate status
        is_valid, error = InputValidator.validate_invoice_status(form_data.get('status', ''))
        if not is_valid:
            errors.append(error)
        
        # Validate items
        items = form_data.get('items', [])
        if not items:
            errors.append("Invoice must contain at least one item")
        else:
            for i, item in enumerate(items, 1):
                is_valid, error = InputValidator.validate_invoice_description(item.get('description', ''))
                if not is_valid:
                    errors.append(f"Item {i}: {error}")
        
        return len(errors) == 0, errors

# Quick validation functions for common use
def is_valid_email(email: str) -> bool:
    """Quick email validation"""
    is_valid, _ = InputValidator.validate_email(email)
    return is_valid

def is_valid_phone(phone: str) -> bool:
    """Quick phone validation"""
    is_valid, _ = InputValidator.validate_phone(phone)
    return is_valid

def format_phone_number(phone: str) -> str:
    """Quick phone formatting"""
    return InputValidator.format_phone(phone)

def clean_input(text: str) -> str:
    """Clean and sanitize text input"""
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    cleaned = text.strip()
    
    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove potentially harmful characters
    cleaned = re.sub(r'[<>\"\'%;()&+]', '', cleaned)
    
    return cleaned