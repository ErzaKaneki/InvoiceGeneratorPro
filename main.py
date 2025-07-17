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
import traceback

# Add the project directory to Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, str(project_root))

# Check version compatibility
def check_python_version():
    if sys.version_info < (3, 8): # pyright: ignore
        # This code is for end users with older Python versions
        error_msg = f"Python 3.8+ required.  Current version: {sys.version}"
        print(error_msg)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Python Version Error", error_msg)
            root.destroy()
        except Exception:
            pass
        return False
    return True

# Import application modules
try:
    from gui.main_window import MainWindow
    from database.db_manager import DatabaseManager
    from config import APP_NAME, APP_VERSION, DATABASE_PATH
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all required dependencies are installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'reportlab',
        'PIL',
        'email_validator',
        'babel',
        'python_dateutil',
        'dnspython'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            if module == 'PIL':
                import PIL # noqa f401
            elif module == 'email_validator':
                import email_validator # noqa F401
            else:
                __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        error_msg = f"""Missing required dependencies:
{chr(10).join(f"  - {module}" for module in missing_modules)}

Please install them using:
pip install -r requirements.txt

Or install individually:
{chr(10).join(f"pip install {module}" for module in missing_modules)}"""
        
        print(error_msg)
        
        # Show GUI error if tkinter is available
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Dependencies", error_msg)
            root.destroy()
        except Exception:
            pass
        
        return False
    
    return True

def check_database():
    """Check database connectivity and initialize if needed"""
    try:
        # Test database connection
        db_manager = DatabaseManager()
        
        # Verify tables exist and are accessible
        stats = db_manager.get_dashboard_stats()
        
        print(f"Database initialized successfully at: {DATABASE_PATH}")
        print(f"Found {stats['total_clients']} clients and {stats['total_invoices']} invoices")
        
        return True
        
    except Exception as e:
        error_msg = f"Database initialization failed: {str(e)}"
        print(error_msg)
        
        # Show GUI error
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Database Error", f"{error_msg}\n\nPlease check database permissions and try again.")
            root.destroy()
        except Exception:
            pass
        
        return False

def setup_error_handling():
    """Setup global error handling"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow Ctrl+C to exit normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log error details
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"Uncaught exception:\n{error_msg}")
        
        # Show user-friendly error dialog
        try:
            root = tk.Tk()
            root.withdraw()
            
            user_msg = f"""An unexpected error occurred in {APP_NAME}:

{exc_type.__name__}: {str(exc_value)}

The application will continue running, but some features may not work correctly.
Please save your work and restart the application.

Technical details have been printed to the console."""
            
            messagebox.showerror("Application Error", user_msg)
            root.destroy()
        except Exception as dialog_error:
            # If GUI error dialog fails, just print
            print(f"Failed to show error dialog: {exc_type.__name__}: {str(exc_value)}")
            print(f"Dialog error: {str(dialog_error)}")
    
    # Set the exception handler
    sys.excepthook = handle_exception

def create_sample_data():
    """Create sample data for demo purposes"""
    try:
        db_manager = DatabaseManager()
        
        # Check if we already have data
        stats = db_manager.get_dashboard_stats()
        if stats['total_clients'] > 0:
            return  # Already have data
        
        print("Creating sample data for demonstration...")
        
        # Import models
        try:
            from database.models import Client, Invoice, InvoiceItem
            from datetime import datetime, timedelta
        except ImportError as e:
            print(f"Cannot create sample data - missing modules: {e}")
            return
            
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
        
        print("Sample data created successfully!")
        print("- 3 sample clients")
        print("- 7 sample invoices") 
        print("- Company settings configured")
        
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")
        # Don't fail the app if sample data creation fails

def show_welcome_message():
    """Show welcome message for first-time users"""
    try:
        db_manager = DatabaseManager()
        stats = db_manager.get_dashboard_stats()
        
        # Only show welcome if no data exists
        if stats['total_clients'] == 0 and stats['total_invoices'] == 0:
            root = tk.Tk()
            root.withdraw()
            
            welcome_msg = f"""Welcome to {APP_NAME} v{APP_VERSION}!

This is your first time running the application. Here's how to get started:

1. Configure your company information in Settings
2. Add your first client in the Clients tab
3. Create your first invoice in the Invoices tab
4. Generate professional PDF invoices

Sample data has been created to help you explore the features.
You can delete this sample data once you're ready to add your own.

Click OK to open the application."""
            
            messagebox.showinfo("Welcome", welcome_msg)
            root.destroy()
            
    except Exception as e:
        print(f"Error showing welcome message: {str(e)}")

def main():
    """Main application entry point"""
    print(f"Starting {APP_NAME} v{APP_VERSION}...")
    print("=" * 50)
    
    # Check Python version first
    if not check_python_version():
        return 1
    
    # Setup error handling
    setup_error_handling()
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        print("Dependency check failed. Exiting.")
        return 1
    print("✓ All dependencies found")
    
    # Check database
    print("Initializing database...")
    if not check_database():
        print("Database check failed. Exiting.")
        return 1
    print("✓ Database ready")
    
    # Create sample data if needed
    create_sample_data()
    
    # Show welcome message for new users
    show_welcome_message()
    
    try:
        print(f"Launching {APP_NAME}...")
        
        # Create and run main application
        app = MainWindow()
        
        print("✓ Application started successfully")
        print(f"Database location: {DATABASE_PATH}")
        print("\nApplication is running. Close the window to exit.")
        
        # Start the GUI event loop
        app.run()
        
        print(f"\n{APP_NAME} closed successfully.")
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{APP_NAME} interrupted by user.")
        return 0
        
    except Exception as e:
        error_msg = f"Failed to start {APP_NAME}: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        
        # Try to show error dialog
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", f"{error_msg}\n\nSee console for details.")
            root.destroy()
        except Exception:
            pass
        
        return 1

if __name__ == "__main__":
    """Entry point when script is run directly"""
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Critical error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)