# File: main.py
# Location: InvoiceGeneratorPro/main.py

"""
Invoice Generator Pro - Main Application Entry Point

Professional invoice generation software for freelancers and small businesses.

Features:
- Client management
- Invoice creation and tracking
- PDF generation with multiple templates
- Dashboard with revenue analytics
- Data export and backup

Author: Your Business Name
Version: 1.0.0
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add the project directory to Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def setup_error_handling():
    """Setup global error handling for end users"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions with user-friendly messages"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow Ctrl+C to exit normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Show user-friendly error dialog
        try:
            from config import APP_NAME
            root = tk.Tk()
            root.withdraw()
            
            user_msg = f"""An unexpected error occurred in {APP_NAME}.

The application will close. Please restart the program.

If this problem persists, please contact support.

Error: {exc_type.__name__}"""
            
            messagebox.showerror("Application Error", user_msg)
            root.destroy()
        except Exception:
            # If GUI fails, just exit gracefully
            print(f"Application error: {exc_type.__name__}: {str(exc_value)}")
    
    # Set the exception handler
    sys.excepthook = handle_exception

def initialize_database():
    """Initialize database and return success status"""
    try:
        from database.db_manager import DatabaseManager
        db_manager = DatabaseManager()
        # Test basic functionality
        db_manager.get_dashboard_stats()
        return True
    except Exception:
        return False

def create_sample_data():
    """Create sample data for new users"""
    try:
        from database.db_manager import DatabaseManager
        from database.models import Client, Invoice, InvoiceItem
        from datetime import datetime, timedelta
        
        db_manager = DatabaseManager()
        
        # Check if we already have data
        stats = db_manager.get_dashboard_stats()
        if stats['total_clients'] > 0:
            return  # Already have data
        
        # Create sample clients
        sample_clients = [
            Client(
                name="Acme Corporation",
                email="billing@acme.com",
                phone="(555) 123-4567",
                address="123 Business St",
                city="New York",
                state="NY",
                zip_code="10001",
                country="United States"
            ),
            Client(
                name="Tech Solutions Inc",
                email="accounts@techsolutions.com", 
                phone="(555) 987-6543",
                address="456 Innovation Ave",
                city="San Francisco",
                state="CA",
                zip_code="94102",
                country="United States"
            ),
            Client(
                name="Green Energy Partners",
                email="finance@greenenergy.com",
                phone="(555) 456-7890",
                address="789 Sustainable Blvd",
                city="Austin",
                state="TX",
                zip_code="73301",
                country="United States"
            )
        ]
        
        # Save sample clients
        saved_clients = []
        for client in sample_clients:
            saved_client = db_manager.save_client(client)
            saved_clients.append(saved_client)
        
        # Create sample invoices
        base_date = datetime.now() - timedelta(days=30)
        
        for i, client in enumerate(saved_clients):
            # Create 2-3 invoices per client
            for j in range(2 + (i % 2)):  # 2 or 3 invoices
                invoice = Invoice(
                    client_id=client.id,
                    client=client,
                    invoice_date=base_date + timedelta(days=j*7 + i*3),
                    payment_terms="Net 30",
                    currency="USD",
                    tax_rate=0.0875,  # 8.75% tax
                    status=["Draft", "Sent", "Paid"][j % 3],
                    company_name="Your Business Name",
                    company_address="123 Your Street\nYour City, State 12345",
                    company_phone="(555) 000-0000",
                    company_email="billing@yourbusiness.com",
                    company_website="www.yourbusiness.com"
                )
                
                # Add sample items
                sample_items = [
                    InvoiceItem(
                        description=f"Consulting Services - Phase {j+1}",
                        quantity=10.0,
                        rate=150.0
                    ),
                    InvoiceItem(
                        description="Project Documentation",
                        quantity=1.0,
                        rate=500.0
                    )
                ]
                
                if j == 0:  # Add extra item to first invoice
                    sample_items.append(InvoiceItem(
                        description="Additional Analysis",
                        quantity=5.0,
                        rate=200.0
                    ))
                
                invoice.items = sample_items
                
                # Save invoice
                db_manager.save_invoice(invoice)
        
        # Update app settings with sample company info
        settings = db_manager.get_app_settings()
        settings.company_name = "Your Business Name"
        settings.company_address = "123 Your Street\nYour City, State 12345"
        settings.company_phone = "(555) 000-0000"
        settings.company_email = "billing@yourbusiness.com"
        settings.company_website = "www.yourbusiness.com"
        settings.default_currency = "USD"
        settings.default_tax_rate = 0.0875
        settings.default_payment_terms = "Net 30"
        db_manager.save_app_settings(settings)
        
    except Exception:
        # Don't fail the app if sample data creation fails
        pass

def show_welcome_message():
    """Show welcome message for first-time users"""
    try:
        from database.db_manager import DatabaseManager
        from config import APP_NAME, APP_VERSION
        
        db_manager = DatabaseManager()
        stats = db_manager.get_dashboard_stats()
        
        # Only show welcome if no data exists
        if stats['total_clients'] == 0 and stats['total_invoices'] == 0:
            root = tk.Tk()
            root.withdraw()
            
            welcome_msg = f"""Welcome to {APP_NAME} v{APP_VERSION}!

Getting started is easy:

1. Go to Settings to add your company information
2. Add your first client in the Clients tab
3. Create your first invoice in the Invoices tab
4. Generate professional PDF invoices

Sample data has been created to help you explore the features.
You can delete this sample data once you're ready to add your own.

Click OK to open the application."""
            
            messagebox.showinfo("Welcome", welcome_msg)
            root.destroy()
            
    except Exception:
        # Don't fail if welcome message fails
        pass

def main():
    """Main application entry point"""
    # Setup error handling for end users
    setup_error_handling()
    
    try:
        # Initialize database
        if not initialize_database():
            # Show user-friendly error
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Database Error", 
                               "Unable to initialize the application database.\n\n" +
                               "Please ensure you have write permissions to the Documents folder\n" +
                               "and try running the application as administrator.")
            root.destroy()
            return 1
        
        # Create sample data if needed
        create_sample_data()
        
        # Show welcome message for new users
        show_welcome_message()
        
        # Import and start main application
        from gui.main_window import MainWindow
        
        # Create and run the application
        app = MainWindow()
        app.run()
        
        return 0
        
    except KeyboardInterrupt:
        return 0
        
    except Exception as e:
        # Show user-friendly error for any startup failures
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", 
                               "Unable to start the application.\n\n" +
                               "Please try restarting the program.\n" +
                               "If the problem persists, contact support.\n\n" +
                               f"Error: {str(e)}")
            root.destroy()
        except Exception:
            pass
        
        return 1

if __name__ == "__main__":
    """Entry point when application is launched"""
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception:
        # Final fallback - just exit gracefully
        sys.exit(1)