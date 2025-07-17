# File: db_manager.py
# Location: InvoiceGeneratorPro/database/db_manager.py

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Optional, Tuple
from contextlib import contextmanager

from .models import Client, Invoice, InvoiceItem, AppSettings
from config import DATABASE_PATH, ERROR_MESSAGES, SUCCESS_MESSAGES

class DatabaseManager:
    """Handles all database operations for Invoice Generator Pro"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create clients table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    country TEXT,
                    created_date TEXT,
                    notes TEXT
                )
            ''')
            
            # Create invoices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT UNIQUE NOT NULL,
                    client_id INTEGER NOT NULL,
                    invoice_date TEXT,
                    due_date TEXT,
                    status TEXT DEFAULT 'Draft',
                    items TEXT,
                    subtotal REAL DEFAULT 0.0,
                    tax_rate REAL DEFAULT 0.0,
                    tax_amount REAL DEFAULT 0.0,
                    total REAL DEFAULT 0.0,
                    notes TEXT,
                    payment_terms TEXT DEFAULT 'Net 30',
                    currency TEXT DEFAULT 'USD',
                    created_date TEXT,
                    updated_date TEXT,
                    company_name TEXT,
                    company_address TEXT,
                    company_phone TEXT,
                    company_email TEXT,
                    company_website TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            ''')
            
            # Create app_settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    company_address TEXT,
                    company_phone TEXT,
                    company_email TEXT,
                    company_website TEXT,
                    default_currency TEXT DEFAULT 'USD',
                    default_tax_rate REAL DEFAULT 0.0,
                    default_payment_terms TEXT DEFAULT 'Net 30',
                    invoice_number_format TEXT DEFAULT 'INV-{:04d}',
                    next_invoice_number INTEGER DEFAULT 1,
                    auto_backup INTEGER DEFAULT 1,
                    backup_frequency INTEGER DEFAULT 7,
                    last_backup TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_name ON clients (name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_number ON invoices (invoice_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_client ON invoices (client_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_status ON invoices (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_date ON invoices (invoice_date)')
            
            conn.commit()
            
            # Initialize default settings if not exists
            self._init_default_settings()
    
    def _init_default_settings(self):
        """Initialize default app settings"""
        settings = self.get_app_settings()
        if not settings:
            default_settings = AppSettings()
            self.save_app_settings(default_settings)
    
    # CLIENT OPERATIONS
    
    def save_client(self, client: Client) -> Client:
        """Save or update a client"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            client_data = client.to_dict()
            client_data.pop('id', None)  # Remove id for insert/update
            
            if client.id:
                # Update existing client
                set_clause = ', '.join([f"{key} = ?" for key in client_data.keys()])
                query = f"UPDATE clients SET {set_clause} WHERE id = ?"
                values = list(client_data.values()) + [client.id]
            else:
                # Insert new client
                columns = ', '.join(client_data.keys())
                placeholders = ', '.join(['?' for _ in client_data])
                query = f"INSERT INTO clients ({columns}) VALUES ({placeholders})"
                values = list(client_data.values())
            
            try:
                cursor.execute(query, values)
                conn.commit()
                
                if not client.id:
                    client.id = cursor.lastrowid
                
                return client
            except sqlite3.IntegrityError:
                raise ValueError(ERROR_MESSAGES["duplicate_client"])
    
    def get_client(self, client_id: int) -> Optional[Client]:
        """Get client by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
            row = cursor.fetchone()
            
            if row:
                return Client.from_dict(dict(row))
            return None
    
    def get_client_by_name(self, name: str) -> Optional[Client]:
        """Get client by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                return Client.from_dict(dict(row))
            return None
    
    def get_all_clients(self) -> List[Client]:
        """Get all clients"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients ORDER BY name")
            rows = cursor.fetchall()
            
            return [Client.from_dict(dict(row)) for row in rows]
    
    def search_clients(self, search_term: str) -> List[Client]:
        """Search clients by name or email"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT * FROM clients 
                WHERE name LIKE ? OR email LIKE ? 
                ORDER BY name
            """
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_pattern))
            rows = cursor.fetchall()
            
            return [Client.from_dict(dict(row)) for row in rows]
    
    def delete_client(self, client_id: int) -> bool:
        """Delete a client (only if no invoices exist)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if client has invoices
            cursor.execute("SELECT COUNT(*) FROM invoices WHERE client_id = ?", (client_id,))
            invoice_count = cursor.fetchone()[0]
            
            if invoice_count > 0:
                raise ValueError("Cannot delete client with existing invoices")
            
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    # INVOICE OPERATIONS
    
    def save_invoice(self, invoice: Invoice) -> Invoice:
        """Save or update an invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure we have a valid client
            if not invoice.client_id or not self.get_client(invoice.client_id):
                raise ValueError("Valid client is required")
            
            # Generate invoice number if new invoice
            if not invoice.id and not invoice.invoice_number:
                settings = self.get_app_settings()
                invoice.invoice_number = settings.get_next_invoice_number()
                self.save_app_settings(settings)
            
            # Recalculate totals
            invoice.calculate_totals()
            
            invoice_data = invoice.to_dict()
            invoice_data.pop('id', None)  # Remove id for insert/update
            
            if invoice.id:
                # Update existing invoice
                set_clause = ', '.join([f"{key} = ?" for key in invoice_data.keys()])
                query = f"UPDATE invoices SET {set_clause} WHERE id = ?"
                values = list(invoice_data.values()) + [invoice.id]
            else:
                # Insert new invoice
                columns = ', '.join(invoice_data.keys())
                placeholders = ', '.join(['?' for _ in invoice_data])
                query = f"INSERT INTO invoices ({columns}) VALUES ({placeholders})"
                values = list(invoice_data.values())
            
            try:
                cursor.execute(query, values)
                conn.commit()
                
                if not invoice.id:
                    invoice.id = cursor.lastrowid
                
                return invoice
            except sqlite3.IntegrityError:
                raise ValueError("Invoice number must be unique")
    
    def get_invoice(self, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by ID with client information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
            row = cursor.fetchone()
            
            if row:
                invoice = Invoice.from_dict(dict(row))
                # Load client information
                invoice.client = self.get_client(invoice.client_id)
                return invoice
            return None
    
    def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE invoice_number = ?", (invoice_number,))
            row = cursor.fetchone()
            
            if row:
                invoice = Invoice.from_dict(dict(row))
                invoice.client = self.get_client(invoice.client_id)
                return invoice
            return None
    
    def get_all_invoices(self) -> List[Invoice]:
        """Get all invoices with client information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.*, c.name as client_name 
                FROM invoices i 
                JOIN clients c ON i.client_id = c.id 
                ORDER BY i.created_date DESC
            """)
            rows = cursor.fetchall()
            
            invoices = []
            for row in rows:
                row_dict = dict(row)
                # Remove client_name from invoice data
                row_dict.pop('client_name', None)
                invoice = Invoice.from_dict(row_dict)
                invoice.client = self.get_client(invoice.client_id)
                invoices.append(invoice)
            
            return invoices
    
    def get_invoices_by_status(self, status: str) -> List[Invoice]:
        """Get invoices by status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE status = ? ORDER BY created_date DESC", (status,))
            rows = cursor.fetchall()
            
            invoices = []
            for row in rows:
                invoice = Invoice.from_dict(dict(row))
                invoice.client = self.get_client(invoice.client_id)
                invoices.append(invoice)
            
            return invoices
    
    def get_invoices_by_client(self, client_id: int) -> List[Invoice]:
        """Get all invoices for a specific client"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE client_id = ? ORDER BY created_date DESC", (client_id,))
            rows = cursor.fetchall()
            
            invoices = []
            for row in rows:
                invoice = Invoice.from_dict(dict(row))
                invoice.client = self.get_client(invoice.client_id)
                invoices.append(invoice)
            
            return invoices
    
    def get_overdue_invoices(self) -> List[Invoice]:
        """Get all overdue invoices"""
        today = datetime.now().date().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM invoices 
                WHERE status = 'Sent' AND due_date < ? 
                ORDER BY due_date ASC
            """, (today,))
            rows = cursor.fetchall()
            
            invoices = []
            for row in rows:
                invoice = Invoice.from_dict(dict(row))
                invoice.client = self.get_client(invoice.client_id)
                invoices.append(invoice)
            
            return invoices
    
    def update_invoice_status(self, invoice_id: int, status: str) -> bool:
        """Update invoice status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE invoices 
                SET status = ?, updated_date = ? 
                WHERE id = ?
            """, (status, datetime.now().isoformat(), invoice_id))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def delete_invoice(self, invoice_id: int) -> bool:
        """Delete an invoice"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    # APP SETTINGS OPERATIONS
    
    def get_app_settings(self) -> AppSettings:
        """Get application settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM app_settings LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                return AppSettings.from_dict(dict(row))
            else:
                return AppSettings()
    
    def save_app_settings(self, settings: AppSettings) -> AppSettings:
        """Save application settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            settings_data = settings.to_dict()
            
            # Check if settings exist
            cursor.execute("SELECT id FROM app_settings LIMIT 1")
            existing = cursor.fetchone()
            
            if existing:
                # Update existing settings
                settings_data.pop('id', None)
                set_clause = ', '.join([f"{key} = ?" for key in settings_data.keys()])
                query = f"UPDATE app_settings SET {set_clause} WHERE id = ?"
                values = list(settings_data.values()) + [existing[0]]
                settings.id = existing[0]
            else:
                # Insert new settings
                settings_data.pop('id', None)
                columns = ', '.join(settings_data.keys())
                placeholders = ', '.join(['?' for _ in settings_data])
                query = f"INSERT INTO app_settings ({columns}) VALUES ({placeholders})"
                values = list(settings_data.values())
            
            cursor.execute(query, values)
            conn.commit()
            
            if not settings.id:
                settings.id = cursor.lastrowid
            
            return settings
    
    # DASHBOARD & ANALYTICS
    
    def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total clients
            cursor.execute("SELECT COUNT(*) FROM clients")
            stats['total_clients'] = cursor.fetchone()[0]
            
            # Total invoices
            cursor.execute("SELECT COUNT(*) FROM invoices")
            stats['total_invoices'] = cursor.fetchone()[0]
            
            # Invoices by status
            cursor.execute("SELECT status, COUNT(*) FROM invoices GROUP BY status")
            status_counts = dict(cursor.fetchall())
            stats['draft_invoices'] = status_counts.get('Draft', 0)
            stats['sent_invoices'] = status_counts.get('Sent', 0)
            stats['paid_invoices'] = status_counts.get('Paid', 0)
            stats['overdue_invoices'] = len(self.get_overdue_invoices())
            
            # Total revenue
            cursor.execute("SELECT SUM(total) FROM invoices WHERE status = 'Paid'")
            result = cursor.fetchone()[0]
            stats['total_revenue'] = result if result else 0.0
            
            # Pending revenue
            cursor.execute("SELECT SUM(total) FROM invoices WHERE status IN ('Sent', 'Draft')")
            result = cursor.fetchone()[0]
            stats['pending_revenue'] = result if result else 0.0
            
            return stats
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            # Update last backup time
            settings = self.get_app_settings()
            settings.last_backup = datetime.now()
            self.save_app_settings(settings)
            
            return True
        except Exception:
            return False