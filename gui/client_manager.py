# File: client_manager.py
# Location: InvoiceGeneratorPro/gui/client_manager.py

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import re
from datetime import datetime

from database.db_manager import DatabaseManager
from database.models import Client
from utils.validators import (
    is_valid_email, is_valid_phone, format_phone_number, clean_input
)
from config import (
    DEFAULT_FONT, HEADER_FONT, BUTTON_FONT, PRIMARY_COLOR,
    SUCCESS_COLOR, ERROR_COLOR, MAX_CLIENT_NAME_LENGTH
)

class ClientFormWindow:
    """Window for creating and editing clients"""
    
    def __init__(self, parent, db_manager: DatabaseManager, client_id: Optional[int] = None):
        self.parent = parent
        self.db_manager = db_manager
        self.client_id = client_id
        self.client: Optional[Client] = None
        self.created_client_name = None  # For returning to invoice form
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Client Form")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center window
        self._center_window()
        
        # Create widgets
        self._create_widgets()
        
        # Load existing client if editing
        if self.client_id:
            self._load_client()
        else:
            self._setup_new_client()
    
    def _center_window(self):
        """Center window on parent"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (300)
        y = (self.window.winfo_screenheight() // 2) - (250)
        self.window.geometry(f"600x500+{x}+{y}")
    
    def _create_widgets(self):
        """Create and layout all widgets"""
        # Main container
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_text = "Edit Client" if self.client_id else "Add New Client"
        ttk.Label(main_frame, text=title_text, font=HEADER_FONT, 
                 foreground=PRIMARY_COLOR).pack(pady=(0, 20))
        
        # Create form sections
        self._create_basic_info_section(main_frame)
        self._create_contact_info_section(main_frame)
        self._create_address_section(main_frame)
        self._create_additional_info_section(main_frame)
        self._create_buttons_section(main_frame)
        
        # Configure tab order
        self._configure_tab_order()
    
    def _create_basic_info_section(self, parent):
        """Create basic information section"""
        basic_frame = ttk.LabelFrame(parent, text="Basic Information", padding=10)
        basic_frame.pack(fill='x', pady=(0, 10))
        
        # Client name (required)
        ttk.Label(basic_frame, text="Client Name: *").grid(row=0, column=0, sticky='w', pady=(0, 5))
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(basic_frame, textvariable=self.name_var, width=40, font=DEFAULT_FONT)
        self.name_entry.grid(row=0, column=1, sticky='ew', pady=(0, 5), padx=(10, 0))
        
        # Name validation feedback
        self.name_validation_var = tk.StringVar()
        self.name_validation_label = ttk.Label(basic_frame, textvariable=self.name_validation_var, 
                                              foreground=ERROR_COLOR, font=('Arial', 8))
        self.name_validation_label.grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # Bind validation
        self.name_var.trace('w', self._validate_name)
        
        # Configure grid
        basic_frame.grid_columnconfigure(1, weight=1)
    
    def _create_contact_info_section(self, parent):
        """Create contact information section"""
        contact_frame = ttk.LabelFrame(parent, text="Contact Information", padding=10)
        contact_frame.pack(fill='x', pady=(0, 10))
        
        # Email
        ttk.Label(contact_frame, text="Email:").grid(row=0, column=0, sticky='w', pady=(0, 5))
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(contact_frame, textvariable=self.email_var, width=40, font=DEFAULT_FONT)
        self.email_entry.grid(row=0, column=1, sticky='ew', pady=(0, 5), padx=(10, 0))
        
        # Email validation feedback
        self.email_validation_var = tk.StringVar()
        self.email_validation_label = ttk.Label(contact_frame, textvariable=self.email_validation_var, 
                                               foreground=ERROR_COLOR, font=('Arial', 8))
        self.email_validation_label.grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # Phone
        ttk.Label(contact_frame, text="Phone:").grid(row=2, column=0, sticky='w', pady=(5, 5))
        self.phone_var = tk.StringVar()
        self.phone_entry = ttk.Entry(contact_frame, textvariable=self.phone_var, width=40, font=DEFAULT_FONT)
        self.phone_entry.grid(row=2, column=1, sticky='ew', pady=(5, 5), padx=(10, 0))
        
        # Phone validation feedback
        self.phone_validation_var = tk.StringVar()
        self.phone_validation_label = ttk.Label(contact_frame, textvariable=self.phone_validation_var, 
                                               foreground=ERROR_COLOR, font=('Arial', 8))
        self.phone_validation_label.grid(row=3, column=1, sticky='w', padx=(10, 0))
        
        # Website
        ttk.Label(contact_frame, text="Website:").grid(row=4, column=0, sticky='w', pady=(5, 0))
        self.website_var = tk.StringVar()
        self.website_entry = ttk.Entry(contact_frame, textvariable=self.website_var, width=40, font=DEFAULT_FONT)
        self.website_entry.grid(row=4, column=1, sticky='ew', pady=(5, 0), padx=(10, 0))
        
        # Bind validation
        self.email_var.trace('w', self._validate_email)
        self.phone_var.trace('w', self._validate_phone)
        
        # Configure grid
        contact_frame.grid_columnconfigure(1, weight=1)
    
    def _create_address_section(self, parent):
        """Create address section"""
        address_frame = ttk.LabelFrame(parent, text="Address", padding=10)
        address_frame.pack(fill='x', pady=(0, 10))
        
        # Street address
        ttk.Label(address_frame, text="Street Address:").grid(row=0, column=0, sticky='nw', pady=(0, 5))
        self.address_var = tk.StringVar()
        self.address_text = tk.Text(address_frame, height=3, width=40, font=DEFAULT_FONT)
        self.address_text.grid(row=0, column=1, sticky='ew', pady=(0, 5), padx=(10, 0))
        
        # City, State, ZIP row
        location_frame = ttk.Frame(address_frame)
        location_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(5, 0))
        
        # City
        ttk.Label(location_frame, text="City:").grid(row=0, column=0, sticky='w')
        self.city_var = tk.StringVar()
        city_entry = ttk.Entry(location_frame, textvariable=self.city_var, width=20, font=DEFAULT_FONT)
        city_entry.grid(row=0, column=1, sticky='ew', padx=(5, 10))
        
        # State
        ttk.Label(location_frame, text="State:").grid(row=0, column=2, sticky='w')
        self.state_var = tk.StringVar()
        state_entry = ttk.Entry(location_frame, textvariable=self.state_var, width=15, font=DEFAULT_FONT)
        state_entry.grid(row=0, column=3, sticky='ew', padx=(5, 10))
        
        # ZIP Code
        ttk.Label(location_frame, text="ZIP:").grid(row=0, column=4, sticky='w')
        self.zip_var = tk.StringVar()
        zip_entry = ttk.Entry(location_frame, textvariable=self.zip_var, width=12, font=DEFAULT_FONT)
        zip_entry.grid(row=0, column=5, sticky='ew', padx=(5, 0))
        
        # Country
        ttk.Label(address_frame, text="Country:").grid(row=2, column=0, sticky='w', pady=(10, 0))
        self.country_var = tk.StringVar(value="United States")
        country_combo = ttk.Combobox(address_frame, textvariable=self.country_var, width=25,
                                    values=["United States", "Canada", "United Kingdom", "Australia", "Other"])
        country_combo.grid(row=2, column=1, sticky='w', pady=(10, 0), padx=(10, 0))
        
        # Configure grid weights
        address_frame.grid_columnconfigure(1, weight=1)
        location_frame.grid_columnconfigure(1, weight=1)
        location_frame.grid_columnconfigure(3, weight=1)
        location_frame.grid_columnconfigure(5, weight=1)
    
    def _create_additional_info_section(self, parent):
        """Create additional information section"""
        additional_frame = ttk.LabelFrame(parent, text="Additional Information", padding=10)
        additional_frame.pack(fill='x', pady=(0, 10))
        
        # Notes
        ttk.Label(additional_frame, text="Notes:").grid(row=0, column=0, sticky='nw', pady=(0, 5))
        self.notes_text = tk.Text(additional_frame, height=4, width=40, font=DEFAULT_FONT)
        self.notes_text.grid(row=0, column=1, sticky='ew', pady=(0, 5), padx=(10, 0))
        
        # Client statistics (if editing existing client)
        if self.client_id:
            self.stats_frame = ttk.Frame(additional_frame)
            self.stats_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10, 0))
            
            # Stats will be loaded when client data is loaded
            self.stats_vars = {
                'total_invoices': tk.StringVar(value="0"),
                'total_revenue': tk.StringVar(value="$0.00"),
                'last_invoice': tk.StringVar(value="Never")
            }
        
        # Configure grid
        additional_frame.grid_columnconfigure(1, weight=1)
    
    def _create_buttons_section(self, parent):
        """Create action buttons section"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill='x', pady=(20, 0))
        
        # Left side - additional actions (if editing)
        left_buttons = ttk.Frame(buttons_frame)
        left_buttons.pack(side='left')
        
        if self.client_id:
            ttk.Button(left_buttons, text="View Invoices", 
                      command=self._view_client_invoices).pack(side='left', padx=(0, 5))
            ttk.Button(left_buttons, text="Create Invoice", style='Success.TButton',
                      command=self._create_invoice_for_client).pack(side='left', padx=(0, 5))
        
        # Right side - save/cancel
        right_buttons = ttk.Frame(buttons_frame)
        right_buttons.pack(side='right')
        
        ttk.Button(right_buttons, text="Save", style='Primary.TButton',
                  command=self._save_client).pack(side='left', padx=(0, 5))
        ttk.Button(right_buttons, text="Cancel", 
                  command=self.window.destroy).pack(side='left')
    
    def _configure_tab_order(self):
        """Configure tab order for form navigation"""
        widgets = [
            self.name_entry, self.email_entry, self.phone_entry, self.website_entry,
            self.address_text, self.city_var, self.state_var, self.zip_var,
            self.notes_text
        ]
        
        for i, widget in enumerate(widgets):
            if hasattr(widget, 'tk'):  # Skip StringVar objects
                continue
            if i < len(widgets) - 1 and hasattr(widgets[i + 1], 'focus'):
                widget.bind('<Tab>', lambda e, next_widget=widgets[i + 1]: next_widget.focus())
    
    # Data loading methods
    def _load_client(self):
        """Load existing client data"""
        try:
            if self.client_id is None:
                return
            self.client = self.db_manager.get_client(self.client_id)
            if not self.client:
                messagebox.showerror("Error", "Client not found.")
                self.window.destroy()
                return
            
            # Load basic info
            self.name_var.set(self.client.name)
            
            # Load contact info
            self.email_var.set(self.client.email or "")
            self.phone_var.set(self.client.phone or "")
            
            # Load address
            self.address_text.delete('1.0', 'end')
            self.address_text.insert('1.0', self.client.address or "")
            self.city_var.set(self.client.city or "")
            self.state_var.set(self.client.state or "")
            self.zip_var.set(self.client.zip_code or "")
            self.country_var.set(self.client.country or "United States")
            
            # Load notes
            self.notes_text.delete('1.0', 'end')
            self.notes_text.insert('1.0', self.client.notes or "")
            
            # Load client statistics
            self._load_client_stats()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading client: {str(e)}")
    
    def _setup_new_client(self):
        """Setup form for new client"""
        # Set focus on name field
        self.name_entry.focus()
    
    def _load_client_stats(self):
        """Load and display client statistics"""
        if not self.client_id:
            return
        
        try:
            # Get client invoices
            invoices = self.db_manager.get_invoices_by_client(self.client_id)
            
            # Calculate stats
            total_invoices = len(invoices)
            total_revenue = sum(inv.total for inv in invoices if inv.status == "Paid")
            last_invoice_date = "Never"
            
            if invoices:
                last_invoice = max(invoices, key=lambda x: x.created_date or datetime.min)
                if last_invoice.created_date:
                    last_invoice_date = last_invoice.created_date.strftime('%m/%d/%Y')
            
            # Update stats display
            self.stats_vars['total_invoices'].set(str(total_invoices))
            self.stats_vars['total_revenue'].set(f"${total_revenue:.2f}")
            self.stats_vars['last_invoice'].set(last_invoice_date)
            
            # Create stats display if not exists
            if hasattr(self, 'stats_frame'):
                # Clear existing stats
                for widget in self.stats_frame.winfo_children():
                    widget.destroy()
                
                # Display stats
                ttk.Label(self.stats_frame, text="Client Statistics:", font=HEADER_FONT).grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 5))
                
                ttk.Label(self.stats_frame, text="Total Invoices:").grid(row=1, column=0, sticky='w', padx=(0, 5))
                ttk.Label(self.stats_frame, textvariable=self.stats_vars['total_invoices'], font=HEADER_FONT).grid(row=1, column=1, sticky='w', padx=(0, 15))
                
                ttk.Label(self.stats_frame, text="Total Revenue:").grid(row=1, column=2, sticky='w', padx=(0, 5))
                ttk.Label(self.stats_frame, textvariable=self.stats_vars['total_revenue'], font=HEADER_FONT, foreground=SUCCESS_COLOR).grid(row=1, column=3, sticky='w')
                
                ttk.Label(self.stats_frame, text="Last Invoice:").grid(row=2, column=0, sticky='w', padx=(0, 5))
                ttk.Label(self.stats_frame, textvariable=self.stats_vars['last_invoice'], font=DEFAULT_FONT).grid(row=2, column=1, sticky='w')
            
        except Exception as e:
            print(f"Error loading client stats: {str(e)}")
    
    # Validation methods
    def _validate_name(self, *args):
        """Validate client name as user types"""
        name = self.name_var.get()
        
        if not name:
            self.name_validation_var.set("Name is required")
            return False
        
        if len(name) > MAX_CLIENT_NAME_LENGTH:
            self.name_validation_var.set(f"Name too long (max {MAX_CLIENT_NAME_LENGTH} characters)")
            return False
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9\s\.,\-&\'\"]+$', name):
            self.name_validation_var.set("Name contains invalid characters")
            return False
        
        # Check for duplicate name (only when editing or name is complete)
        if len(name) > 2:  # Only check when user has typed enough
            existing_client = self.db_manager.get_client_by_name(name)
            if existing_client and (not self.client_id or existing_client.id != self.client_id):
                self.name_validation_var.set("A client with this name already exists")
                return False
        
        self.name_validation_var.set("")  # Clear validation message
        return True
    
    def _validate_email(self, *args):
        """Validate email as user types"""
        email = self.email_var.get()
        
        if not email:
            self.email_validation_var.set("")  # Email is optional
            return True
        
        if is_valid_email(email):
            self.email_validation_var.set("")
            return True
        else:
            self.email_validation_var.set("Invalid email format")
            return False
    
    def _validate_phone(self, *args):
        """Validate and format phone as user types"""
        phone = self.phone_var.get()
        
        if not phone:
            self.phone_validation_var.set("")  # Phone is optional
            return True
        
        if is_valid_phone(phone):
            self.phone_validation_var.set("")
            # Auto-format phone number
            formatted = format_phone_number(phone)
            if formatted != phone:
                # Update without triggering validation again
                self.phone_var.trace_vdelete('w', self.phone_var.trace_vinfo()[0][1])
                self.phone_var.set(formatted)
                self.phone_var.trace('w', self._validate_phone)
            return True
        else:
            self.phone_validation_var.set("Invalid phone format")
            return False
    
    def _validate_form(self):
        """Validate entire form before saving"""
        errors = []
        
        # Validate required fields
        if not self.name_var.get().strip():
            errors.append("Client name is required")
        
        # Validate name length and format
        name = self.name_var.get().strip()
        if len(name) > MAX_CLIENT_NAME_LENGTH:
            errors.append(f"Client name cannot exceed {MAX_CLIENT_NAME_LENGTH} characters")
        
        # Check for duplicate name
        if name:
            existing_client = self.db_manager.get_client_by_name(name)
            if existing_client and (not self.client_id or existing_client.id != self.client_id):
                errors.append("A client with this name already exists")
        
        # Validate email if provided
        email = self.email_var.get().strip()
        if email and not is_valid_email(email):
            errors.append("Invalid email address")
        
        # Validate phone if provided
        phone = self.phone_var.get().strip()
        if phone and not is_valid_phone(phone):
            errors.append("Invalid phone number")
        
        # Show errors if any
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return False
        
        return True
    
    # Action methods
    def _save_client(self):
        """Save the client"""
        try:
            # Validate form
            if not self._validate_form():
                return
            
            # Create or update client
            if self.client_id and self.client:
                client = self.client
            else:
                client = Client()
            
            # Set client data
            client.name = clean_input(self.name_var.get())
            client.email = clean_input(self.email_var.get()) or ""
            client.phone = clean_input(self.phone_var.get()) or ""
            client.address = self.address_text.get('1.0', 'end-1c').strip() or ""
            client.city = clean_input(self.city_var.get()) or ""
            client.state = clean_input(self.state_var.get()) or ""
            client.zip_code = clean_input(self.zip_var.get()) or ""
            client.country = clean_input(self.country_var.get()) or ""
            client.notes = self.notes_text.get('1.0', 'end-1c').strip() or ""
            
            # Save client
            saved_client = self.db_manager.save_client(client)
            self.client = saved_client
            self.client_id = saved_client.id
            
            # Store name for invoice form reference
            self.created_client_name = saved_client.name
            
            messagebox.showinfo("Success", "Client saved successfully!")
            
            # Update window title and reload stats if editing
            if self.client_id:
                self.window.title("Edit Client")
                self._load_client_stats()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error saving client: {str(e)}")
    
    def _view_client_invoices(self):
        """View invoices for this client"""
        if not self.client_id:
            return
        
        # This would open the main window's invoices tab filtered by client
        # For now, just show a message
        messagebox.showinfo("View Invoices", "This feature will open the invoices tab filtered by this client.")
    
    def _create_invoice_for_client(self):
        """Create new invoice for this client"""
        if not self.client_id:
            return
        
        try:
            from gui.invoice_form import InvoiceFormWindow
            form = InvoiceFormWindow(self.window, self.db_manager, client_id=self.client_id)
            self.window.wait_window(form.window)
            
            # Reload stats after potential invoice creation
            self._load_client_stats()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error creating invoice: {str(e)}")

# Configure ttk styles for this module
def configure_styles():
    """Configure custom styles for client form"""
    style = ttk.Style()
    
    # Primary button style
    style.configure('Primary.TButton',
                   font=BUTTON_FONT,
                   foreground='white',
                   background=PRIMARY_COLOR)
    
    # Success button style  
    style.configure('Success.TButton',
                   font=BUTTON_FONT,
                   foreground='white',
                   background=SUCCESS_COLOR)

# Call style configuration when module is imported
configure_styles()