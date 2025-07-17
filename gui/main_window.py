# File: main_window.py
# Location: InvoiceGeneratorPro/gui/main_window.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import Invoice, Client
from pdf_generator.invoice_pdf import generate_invoice_pdf
from pdf_generator.templates import generate_invoice_with_template
from utils.calculations import CurrencyFormatter
from config import (
    APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    PRIMARY_COLOR, SECONDARY_COLOR, BACKGROUND_COLOR, TEXT_COLOR, SUCCESS_COLOR, ERROR_COLOR,
    DEFAULT_FONT, HEADER_FONT, TITLE_FONT, BUTTON_FONT, INVOICE_STATUSES, EXPORT_DIR
)

class MainWindow:
    """Main application window for Invoice Generator Pro"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.db_manager = DatabaseManager()
        self.current_invoice: Optional[Invoice] = None
        self.current_client: Optional[Client] = None
        
        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        self._setup_menu()
        
        # Load app settings
        self.app_settings = self.db_manager.get_app_settings()
    
    def _setup_window(self):
        """Configure main window properties"""
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.root.configure(bg=BACKGROUND_COLOR)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (WINDOW_WIDTH // 2)
        y = (self.root.winfo_screenheight() // 2) - (WINDOW_HEIGHT // 2)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        
        # Configure window icon (if available)
        try:
            self.root.iconbitmap("assets/icon.ico")
        except Exception:
            pass  # Icon file not found, continue without it
    
    def _setup_styles(self):
        """Configure ttk styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors and fonts
        self.style.configure('Title.TLabel', 
                           font=TITLE_FONT, 
                           foreground=PRIMARY_COLOR,
                           background=BACKGROUND_COLOR)
        
        self.style.configure('Header.TLabel', 
                           font=HEADER_FONT, 
                           foreground=TEXT_COLOR,
                           background=BACKGROUND_COLOR)
        
        self.style.configure('Primary.TButton',
                           font=BUTTON_FONT,
                           foreground='white',
                           background=PRIMARY_COLOR)
        
        self.style.configure('Success.TButton',
                           font=BUTTON_FONT,
                           foreground='white',
                           background=SUCCESS_COLOR)
        
        self.style.configure('Danger.TButton',
                           font=BUTTON_FONT,
                           foreground='white',
                           background=ERROR_COLOR)
        
        # Treeview styling
        self.style.configure('Treeview.Heading',
                           font=HEADER_FONT,
                           foreground=TEXT_COLOR)
        
        self.style.configure('Treeview',
                           font=DEFAULT_FONT,
                           foreground=TEXT_COLOR,
                           fieldbackground='white')
    
    def _create_widgets(self):
        """Create and layout all widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text=APP_NAME, style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Dashboard tab
        self._create_dashboard_tab()
        
        # Invoices tab
        self._create_invoices_tab()
        
        # Clients tab
        self._create_clients_tab()
        
        # Settings tab
        self._create_settings_tab()
        
        # Status bar
        self._create_status_bar(main_frame)
    
    def _create_dashboard_tab(self):
        """Create dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Dashboard title
        ttk.Label(dashboard_frame, text="Dashboard", style='Header.TLabel').pack(pady=(10, 20))
        
        # Stats frame
        stats_frame = ttk.Frame(dashboard_frame)
        stats_frame.pack(fill='x', padx=20, pady=10)
        
        # Create stats cards
        self.stats_vars = {}
        stats_info = [
            ("Total Clients", "total_clients", PRIMARY_COLOR),
            ("Total Invoices", "total_invoices", SECONDARY_COLOR),
            ("Paid Invoices", "paid_invoices", SUCCESS_COLOR),
            ("Overdue Invoices", "overdue_invoices", ERROR_COLOR)
        ]
        
        for i, (label, var_name, color) in enumerate(stats_info):
            self.stats_vars[var_name] = tk.StringVar(value="0")
            self._create_stat_card(stats_frame, label, self.stats_vars[var_name], color, i)
        
        # Revenue frame
        revenue_frame = ttk.LabelFrame(dashboard_frame, text="Revenue Overview", padding=10)
        revenue_frame.pack(fill='x', padx=20, pady=10)
        
        # Revenue stats
        self.revenue_vars = {
            'total_revenue': tk.StringVar(value="$0.00"),
            'pending_revenue': tk.StringVar(value="$0.00")
        }
        
        ttk.Label(revenue_frame, text="Total Revenue (Paid):").grid(row=0, column=0, sticky='w', padx=(0, 10))
        ttk.Label(revenue_frame, textvariable=self.revenue_vars['total_revenue'], 
                 font=HEADER_FONT, foreground=SUCCESS_COLOR).grid(row=0, column=1, sticky='w')
        
        ttk.Label(revenue_frame, text="Pending Revenue:").grid(row=1, column=0, sticky='w', padx=(0, 10))
        ttk.Label(revenue_frame, textvariable=self.revenue_vars['pending_revenue'], 
                 font=HEADER_FONT, foreground=PRIMARY_COLOR).grid(row=1, column=1, sticky='w')
        
        # Quick actions frame
        actions_frame = ttk.LabelFrame(dashboard_frame, text="Quick Actions", padding=10)
        actions_frame.pack(fill='x', padx=20, pady=10)
        
        # Action buttons
        ttk.Button(actions_frame, text="Create New Invoice", 
                  style='Primary.TButton', command=self._create_new_invoice).pack(side='left', padx=(0, 10))
        ttk.Button(actions_frame, text="Add New Client", 
                  style='Primary.TButton', command=self._create_new_client).pack(side='left', padx=(0, 10))
        ttk.Button(actions_frame, text="View Overdue Invoices", 
                  style='Danger.TButton', command=self._view_overdue_invoices).pack(side='left')
        
        # Recent invoices frame
        recent_frame = ttk.LabelFrame(dashboard_frame, text="Recent Invoices", padding=10)
        recent_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Recent invoices treeview
        self.recent_tree = ttk.Treeview(recent_frame, columns=('Invoice', 'Client', 'Amount', 'Status', 'Date'), 
                                       show='headings', height=8)
        
        # Configure columns
        self.recent_tree.heading('Invoice', text='Invoice #')
        self.recent_tree.heading('Client', text='Client')
        self.recent_tree.heading('Amount', text='Amount')
        self.recent_tree.heading('Status', text='Status')
        self.recent_tree.heading('Date', text='Date')
        
        self.recent_tree.column('Invoice', width=100)
        self.recent_tree.column('Client', width=150)
        self.recent_tree.column('Amount', width=100)
        self.recent_tree.column('Status', width=80)
        self.recent_tree.column('Date', width=100)
        
        # Scrollbar for recent invoices
        recent_scrollbar = ttk.Scrollbar(recent_frame, orient='vertical', command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=recent_scrollbar.set)
        
        # Pack recent invoices widgets
        self.recent_tree.pack(side='left', fill='both', expand=True)
        recent_scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to open invoice
        self.recent_tree.bind('<Double-1>', self._on_recent_invoice_double_click)
    
    def _create_stat_card(self, parent, label, var, color, column):
        """Create a stat card widget"""
        card_frame = ttk.Frame(parent)
        card_frame.grid(row=0, column=column, padx=10, pady=5, sticky='ew')
        
        # Configure column weight
        parent.grid_columnconfigure(column, weight=1)
        
        # Card content
        ttk.Label(card_frame, text=label, font=DEFAULT_FONT).pack()
        ttk.Label(card_frame, textvariable=var, font=HEADER_FONT, foreground=color).pack()
    
    def _create_invoices_tab(self):
        """Create invoices management tab"""
        invoices_frame = ttk.Frame(self.notebook)
        self.notebook.add(invoices_frame, text="Invoices")
        
        # Invoices header
        header_frame = ttk.Frame(invoices_frame)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(header_frame, text="Invoice Management", style='Header.TLabel').pack(side='left')
        
        # Invoice actions
        ttk.Button(header_frame, text="New Invoice", style='Primary.TButton', 
                  command=self._create_new_invoice).pack(side='right', padx=(5, 0))
        ttk.Button(header_frame, text="Refresh", command=self._load_invoices).pack(side='right', padx=(5, 0))
        
        # Filter frame
        filter_frame = ttk.Frame(invoices_frame)
        filter_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by Status:").pack(side='left', padx=(0, 5))
        self.invoice_filter = ttk.Combobox(filter_frame, values=['All'] + INVOICE_STATUSES, 
                                          state='readonly', width=15)
        self.invoice_filter.set('All')
        self.invoice_filter.bind('<<ComboboxSelected>>', self._filter_invoices)
        self.invoice_filter.pack(side='left')
        
        # Invoices treeview
        tree_frame = ttk.Frame(invoices_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.invoices_tree = ttk.Treeview(tree_frame, 
                                         columns=('Invoice', 'Client', 'Date', 'Due', 'Amount', 'Status'), 
                                         show='headings')
        
        # Configure invoice columns
        self.invoices_tree.heading('Invoice', text='Invoice #')
        self.invoices_tree.heading('Client', text='Client')
        self.invoices_tree.heading('Date', text='Invoice Date')
        self.invoices_tree.heading('Due', text='Due Date')
        self.invoices_tree.heading('Amount', text='Amount')
        self.invoices_tree.heading('Status', text='Status')
        
        self.invoices_tree.column('Invoice', width=120)
        self.invoices_tree.column('Client', width=150)
        self.invoices_tree.column('Date', width=100)
        self.invoices_tree.column('Due', width=100)
        self.invoices_tree.column('Amount', width=100)
        self.invoices_tree.column('Status', width=80)
        
        # Scrollbar for invoices
        invoices_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.invoices_tree.yview)
        self.invoices_tree.configure(yscrollcommand=invoices_scrollbar.set)
        
        # Pack invoices widgets
        self.invoices_tree.pack(side='left', fill='both', expand=True)
        invoices_scrollbar.pack(side='right', fill='y')
        
        # Invoice actions frame
        invoice_actions_frame = ttk.Frame(invoices_frame)
        invoice_actions_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(invoice_actions_frame, text="View/Edit", 
                  command=self._edit_selected_invoice).pack(side='left', padx=(0, 5))
        ttk.Button(invoice_actions_frame, text="Generate PDF", style='Success.TButton',
                  command=self._generate_invoice_pdf).pack(side='left', padx=(0, 5))
        ttk.Button(invoice_actions_frame, text="Mark as Paid", 
                  command=self._mark_invoice_paid).pack(side='left', padx=(0, 5))
        ttk.Button(invoice_actions_frame, text="Delete", style='Danger.TButton',
                  command=self._delete_selected_invoice).pack(side='right')
        
        # Bind double-click
        self.invoices_tree.bind('<Double-1>', self._on_invoice_double_click)
    
    def _create_clients_tab(self):
        """Create clients management tab"""
        clients_frame = ttk.Frame(self.notebook)
        self.notebook.add(clients_frame, text="Clients")
        
        # Clients header
        header_frame = ttk.Frame(clients_frame)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(header_frame, text="Client Management", style='Header.TLabel').pack(side='left')
        
        # Client actions
        ttk.Button(header_frame, text="New Client", style='Primary.TButton', 
                  command=self._create_new_client).pack(side='right', padx=(5, 0))
        ttk.Button(header_frame, text="Refresh", command=self._load_clients).pack(side='right', padx=(5, 0))
        
        # Search frame
        search_frame = ttk.Frame(clients_frame)
        search_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.client_search_var = tk.StringVar()
        self.client_search_var.trace('w', self._search_clients)
        search_entry = ttk.Entry(search_frame, textvariable=self.client_search_var, width=30)
        search_entry.pack(side='left')
        
        # Clients treeview
        tree_frame = ttk.Frame(clients_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.clients_tree = ttk.Treeview(tree_frame, 
                                        columns=('Name', 'Email', 'Phone', 'City', 'Invoices'), 
                                        show='headings')
        
        # Configure client columns
        self.clients_tree.heading('Name', text='Name')
        self.clients_tree.heading('Email', text='Email')
        self.clients_tree.heading('Phone', text='Phone')
        self.clients_tree.heading('City', text='City')
        self.clients_tree.heading('Invoices', text='Invoices')
        
        self.clients_tree.column('Name', width=150)
        self.clients_tree.column('Email', width=200)
        self.clients_tree.column('Phone', width=120)
        self.clients_tree.column('City', width=100)
        self.clients_tree.column('Invoices', width=80)
        
        # Scrollbar for clients
        clients_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.clients_tree.yview)
        self.clients_tree.configure(yscrollcommand=clients_scrollbar.set)
        
        # Pack clients widgets
        self.clients_tree.pack(side='left', fill='both', expand=True)
        clients_scrollbar.pack(side='right', fill='y')
        
        # Client actions frame
        client_actions_frame = ttk.Frame(clients_frame)
        client_actions_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(client_actions_frame, text="View/Edit", 
                  command=self._edit_selected_client).pack(side='left', padx=(0, 5))
        ttk.Button(client_actions_frame, text="Create Invoice", style='Success.TButton',
                  command=self._create_invoice_for_client).pack(side='left', padx=(0, 5))
        ttk.Button(client_actions_frame, text="View Invoices", 
                  command=self._view_client_invoices).pack(side='left', padx=(0, 5))
        ttk.Button(client_actions_frame, text="Delete", style='Danger.TButton',
                  command=self._delete_selected_client).pack(side='right')
        
        # Bind double-click
        self.clients_tree.bind('<Double-1>', self._on_client_double_click)
    
    def _create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Settings header
        ttk.Label(settings_frame, text="Application Settings", style='Header.TLabel').pack(pady=(10, 20))
        
        # Company information frame
        company_frame = ttk.LabelFrame(settings_frame, text="Company Information", padding=10)
        company_frame.pack(fill='x', padx=20, pady=10)
        
        # Company fields
        self.company_vars = {}
        company_fields = [
            ('Company Name:', 'company_name'),
            ('Address:', 'company_address'),
            ('Phone:', 'company_phone'),
            ('Email:', 'company_email'),
            ('Website:', 'company_website')
        ]
        
        for i, (label, var_name) in enumerate(company_fields):
            ttk.Label(company_frame, text=label).grid(row=i, column=0, sticky='w', padx=(0, 10), pady=2)
            self.company_vars[var_name] = tk.StringVar()
            if var_name == 'company_address':
                # Multi-line text for address
                text_widget = tk.Text(company_frame, height=3, width=40, font=DEFAULT_FONT)
                text_widget.grid(row=i, column=1, sticky='ew', pady=2)
                self.company_vars[var_name] = text_widget
            else:
                entry = ttk.Entry(company_frame, textvariable=self.company_vars[var_name], width=40)
                entry.grid(row=i, column=1, sticky='ew', pady=2)
        
        company_frame.grid_columnconfigure(1, weight=1)
        
        # Invoice settings frame
        invoice_frame = ttk.LabelFrame(settings_frame, text="Invoice Settings", padding=10)
        invoice_frame.pack(fill='x', padx=20, pady=10)
        
        # Invoice settings fields
        self.invoice_vars = {}
        
        ttk.Label(invoice_frame, text="Default Currency:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.invoice_vars['default_currency'] = tk.StringVar()
        currency_combo = ttk.Combobox(invoice_frame, textvariable=self.invoice_vars['default_currency'],
                                     values=['USD', 'EUR', 'GBP', 'CAD', 'AUD'], state='readonly')
        currency_combo.grid(row=0, column=1, sticky='w', pady=2)
        
        ttk.Label(invoice_frame, text="Default Tax Rate (%):").grid(row=1, column=0, sticky='w', padx=(0, 10))
        self.invoice_vars['default_tax_rate'] = tk.StringVar()
        ttk.Entry(invoice_frame, textvariable=self.invoice_vars['default_tax_rate'], width=10).grid(row=1, column=1, sticky='w', pady=2)
        
        ttk.Label(invoice_frame, text="Default Payment Terms:").grid(row=2, column=0, sticky='w', padx=(0, 10))
        self.invoice_vars['default_payment_terms'] = tk.StringVar()
        terms_combo = ttk.Combobox(invoice_frame, textvariable=self.invoice_vars['default_payment_terms'],
                                  values=['Net 15', 'Net 30', 'Net 45', 'Due on Receipt'], state='readonly')
        terms_combo.grid(row=2, column=1, sticky='w', pady=2)
        
        # Save settings button
        ttk.Button(settings_frame, text="Save Settings", style='Success.TButton',
                  command=self._save_settings).pack(pady=20)
        
        # Load current settings
        self._load_settings()
    
    def _create_status_bar(self, parent):
        """Create status bar"""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief='sunken', anchor='w')
        status_bar.pack(side='bottom', fill='x')
    
    def _setup_menu(self):
        """Setup application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Invoice", command=self._create_new_invoice)
        file_menu.add_command(label="New Client", command=self._create_new_client)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data", command=self._export_data)
        file_menu.add_command(label="Backup Database", command=self._backup_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    # Data loading methods
    def _load_dashboard_data(self):
        """Load and display dashboard data"""
        try:
            stats = self.db_manager.get_dashboard_stats()
            
            # Update stat cards
            self.stats_vars['total_clients'].set(str(stats['total_clients']))
            self.stats_vars['total_invoices'].set(str(stats['total_invoices']))
            self.stats_vars['paid_invoices'].set(str(stats['paid_invoices']))
            self.stats_vars['overdue_invoices'].set(str(stats['overdue_invoices']))
            
            # Update revenue
            self.revenue_vars['total_revenue'].set(CurrencyFormatter.format_currency(stats['total_revenue']))
            self.revenue_vars['pending_revenue'].set(CurrencyFormatter.format_currency(stats['pending_revenue']))
            
            # Load recent invoices
            self._load_recent_invoices()
            
        except Exception as e:
            self._show_error(f"Error loading dashboard data: {str(e)}")
    
    def _load_recent_invoices(self):
        """Load recent invoices for dashboard"""
        try:
            # Clear existing items
            for item in self.recent_tree.get_children():
                self.recent_tree.delete(item)
            
            # Get recent invoices (last 10)
            all_invoices = self.db_manager.get_all_invoices()
            recent_invoices = all_invoices[:10]  # Already sorted by created_date DESC
            
            for invoice in recent_invoices:
                client_name = invoice.client.name if invoice.client else "Unknown"
                amount = CurrencyFormatter.format_currency(invoice.total, invoice.currency)
                date = invoice.invoice_date.strftime('%m/%d/%Y') if invoice.invoice_date else ""
                
                self.recent_tree.insert('', 'end', values=(
                    invoice.formatted_invoice_number,
                    client_name,
                    amount,
                    invoice.status,
                    date
                ), tags=(str(invoice.id),))
                
        except Exception as e:
            self._show_error(f"Error loading recent invoices: {str(e)}")
    
    def _load_invoices(self):
        """Load invoices into treeview"""
        try:
            # Clear existing items
            for item in self.invoices_tree.get_children():
                self.invoices_tree.delete(item)
            
            # Get filter value
            filter_status = self.invoice_filter.get()
            
            # Get invoices based on filter
            if filter_status == 'All':
                invoices = self.db_manager.get_all_invoices()
            else:
                invoices = self.db_manager.get_invoices_by_status(filter_status)
            
            for invoice in invoices:
                client_name = invoice.client.name if invoice.client else "Unknown"
                amount = CurrencyFormatter.format_currency(invoice.total, invoice.currency)
                invoice_date = invoice.invoice_date.strftime('%m/%d/%Y') if invoice.invoice_date else ""
                due_date = invoice.due_date.strftime('%m/%d/%Y') if invoice.due_date else ""
                
                # Color coding for overdue invoices
                tags = [str(invoice.id)]
                if invoice.is_overdue:
                    tags.append('overdue')
                
                self.invoices_tree.insert('', 'end', values=(
                    invoice.formatted_invoice_number,
                    client_name,
                    invoice_date,
                    due_date,
                    amount,
                    invoice.status
                ), tags=tuple(tags))
            
            # Configure tag colors
            self.invoices_tree.tag_configure('overdue', foreground=ERROR_COLOR)
            
        except Exception as e:
            self._show_error(f"Error loading invoices: {str(e)}")
    
    def _load_clients(self):
        """Load clients into treeview"""
        try:
            # Clear existing items
            for item in self.clients_tree.get_children():
                self.clients_tree.delete(item)
            
            # Get all clients
            clients = self.db_manager.get_all_clients()
            
            for client in clients:
                # Get invoice count for this client
                if client.id is not None:
                    client_invoices = self.db_manager.get_invoices_by_client(client.id)
                else:
                    client_invoices = []

                invoice_count = len(client_invoices)
                
                self.clients_tree.insert('', 'end', values=(
                    client.name,
                    client.email or "",
                    client.phone or "",
                    client.city or "",
                    invoice_count
                ), tags=(str(client.id),))
                
        except Exception as e:
            self._show_error(f"Error loading clients: {str(e)}")
    
    def _load_settings(self):
        """Load current settings into form"""
        try:
            settings = self.db_manager.get_app_settings()
            
            # Load company settings
            self.company_vars['company_name'].set(settings.company_name)
            if isinstance(self.company_vars['company_address'], tk.Text):
                self.company_vars['company_address'].delete('1.0', 'end')
                self.company_vars['company_address'].insert('1.0', settings.company_address)
            self.company_vars['company_phone'].set(settings.company_phone)
            self.company_vars['company_email'].set(settings.company_email)
            self.company_vars['company_website'].set(settings.company_website)
            
            # Load invoice settings
            self.invoice_vars['default_currency'].set(settings.default_currency)
            self.invoice_vars['default_tax_rate'].set(str(settings.default_tax_rate * 100))  # Convert to percentage
            self.invoice_vars['default_payment_terms'].set(settings.default_payment_terms)
            
        except Exception as e:
            self._show_error(f"Error loading settings: {str(e)}")
    
    # Filter and search methods
    def _filter_invoices(self, event=None):
        """Filter invoices by status"""
        self._load_invoices()
    
    def _search_clients(self, *args):
        """Search clients as user types"""
        search_term = self.client_search_var.get()
        if not search_term:
            self._load_clients()
            return
        
        try:
            # Clear existing items
            for item in self.clients_tree.get_children():
                self.clients_tree.delete(item)
            
            # Search clients
            clients = self.db_manager.search_clients(search_term)
            
            for client in clients:
                # Get invoice count for this client
                if client.id is not None:
                    client_invoices = self.db_manager.get_invoices_by_client(client.id)
                else:
                    client_invoices = []

                invoice_count = len(client_invoices)
                
                self.clients_tree.insert('', 'end', values=(
                    client.name,
                    client.email or "",
                    client.phone or "",
                    client.city or "",
                    invoice_count
                ), tags=(str(client.id),))
                
        except Exception as e:
            self._show_error(f"Error searching clients: {str(e)}")
    
    # Action methods
    def _create_new_invoice(self):
        """Create a new invoice"""
        from gui.invoice_form import InvoiceFormWindow
        form = InvoiceFormWindow(self.root, self.db_manager)
        self.root.wait_window(form.window)
        self._load_invoices()
        self._load_dashboard_data()
    
    def _create_new_client(self):
        """Create a new client"""
        from gui.client_manager import ClientFormWindow
        form = ClientFormWindow(self.root, self.db_manager)
        self.root.wait_window(form.window)
        self._load_clients()
        self._load_dashboard_data()
    
    def _edit_selected_invoice(self):
        """Edit the selected invoice"""
        selection = self.invoices_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an invoice to edit.")
            return
        
        # Get invoice ID from tags
        item = self.invoices_tree.item(selection[0])
        invoice_id = int(item['tags'][0])
        
        # Open invoice form with existing invoice
        from gui.invoice_form import InvoiceFormWindow
        form = InvoiceFormWindow(self.root, self.db_manager, invoice_id=invoice_id)
        self.root.wait_window(form.window)
        self._load_invoices()
        self._load_dashboard_data()
    
    def _edit_selected_client(self):
        """Edit the selected client"""
        selection = self.clients_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a client to edit.")
            return
        
        # Get client ID from tags
        item = self.clients_tree.item(selection[0])
        client_id = int(item['tags'][0])
        
        # Open client form with existing client
        from gui.client_manager import ClientFormWindow
        form = ClientFormWindow(self.root, self.db_manager, client_id=client_id)
        self.root.wait_window(form.window)
        self._load_clients()
        self._load_dashboard_data()
    
    def _generate_invoice_pdf(self):
        """Generate PDF for selected invoice"""
        selection = self.invoices_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an invoice to generate PDF.")
            return
        
        try:
            # Get invoice ID from tags
            item = self.invoices_tree.item(selection[0])
            invoice_id = int(item['tags'][0])
            
            # Get invoice from database
            invoice_optional = self.db_manager.get_invoice(invoice_id)
            if not invoice_optional:
                messagebox.showerror("Error", "Invoice not found.")
                return
            invoice = invoice_optional
            
            # Ask user for template choice
            template_choice = self._choose_template()
            if not template_choice:
                return
            
            # Generate filename
            from pdf_generator.invoice_pdf import generate_invoice_filename
            filename = generate_invoice_filename(invoice)
            
            # Ask user for save location
            output_path = filedialog.asksaveasfilename(
                title="Save Invoice PDF",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=filename,
                initialdir=EXPORT_DIR
            )
            
            if output_path:
                # Generate PDF
                if template_choice == 'default':

                    final_path = generate_invoice_pdf(invoice, output_path)
                else:
                    final_path = generate_invoice_with_template(invoice, template_choice, output_path)
                
                messagebox.showinfo("Success", f"Invoice PDF generated successfully!\nSaved to: {final_path}")
                self._update_status(f"Invoice PDF generated: {filename}")
                
                # Ask if user wants to open the file
                if messagebox.askyesno("Open File", "Would you like to open the PDF file?"):
                    os.startfile(final_path)  # Windows
            
        except Exception as e:
            self._show_error(f"Error generating PDF: {str(e)}")
    
    def _choose_template(self):
        """Show template selection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose Template")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"400x300+{x}+{y}")
        
        selected_template = tk.StringVar(value='modern')
        
        ttk.Label(dialog, text="Choose Invoice Template", font=HEADER_FONT).pack(pady=10)
        
        # Template options
        frame = ttk.Frame(dialog)
        frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        template_options = [
            ('modern', 'Modern Professional', 'Clean, modern design with blue accents'),
            ('classic', 'Classic Elegant', 'Traditional business design with formal styling'),
            ('minimal', 'Minimal Clean', 'Ultra-clean design with minimal colors'),
            ('default', 'Default', 'Standard invoice layout')
        ]
        
        for value, name, description in template_options:
            radio_frame = ttk.Frame(frame)
            radio_frame.pack(fill='x', pady=5)
            
            ttk.Radiobutton(radio_frame, text=name, variable=selected_template, 
                           value=value).pack(anchor='w')
            ttk.Label(radio_frame, text=description, font=('Arial', 8), 
                     foreground='gray').pack(anchor='w', padx=(20, 0))
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side='bottom', fill='x', padx=20, pady=10)
        
        result: list[Optional[str]] = [None]
        
        def ok_clicked():
            result[0] = selected_template.get()
            dialog.destroy()
        
        def cancel_clicked():
            result[0] = None
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=ok_clicked).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=cancel_clicked).pack(side='right')
        
        self.root.wait_window(dialog)
        return result[0]
    
    def _mark_invoice_paid(self):
        """Mark selected invoice as paid"""
        selection = self.invoices_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an invoice to mark as paid.")
            return
        
        try:
            # Get invoice ID from tags
            item = self.invoices_tree.item(selection[0])
            invoice_id = int(item['tags'][0])
            
            # Confirm action
            if messagebox.askyesno("Confirm", "Mark this invoice as paid?"):
                success = self.db_manager.update_invoice_status(invoice_id, "Paid")
                if success:
                    messagebox.showinfo("Success", "Invoice marked as paid!")
                    self._load_invoices()
                    self._load_dashboard_data()
                else:
                    messagebox.showerror("Error", "Failed to update invoice status.")
            
        except Exception as e:
            self._show_error(f"Error updating invoice: {str(e)}")
    
    def _delete_selected_invoice(self):
        """Delete selected invoice"""
        selection = self.invoices_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an invoice to delete.")
            return
        
        try:
            # Get invoice ID from tags
            item = self.invoices_tree.item(selection[0])
            invoice_id = int(item['tags'][0])
            
            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this invoice?\nThis action cannot be undone."):
                success = self.db_manager.delete_invoice(invoice_id)
                if success:
                    messagebox.showinfo("Success", "Invoice deleted successfully!")
                    self._load_invoices()
                    self._load_dashboard_data()
                else:
                    messagebox.showerror("Error", "Failed to delete invoice.")
            
        except Exception as e:
            self._show_error(f"Error deleting invoice: {str(e)}")
    
    def _delete_selected_client(self):
        """Delete selected client"""
        selection = self.clients_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a client to delete.")
            return
        
        try:
            # Get client ID from tags
            item = self.clients_tree.item(selection[0])
            client_id = int(item['tags'][0])
            
            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this client?\nThis action cannot be undone."):
                success = self.db_manager.delete_client(client_id)
                if success:
                    messagebox.showinfo("Success", "Client deleted successfully!")
                    self._load_clients()
                    self._load_dashboard_data()
                else:
                    messagebox.showerror("Error", "Failed to delete client.")
            
        except Exception as e:
            if "existing invoices" in str(e).lower():
                messagebox.showerror("Cannot Delete", "Cannot delete client with existing invoices.\nPlease delete all invoices for this client first.")
            else:
                self._show_error(f"Error deleting client: {str(e)}")
    
    def _create_invoice_for_client(self):
        """Create new invoice for selected client"""
        selection = self.clients_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a client to create an invoice for.")
            return
        
        # Get client ID from tags
        item = self.clients_tree.item(selection[0])
        client_id = int(item['tags'][0])
        
        # Open invoice form with pre-selected client
        from gui.invoice_form import InvoiceFormWindow
        form = InvoiceFormWindow(self.root, self.db_manager, client_id=client_id)
        self.root.wait_window(form.window)
        self._load_invoices()
        self._load_dashboard_data()
    
    def _view_client_invoices(self):
        """View all invoices for selected client"""
        selection = self.clients_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a client to view invoices.")
            return
        
        # Switch to invoices tab
        self.notebook.select(1)  # Invoices tab
        # Note: Could add client filtering here in future versions
        
    def _view_overdue_invoices(self):
        """View overdue invoices"""
        self.notebook.select(1)  # Switch to invoices tab
        self.invoice_filter.set('Sent')  # Show sent invoices (where overdue ones would be)
        self._load_invoices()
    
    def _save_settings(self):
        """Save application settings"""
        try:
            settings = self.db_manager.get_app_settings()
            
            # Update company settings
            settings.company_name = self.company_vars['company_name'].get()
            if isinstance(self.company_vars['company_address'], tk.Text):
                settings.company_address = self.company_vars['company_address'].get('1.0', 'end-1c')
            settings.company_phone = self.company_vars['company_phone'].get()
            settings.company_email = self.company_vars['company_email'].get()
            settings.company_website = self.company_vars['company_website'].get()
            
            # Update invoice settings
            settings.default_currency = self.invoice_vars['default_currency'].get()
            try:
                tax_rate = float(self.invoice_vars['default_tax_rate'].get()) / 100  # Convert percentage to decimal
                settings.default_tax_rate = tax_rate
            except ValueError:
                settings.default_tax_rate = 0.0
            
            settings.default_payment_terms = self.invoice_vars['default_payment_terms'].get()
            
            # Save to database
            self.db_manager.save_app_settings(settings)
            self.app_settings = settings
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            self._update_status("Settings saved")
            
        except Exception as e:
            self._show_error(f"Error saving settings: {str(e)}")
    
    def _export_data(self):
        """Export data to CSV"""
        try:
            export_dir = filedialog.askdirectory(title="Choose Export Directory", initialdir=EXPORT_DIR)
            if not export_dir:
                return
            
            # Export invoices
            invoices = self.db_manager.get_all_invoices()
            invoice_file = os.path.join(export_dir, f"invoices_export_{datetime.now().strftime('%Y%m%d')}.csv")
            
            with open(invoice_file, 'w', newline='', encoding='utf-8') as f:
                import csv
                writer = csv.writer(f)
                writer.writerow(['Invoice Number', 'Client', 'Date', 'Due Date', 'Amount', 'Status'])
                
                for invoice in invoices:
                    client_name = invoice.client.name if invoice.client else "Unknown"
                    invoice_date = invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else ""
                    due_date = invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else ""
                    
                    writer.writerow([
                        invoice.formatted_invoice_number,
                        client_name,
                        invoice_date,
                        due_date,
                        f"{invoice.total:.2f}",
                        invoice.status
                    ])
            
            # Export clients
            clients = self.db_manager.get_all_clients()
            client_file = os.path.join(export_dir, f"clients_export_{datetime.now().strftime('%Y%m%d')}.csv")
            
            with open(client_file, 'w', newline='', encoding='utf-8') as f:
                import csv
                writer = csv.writer(f)
                writer.writerow(['Name', 'Email', 'Phone', 'Address', 'City', 'State', 'ZIP', 'Country'])
                
                for client in clients:
                    writer.writerow([
                        client.name,
                        client.email or "",
                        client.phone or "",
                        client.address or "",
                        client.city or "",
                        client.state or "",
                        client.zip_code or "",
                        client.country or ""
                    ])
            
            messagebox.showinfo("Export Complete", f"Data exported successfully!\n\nFiles saved:\n- {invoice_file}\n- {client_file}")
            
        except Exception as e:
            self._show_error(f"Error exporting data: {str(e)}")
    
    def _backup_database(self):
        """Create database backup"""
        try:
            backup_file = filedialog.asksaveasfilename(
                title="Save Database Backup",
                defaultextension=".db",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                initialfile=f"invoice_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            
            if backup_file:
                success = self.db_manager.backup_database(backup_file)
                if success:
                    messagebox.showinfo("Backup Complete", f"Database backed up successfully!\nSaved to: {backup_file}")
                else:
                    messagebox.showerror("Backup Failed", "Failed to create database backup.")
            
        except Exception as e:
            self._show_error(f"Error creating backup: {str(e)}")
    
    def _show_about(self):
        """Show about dialog"""
        about_text = f"""{APP_NAME} v{APP_VERSION}

Professional invoice generation software for freelancers and small businesses.

Features:
• Client management
• Invoice creation and tracking
• PDF generation with multiple templates
• Dashboard with revenue analytics
• Data export and backup

© 2024 Your Business Name
Built with Python and tkinter"""
        
        messagebox.showinfo("About", about_text)
    
    # Event handlers for double-clicks
    def _on_recent_invoice_double_click(self, event):
        """Handle double-click on recent invoice"""
        selection = self.recent_tree.selection()
        if selection:
            item = self.recent_tree.item(selection[0])
            invoice_id = int(item['tags'][0])
            
            # Open invoice form
            from gui.invoice_form import InvoiceFormWindow
            form = InvoiceFormWindow(self.root, self.db_manager, invoice_id=invoice_id)
            self.root.wait_window(form.window)
            self._load_dashboard_data()
    
    def _on_invoice_double_click(self, event):
        """Handle double-click on invoice"""
        self._edit_selected_invoice()
    
    def _on_client_double_click(self, event):
        """Handle double-click on client"""
        self._edit_selected_client()
    
    # Utility methods
    def _show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
        self._update_status("Error occurred")
    
    def _update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
        self.root.after(5000, lambda: self.status_var.set("Ready"))  # Clear after 5 seconds
    
    def run(self):
        """Start the application"""
        # Load initial data
        self._load_invoices()
        self._load_clients()
        self._load_dashboard_data()
        
        # Start main loop
        self.root.mainloop()

def main():
    """Main entry point"""
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()