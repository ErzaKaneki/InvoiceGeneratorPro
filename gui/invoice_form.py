# File: invoice_form.py
# Location: InvoiceGeneratorPro/gui/invoice_form.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, List
from pdf_generator.invoice_pdf import InvoicePDFGenerator
from tkinter import filedialog


from database.db_manager import DatabaseManager
from database.models import Invoice, Client, InvoiceItem
from utils.calculations import (
    CurrencyFormatter, DateCalculator, 
    calculate_invoice_total
)
from config import (
    DEFAULT_FONT, HEADER_FONT, BUTTON_FONT, PRIMARY_COLOR,
    SUCCESS_COLOR, BACKGROUND_COLOR,
    INVOICE_STATUSES, PAYMENT_TERMS, DEFAULT_TAX_RATES, CURRENCY_SYMBOLS
)

class InvoiceFormWindow:
    """Window for creating and editing invoices"""
    
    def __init__(self, parent, db_manager: DatabaseManager, invoice_id: Optional[int] = None, client_id: Optional[int] = None):
        self.parent = parent
        self.db_manager = db_manager
        self.invoice_id = invoice_id
        self.client_id = client_id
        self.invoice: Optional[Invoice] = None
        self.items: List[InvoiceItem] = []
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Invoice Form")
        self.window.geometry("900x700")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center window
        self._center_window()
        
        # Load app settings for defaults
        self.app_settings = self.db_manager.get_app_settings()
        
        # Create widgets
        self._create_widgets()
        
        # Load existing invoice if editing
        if self.invoice_id:
            self._load_invoice()
        else:
            self._setup_new_invoice()
    
    def _center_window(self):
        """Center window on parent"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (450)
        y = (self.window.winfo_screenheight() // 2) - (350)
        self.window.geometry(f"900x700+{x}+{y}")
    
    def _create_widgets(self):
        """Create and layout all widgets"""
        # Main container with scrollable frame
        main_canvas = tk.Canvas(self.window, bg=BACKGROUND_COLOR)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=main_canvas.yview)
        self.scrollable_frame = ttk.Frame(main_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_text = "Edit Invoice" if self.invoice_id else "Create New Invoice"
        ttk.Label(self.scrollable_frame, text=title_text, font=HEADER_FONT, 
                 foreground=PRIMARY_COLOR).pack(pady=(0, 20))
        
        # Invoice header section
        self._create_header_section()
        
        # Client selection section
        self._create_client_section()
        
        # Invoice details section
        self._create_details_section()
        
        # Items section
        self._create_items_section()
        
        # Totals section
        self._create_totals_section()
        
        # Notes section
        self._create_notes_section()
        
        # Buttons section
        self._create_buttons_section()
        
        # Bind mouse wheel to canvas
        self._bind_mousewheel(main_canvas)
    
    def _bind_mousewheel(self, canvas):
        """Bind mouse wheel to canvas scrolling"""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def _create_header_section(self):
        """Create invoice header section"""
        header_frame = ttk.LabelFrame(self.scrollable_frame, text="Invoice Information", padding=10)
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Invoice number and status
        row1_frame = ttk.Frame(header_frame)
        row1_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(row1_frame, text="Invoice Number:").pack(side='left')
        self.invoice_number_var = tk.StringVar()
        ttk.Entry(row1_frame, textvariable=self.invoice_number_var, width=20).pack(side='left', padx=(5, 20))
        
        ttk.Label(row1_frame, text="Status:").pack(side='left')
        self.status_var = tk.StringVar(value="Draft")
        status_combo = ttk.Combobox(row1_frame, textvariable=self.status_var, 
                                   values=INVOICE_STATUSES, state='readonly', width=15)
        status_combo.pack(side='left', padx=(5, 0))
        
        # Dates
        row2_frame = ttk.Frame(header_frame)
        row2_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(row2_frame, text="Invoice Date:").pack(side='left')
        self.invoice_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(row2_frame, textvariable=self.invoice_date_var, width=12).pack(side='left', padx=(5, 20))
        
        ttk.Label(row2_frame, text="Due Date:").pack(side='left')
        self.due_date_var = tk.StringVar()
        ttk.Entry(row2_frame, textvariable=self.due_date_var, width=12).pack(side='left', padx=(5, 20))
        
        ttk.Label(row2_frame, text="Payment Terms:").pack(side='left')
        self.payment_terms_var = tk.StringVar(value=self.app_settings.default_payment_terms)
        terms_combo = ttk.Combobox(row2_frame, textvariable=self.payment_terms_var, 
                                  values=PAYMENT_TERMS, width=15)
        terms_combo.pack(side='left', padx=(5, 0))
        terms_combo.bind('<<ComboboxSelected>>', self._on_payment_terms_changed)
        
        # Calculate initial due date
        self._calculate_due_date()
    
    def _create_client_section(self):
        """Create client selection section"""
        client_frame = ttk.LabelFrame(self.scrollable_frame, text="Client Information", padding=10)
        client_frame.pack(fill='x', pady=(0, 10))
        
        # Client selection
        selection_frame = ttk.Frame(client_frame)
        selection_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(selection_frame, text="Select Client:").pack(side='left')
        
        self.client_var = tk.StringVar()
        self.client_combo = ttk.Combobox(selection_frame, textvariable=self.client_var, 
                                        width=30, state='readonly')
        self.client_combo.pack(side='left', padx=(5, 10))
        self.client_combo.bind('<<ComboboxSelected>>', self._on_client_selected)
        
        ttk.Button(selection_frame, text="New Client", 
                  command=self._create_new_client).pack(side='left', padx=(5, 0))
        
        # Client details display
        self.client_details_frame = ttk.Frame(client_frame)
        self.client_details_frame.pack(fill='x')
        
        self.client_info_text = tk.Text(self.client_details_frame, height=4, width=60, 
                                       font=DEFAULT_FONT, state='disabled')
        self.client_info_text.pack(fill='x')
        
        # Load clients
        self._load_clients()
    
    def _create_details_section(self):
        """Create invoice details section"""
        details_frame = ttk.LabelFrame(self.scrollable_frame, text="Invoice Details", padding=10)
        details_frame.pack(fill='x', pady=(0, 10))
        
        # Currency and tax
        row1_frame = ttk.Frame(details_frame)
        row1_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(row1_frame, text="Currency:").pack(side='left')
        self.currency_var = tk.StringVar(value=self.app_settings.default_currency)
        currency_combo = ttk.Combobox(row1_frame, textvariable=self.currency_var, 
                                     values=list(CURRENCY_SYMBOLS.keys()), state='readonly', width=8)
        currency_combo.pack(side='left', padx=(5, 20))
        currency_combo.bind('<<ComboboxSelected>>', self._on_currency_changed)
        
        ttk.Label(row1_frame, text="Tax Rate:").pack(side='left')
        self.tax_rate_var = tk.StringVar()
        tax_combo = ttk.Combobox(row1_frame, textvariable=self.tax_rate_var, 
                                values=list(DEFAULT_TAX_RATES.keys()), width=15)
        tax_combo.pack(side='left', padx=(5, 0))
        tax_combo.bind('<<ComboboxSelected>>', self._on_tax_rate_changed)
        
        # Set default tax rate
        default_rate = self.app_settings.default_tax_rate
        for rate_name, rate_value in DEFAULT_TAX_RATES.items():
            if abs(rate_value - default_rate) < 0.001:
                self.tax_rate_var.set(rate_name)
                break
        else:
            self.tax_rate_var.set("None")
    
    def _create_items_section(self):
        """Create invoice items section"""
        items_frame = ttk.LabelFrame(self.scrollable_frame, text="Invoice Items", padding=10)
        items_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Items toolbar
        toolbar_frame = ttk.Frame(items_frame)
        toolbar_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(toolbar_frame, text="Add Item", style='Primary.TButton',
                  command=self._add_item).pack(side='left', padx=(0, 5))
        ttk.Button(toolbar_frame, text="Remove Selected", 
                  command=self._remove_selected_item).pack(side='left', padx=(0, 5))
        ttk.Button(toolbar_frame, text="Edit Selected", 
                  command=self._edit_selected_item).pack(side='left')
        
        # Items treeview
        columns = ('Description', 'Quantity', 'Rate', 'Amount')
        self.items_tree = ttk.Treeview(items_frame, columns=columns, show='headings', height=8)
        
        # Configure columns
        self.items_tree.heading('Description', text='Description')
        self.items_tree.heading('Quantity', text='Qty')
        self.items_tree.heading('Rate', text='Rate')
        self.items_tree.heading('Amount', text='Amount')
        
        self.items_tree.column('Description', width=300)
        self.items_tree.column('Quantity', width=80)
        self.items_tree.column('Rate', width=100)
        self.items_tree.column('Amount', width=100)
        
        # Scrollbar for items
        items_scrollbar = ttk.Scrollbar(items_frame, orient='vertical', command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)
        
        # Pack items widgets
        self.items_tree.pack(side='left', fill='both', expand=True)
        items_scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to edit
        self.items_tree.bind('<Double-1>', lambda e: self._edit_selected_item())
    
    def _create_totals_section(self):
        """Create totals display section"""
        totals_frame = ttk.LabelFrame(self.scrollable_frame, text="Invoice Totals", padding=10)
        totals_frame.pack(fill='x', pady=(0, 10))
        
        # Create totals display
        self.totals_vars = {
            'subtotal': tk.StringVar(value="$0.00"),
            'tax_amount': tk.StringVar(value="$0.00"),
            'total': tk.StringVar(value="$0.00")
        }
        
        # Align to right side
        totals_display_frame = ttk.Frame(totals_frame)
        totals_display_frame.pack(side='right')
        
        ttk.Label(totals_display_frame, text="Subtotal:").grid(row=0, column=0, sticky='e', padx=(0, 10))
        ttk.Label(totals_display_frame, textvariable=self.totals_vars['subtotal'], 
                 font=DEFAULT_FONT).grid(row=0, column=1, sticky='e')
        
        ttk.Label(totals_display_frame, text="Tax:").grid(row=1, column=0, sticky='e', padx=(0, 10))
        ttk.Label(totals_display_frame, textvariable=self.totals_vars['tax_amount'], 
                 font=DEFAULT_FONT).grid(row=1, column=1, sticky='e')
        
        ttk.Label(totals_display_frame, text="Total:").grid(row=2, column=0, sticky='e', padx=(0, 10))
        ttk.Label(totals_display_frame, textvariable=self.totals_vars['total'], 
                 font=HEADER_FONT, foreground=PRIMARY_COLOR).grid(row=2, column=1, sticky='e')
    
    def _create_notes_section(self):
        """Create notes section"""
        notes_frame = ttk.LabelFrame(self.scrollable_frame, text="Notes", padding=10)
        notes_frame.pack(fill='x', pady=(0, 10))
        
        self.notes_text = tk.Text(notes_frame, height=4, width=60, font=DEFAULT_FONT)
        self.notes_text.pack(fill='x')
    
    def _create_buttons_section(self):
        """Create action buttons section"""
        buttons_frame = ttk.Frame(self.scrollable_frame)
        buttons_frame.pack(fill='x', pady=20)
        
        # Left side buttons
        left_buttons = ttk.Frame(buttons_frame)
        left_buttons.pack(side='left')
        
        if self.invoice_id:
            ttk.Button(left_buttons, text="Generate PDF", style='Success.TButton',
                      command=self._generate_pdf).pack(side='left', padx=(0, 5))
        
        # Right side buttons
        right_buttons = ttk.Frame(buttons_frame)
        right_buttons.pack(side='right')
        
        ttk.Button(right_buttons, text="Save", style='Primary.TButton',
                  command=self._save_invoice).pack(side='left', padx=(0, 5))
        ttk.Button(right_buttons, text="Cancel", 
                  command=self.window.destroy).pack(side='left')
    
    # Data loading methods
    def _load_clients(self):
        """Load all clients into combo box"""
        try:
            clients = self.db_manager.get_all_clients()
            client_names = [client.name for client in clients]
            self.client_combo['values'] = client_names
            
            # Pre-select client if specified
            if self.client_id:
                client = self.db_manager.get_client(self.client_id)
                if client:
                    self.client_var.set(client.name)
                    self._display_client_info(client)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error loading clients: {str(e)}")
    
    def _load_invoice(self):
        """Load existing invoice data"""
        try:
            if self.invoice_id is None:
                messagebox.showerror("Error", "No invoice ID provided.")
                self.window.destroy()
                return
            
            self.invoice = self.db_manager.get_invoice(self.invoice_id)
            if not self.invoice:
                messagebox.showerror("Error", "Invoice not found.")
                self.window.destroy()
                return
            
            # Load basic info
            self.invoice_number_var.set(self.invoice.invoice_number)
            self.status_var.set(self.invoice.status)
            self.invoice_date_var.set(self.invoice.invoice_date.strftime('%Y-%m-%d') if self.invoice.invoice_date else "")
            self.due_date_var.set(self.invoice.due_date.strftime('%Y-%m-%d') if self.invoice.due_date else "")
            self.payment_terms_var.set(self.invoice.payment_terms)
            self.currency_var.set(self.invoice.currency)
            
            # Set tax rate
            for rate_name, rate_value in DEFAULT_TAX_RATES.items():
                if abs(rate_value - self.invoice.tax_rate) < 0.001:
                    self.tax_rate_var.set(rate_name)
                    break
            else:
                self.tax_rate_var.set("Custom")
            
            # Load client
            if self.invoice.client:
                self.client_var.set(self.invoice.client.name)
                self._display_client_info(self.invoice.client)
            
            # Load items
            self.items = self.invoice.items.copy()
            self._refresh_items_display()
            
            # Load notes
            self.notes_text.delete('1.0', 'end')
            self.notes_text.insert('1.0', self.invoice.notes or "")
            
            # Update totals
            self._calculate_totals()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading invoice: {str(e)}")
    
    def _setup_new_invoice(self):
        """Setup new invoice with defaults"""
        # Generate invoice number
        settings = self.db_manager.get_app_settings()
        invoice_number = settings.get_next_invoice_number()
        self.invoice_number_var.set(invoice_number)
        
        # Calculate due date based on default payment terms
        self._calculate_due_date()
        
        # Initialize empty items list
        self.items = []
        self._refresh_items_display()
    
    # Event handlers
    def _on_client_selected(self, event=None):
        """Handle client selection"""
        client_name = self.client_var.get()
        if client_name:
            client = self.db_manager.get_client_by_name(client_name)
            if client:
                self._display_client_info(client)
    
    def _on_payment_terms_changed(self, event=None):
        """Handle payment terms change"""
        self._calculate_due_date()
    
    def _on_currency_changed(self, event=None):
        """Handle currency change"""
        self._calculate_totals()
    
    def _on_tax_rate_changed(self, event=None):
        """Handle tax rate change"""
        self._calculate_totals()
    
    # Utility methods
    def _display_client_info(self, client: Client):
        """Display client information"""
        self.client_info_text.config(state='normal')
        self.client_info_text.delete('1.0', 'end')
        
        info_lines = [client.name]
        if client.email:
            info_lines.append(f"Email: {client.email}")
        if client.phone:
            info_lines.append(f"Phone: {client.phone}")
        if client.full_address:
            info_lines.extend(client.full_address.split('\n'))
        
        self.client_info_text.insert('1.0', '\n'.join(info_lines))
        self.client_info_text.config(state='disabled')
    
    def _calculate_due_date(self):
        """Calculate due date based on invoice date and payment terms"""
        try:
            invoice_date_str = self.invoice_date_var.get()
            if invoice_date_str:
                invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d')
                payment_terms = self.payment_terms_var.get()
                due_date = DateCalculator.calculate_due_date(invoice_date, payment_terms)
                self.due_date_var.set(due_date.strftime('%Y-%m-%d'))
        except ValueError:
            pass  # Invalid date format
    
    def _calculate_totals(self):
        """Calculate and display invoice totals"""
        try:
            # Get tax rate
            tax_rate_name = self.tax_rate_var.get()
            tax_rate = DEFAULT_TAX_RATES.get(tax_rate_name, 0.0)
            
            # Calculate totals
            items_data = []
            for item in self.items:
                items_data.append({
                    'quantity': item.quantity,
                    'rate': item.rate
                })
            
            totals = calculate_invoice_total(items_data, tax_rate)
            currency = self.currency_var.get()
            
            # Update display
            self.totals_vars['subtotal'].set(CurrencyFormatter.format_currency(totals['subtotal'], currency))
            self.totals_vars['tax_amount'].set(CurrencyFormatter.format_currency(totals['tax_amount'], currency))
            self.totals_vars['total'].set(CurrencyFormatter.format_currency(totals['total'], currency))
            
        except Exception as e:
            messagebox.showerror(
                "Calculation Error",
                f"An error occurred while calculating totals:\n{e}\nValues have been reset to 0.00"
            )
            
            # Reset to zero on error
            currency = self.currency_var.get()
            self.totals_vars['subtotal'].set(CurrencyFormatter.format_currency(0.0, currency))
            self.totals_vars['tax_amount'].set(CurrencyFormatter.format_currency(0.0, currency))
            self.totals_vars['total'].set(CurrencyFormatter.format_currency(0.0, currency))
    
    def _refresh_items_display(self):
        """Refresh the items treeview display"""
        # Clear existing items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        # Add items
        currency = self.currency_var.get()
        for i, item in enumerate(self.items):
            amount = CurrencyFormatter.format_currency(item.total, currency)
            rate = CurrencyFormatter.format_currency(item.rate, currency)
            
            self.items_tree.insert('', 'end', values=(
                item.description,
                f"{item.quantity:g}",  # Remove trailing zeros
                rate,
                amount
            ), tags=(str(i),))
        
        # Recalculate totals
        self._calculate_totals()
    
    # Item management methods
    def _add_item(self):
        """Add new item to invoice"""
        dialog = ItemDialog(self.window, "Add Item")
        self.window.wait_window(dialog.window)
        
        if dialog.result:
            item = InvoiceItem(
                description=dialog.result['description'],
                quantity=dialog.result['quantity'],
                rate=dialog.result['rate']
            )
            self.items.append(item)
            self._refresh_items_display()
    
    def _edit_selected_item(self):
        """Edit selected item"""
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to edit.")
            return
        
        # Get item index from tags
        item_index = int(self.items_tree.item(selection[0])['tags'][0])
        item = self.items[item_index]
        
        dialog = ItemDialog(self.window, "Edit Item", item)
        self.window.wait_window(dialog.window)
        
        if dialog.result:
            # Update item
            item.description = dialog.result['description']
            item.quantity = dialog.result['quantity']
            item.rate = dialog.result['rate']
            item.amount = item.quantity * item.rate  # Recalculate
            
            self._refresh_items_display()
    
    def _remove_selected_item(self):
        """Remove selected item"""
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to remove.")
            return
        
        if messagebox.askyesno("Confirm", "Remove selected item?"):
            # Get item index from tags
            item_index = int(self.items_tree.item(selection[0])['tags'][0])
            del self.items[item_index]
            self._refresh_items_display()
    
    def _create_new_client(self):
        """Create new client"""
        from gui.client_manager import ClientFormWindow
        form = ClientFormWindow(self.window, self.db_manager)
        self.window.wait_window(form.window)
        
        # Reload clients and select the new one if created
        self._load_clients()
        if hasattr(form, 'created_client_name') and form.created_client_name is not None:
            self.client_var.set(form.created_client_name)
            self._on_client_selected()
    
    def _save_invoice(self):
        """Save the invoice"""
        try:
            # Validate form
            if not self._validate_form():
                return
            
            # Get selected client
            client_name = self.client_var.get()
            if not client_name:
                messagebox.showerror("Error", "Please select a client.")
                return
            
            client = self.db_manager.get_client_by_name(client_name)
            if not client:
                messagebox.showerror("Error", "Selected client not found.")
                return
            
            if client.id is None:
                messagebox.showerror("Error", "Client ID is missing.")
                return
            
            # Create or get invoice object
            invoice = self.invoice if self.invoice is not None else Invoice()

            # If it's a new invoice, update settings with new invoice number
            if self.invoice is None:
                settings = self.db_manager.get_app_settings()
                self.db_manager.save_app_settings(settings)

            
            # Set invoice data
            invoice.invoice_number = self.invoice_number_var.get()
            invoice.client_id = client.id
            invoice.client = client
            invoice.status = self.status_var.get()
            
            # Parse dates
            try:
                invoice.invoice_date = datetime.strptime(self.invoice_date_var.get(), '%Y-%m-%d')
                invoice.due_date = datetime.strptime(self.due_date_var.get(), '%Y-%m-%d')
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid date format: {str(e)}")
                return
            
            invoice.payment_terms = self.payment_terms_var.get()
            invoice.currency = self.currency_var.get()
            
            # Set tax rate
            tax_rate_name = self.tax_rate_var.get()
            invoice.tax_rate = DEFAULT_TAX_RATES.get(tax_rate_name, 0.0)
            
            # Set items
            invoice.items = self.items.copy()
            
            # Set notes
            invoice.notes = self.notes_text.get('1.0', 'end-1c').strip()
            
            # Set company info from settings
            invoice.company_name = self.app_settings.company_name
            invoice.company_address = self.app_settings.company_address
            invoice.company_phone = self.app_settings.company_phone
            invoice.company_email = self.app_settings.company_email
            invoice.company_website = self.app_settings.company_website
            
            # Save invoice
            saved_invoice = self.db_manager.save_invoice(invoice)
            self.invoice = saved_invoice
            self.invoice_id = saved_invoice.id
            
            messagebox.showinfo("Success", "Invoice saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving invoice: {str(e)}")
    
    def _validate_form(self):
        """Validate form data"""
        # Validate invoice number
        if not self.invoice_number_var.get().strip():
            messagebox.showerror("Error", "Invoice number is required.")
            return False
        
        # Validate dates
        try:
            datetime.strptime(self.invoice_date_var.get(), '%Y-%m-%d')
            datetime.strptime(self.due_date_var.get(), '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return False
        
        # Validate items
        if not self.items:
            messagebox.showerror("Error", "Invoice must contain at least one item.")
            return False
        
        # Validate client selection
        if not self.client_var.get():
            messagebox.showerror("Error", "Please select a client.")
            return False
        
        return True
    


    def _generate_pdf(self):
        """Generate PDF for current invoice"""
        if not self.invoice_id or not self.invoice:
            messagebox.showwarning("Save Required", "Please save the invoice before generating PDF.")
            return

        try:
            # Ask for save location
            filename = f"Invoice_{self.invoice.formatted_invoice_number}.pdf"
            output_path = filedialog.asksaveasfilename(
                title="Save Invoice PDF",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=filename
            )

            if output_path:
                generator = InvoicePDFGenerator()
                final_path = generator.generate_invoice_pdf(self.invoice, output_path)

                messagebox.showinfo("Success", f"PDF generated successfully!\nSaved to: {final_path}")

                # Ask if user wants to open the file
                if messagebox.askyesno("Open File", "Would you like to open the PDF file?"):
                    import os
                    os.startfile(final_path)
            else:
                return  # User cancelled

        except Exception as e:
            messagebox.showerror("Error", f"Error generating PDF: {str(e)}")


class ItemDialog:
    """Dialog for adding/editing invoice items"""
    
    def __init__(self, parent, title: str, item: Optional[InvoiceItem] = None):
        self.parent = parent
        self.item = item
        self.result = None
        
        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x300")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center dialog
        self._center_dialog()
        
        # Create widgets
        self._create_widgets()
        
        # Load existing item data if editing
        if self.item:
            self._load_item_data()
        
        # Focus on description field
        self.description_entry.focus()
    
    def _center_dialog(self):
        """Center dialog on parent"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (200)
        y = (self.window.winfo_screenheight() // 2) - (150)
        self.window.geometry(f"400x300+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=0, column=0, sticky='w', pady=(0, 5))
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(main_frame, textvariable=self.description_var, width=40)
        self.description_entry.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        # Quantity
        ttk.Label(main_frame, text="Quantity:").grid(row=2, column=0, sticky='w', pady=(0, 5))
        self.quantity_var = tk.StringVar(value="1")
        quantity_entry = ttk.Entry(main_frame, textvariable=self.quantity_var, width=15)
        quantity_entry.grid(row=3, column=0, sticky='w', pady=(0, 15))
        quantity_entry.bind('<KeyRelease>', self._calculate_amount)
        
        # Rate
        ttk.Label(main_frame, text="Rate:").grid(row=4, column=0, sticky='w', pady=(0, 5))
        self.rate_var = tk.StringVar(value="0.00")
        rate_entry = ttk.Entry(main_frame, textvariable=self.rate_var, width=15)
        rate_entry.grid(row=5, column=0, sticky='w', pady=(0, 15))
        rate_entry.bind('<KeyRelease>', self._calculate_amount)
        
        # Amount (calculated)
        ttk.Label(main_frame, text="Amount:").grid(row=6, column=0, sticky='w', pady=(0, 5))
        self.amount_var = tk.StringVar(value="0.00")
        amount_label = ttk.Label(main_frame, textvariable=self.amount_var, 
                                font=HEADER_FONT, foreground=PRIMARY_COLOR)
        amount_label.grid(row=7, column=0, sticky='w', pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, sticky='ew')
        
        ttk.Button(button_frame, text="Save", style='Primary.TButton',
                  command=self._save_item).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", 
                  command=self._cancel).pack(side='right')
        
        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Bind Enter key to save
        self.window.bind('<Return>', lambda e: self._save_item())
        self.window.bind('<Escape>', lambda e: self._cancel())
    
    def _load_item_data(self):
        if self.item is None:
            return
        """Load existing item data into form"""
        self.description_var.set(self.item.description)
        self.quantity_var.set(str(self.item.quantity))
        self.rate_var.set(str(self.item.rate))
        self._calculate_amount()
    
    def _calculate_amount(self, event=None):
        """Calculate and display amount"""
        try:
            quantity = float(self.quantity_var.get() or 0)
            rate = float(self.rate_var.get() or 0)
            amount = quantity * rate
            self.amount_var.set(f"${amount:.2f}")
        except ValueError:
            self.amount_var.set("$0.00")
    
    def _save_item(self):
        """Save the item"""
        try:
            # Validate inputs
            description = self.description_var.get().strip()
            if not description:
                messagebox.showerror("Error", "Description is required.")
                return
            
            try:
                quantity = float(self.quantity_var.get())
                rate = float(self.rate_var.get())
            except ValueError:
                messagebox.showerror("Error", "Quantity and rate must be valid numbers.")
                return
            
            if quantity <= 0:
                messagebox.showerror("Error", "Quantity must be greater than 0.")
                return
            
            if rate < 0:
                messagebox.showerror("Error", "Rate cannot be negative.")
                return
            
            # Create result
            self.result = {
                'description': description,
                'quantity': quantity,
                'rate': rate
            }
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving item: {str(e)}")
    
    def _cancel(self):
        """Cancel dialog"""
        self.result = None
        self.window.destroy()

# Configure ttk styles for this module
def configure_styles():
    """Configure custom styles for invoice form"""
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