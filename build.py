# File: build.py
# Location: InvoiceGeneratorPro/build.py

"""
Build script for Invoice Generator Pro
Creates a standalone executable using PyInstaller
"""

import os
import subprocess
import shutil
import sys
from pathlib import Path
from datetime import datetime

def clean_previous_builds():
    """Clean up previous build artifacts"""
    print("🧹 Cleaning previous builds...")
    
    folders_to_clean = ['build', 'dist', '__pycache__']
    
    for folder in folders_to_clean:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"   ✓ Removed {folder}/")
    
    # Clean .spec files
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"   ✓ Removed {spec_file}")

def check_dependencies():
    """Check if PyInstaller is available"""
    print("📦 Checking build dependencies...")
    
    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
        print("   ✓ PyInstaller found")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ PyInstaller not found!")
        print("   Install with: pip install pyinstaller")
        return False

def build_executable():
    """Build the standalone executable"""
    print("🔨 Building Invoice Generator Pro executable...")
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',                          # Single executable file
        '--windowed',                         # No console window
        '--name=InvoiceGeneratorPro',        # Executable name
        '--distpath=dist',                   # Output directory
        '--workpath=build',                  # Build directory
        '--specpath=.',                      # Spec file location
        
        # Hidden imports for modules that might not be detected
        '--hidden-import=email_validator',
        '--hidden-import=babel.numbers',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=reportlab.graphics.barcode',
        '--hidden-import=sqlite3',
        
        # Exclude unnecessary modules to reduce size
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        
        # Entry point
        'main.py'
    ]
    
    # Add icon if it exists
    icon_path = Path('assets/icon.ico')
    if icon_path.exists():
        cmd.extend(['--icon', str(icon_path)])
        print(f"   ✓ Using icon: {icon_path}")
    
    print(f"   Running: {' '.join(cmd)}")
    print("   This may take a few minutes...")
    
    # Run PyInstaller
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("   ✅ Build successful!")
        return True
    else:
        print("   ❌ Build failed!")
        print("   STDOUT:", result.stdout)
        print("   STDERR:", result.stderr)
        return False

def get_exe_size():
    """Get the size of the generated executable"""
    exe_path = Path('dist/InvoiceGeneratorPro.exe')
    if exe_path.exists():
        size_bytes = exe_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        return size_mb
    return 0

def create_distribution_package():
    """Create a distribution package with the executable and documentation"""
    print("📦 Creating distribution package...")
    
    exe_path = Path('dist/InvoiceGeneratorPro.exe')
    if not exe_path.exists():
        print("   ❌ Executable not found!")
        return False
    
    # Create distribution folder
    version = "1.0.0"
    timestamp = datetime.now().strftime("%Y%m%d")
    dist_folder = Path(f'InvoiceGeneratorPro_v{version}_{timestamp}')
    
    if dist_folder.exists():
        shutil.rmtree(dist_folder)
    
    dist_folder.mkdir()
    
    # Copy executable
    shutil.copy(exe_path, dist_folder / 'InvoiceGeneratorPro.exe')
    
    # Create README for distribution
    readme_content = f"""# Invoice Generator Pro v{version}

## Installation
1. No installation required!
2. Simply double-click InvoiceGeneratorPro.exe to run

## System Requirements
- Windows 10/11 (64-bit)
- No additional software needed

## First Run
- The application will create sample data to help you get started
- Your data is stored in: Documents/InvoiceGeneratorPro/
- Generated PDFs are saved to: Documents/InvoiceGeneratorPro/Exports/

## Features
- Client management
- Invoice creation and tracking
- Professional PDF generation
- Revenue analytics dashboard
- Data export and backup

## Support
For support or questions, please contact: your-email@domain.com

## File Information
- Executable size: {get_exe_size():.1f} MB
- Built on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Version: {version}
"""
    
    with open(dist_folder / 'README.txt', 'w') as f:
        f.write(readme_content)
    
    # Create quick start guide
    quickstart_content = """# Quick Start Guide

1. FIRST TIME SETUP:
   - Double-click InvoiceGeneratorPro.exe
   - Sample data will be created automatically
   - Explore the features with the sample clients and invoices

2. ADD YOUR COMPANY INFO:
   - Go to Settings tab
   - Fill in your company information
   - This will appear on all your invoices

3. CREATE YOUR FIRST CLIENT:
   - Go to Clients tab
   - Click "New Client"
   - Fill in client details

4. CREATE YOUR FIRST INVOICE:
   - Go to Invoices tab
   - Click "New Invoice"
   - Select your client
   - Add invoice items
   - Save and generate PDF

5. DASHBOARD:
   - View your business statistics
   - Track revenue and overdue invoices
   - Quick access to recent invoices

That's it! You're ready to generate professional invoices.
"""
    
    with open(dist_folder / 'QuickStart.txt', 'w') as f:
        f.write(quickstart_content)
    
    print(f"   ✅ Distribution package created: {dist_folder}")
    print("   📁 Package contains:")
    for item in dist_folder.iterdir():
        size = item.stat().st_size / (1024 * 1024) if item.is_file() else 0
        print(f"      - {item.name} ({size:.1f} MB)" if size > 1 else f"      - {item.name}")
    
    return True

def test_executable():
    """Test if the executable runs without errors"""
    print("🧪 Testing executable...")
    
    exe_path = Path('dist/InvoiceGeneratorPro.exe')
    if not exe_path.exists():
        print("   ❌ Executable not found!")
        return False
    
    print("   ⚠️  Manual testing required:")
    print("   1. Navigate to dist/ folder")
    print("   2. Double-click InvoiceGeneratorPro.exe")
    print("   3. Verify the application launches")
    print("   4. Test creating a client and invoice")
    print("   5. Test PDF generation")
    
    return True

def main():
    """Main build process"""
    print("🚀 Invoice Generator Pro Build Script")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Clean previous builds
    clean_previous_builds()
    
    # Build executable
    if not build_executable():
        print("\n❌ Build failed! Check error messages above.")
        sys.exit(1)
    
    # Get build info
    exe_size = get_exe_size()
    
    print("\n✅ Build completed successfully!")
    print(f"📊 Executable size: {exe_size:.1f} MB")
    print(f"📍 Location: {Path('dist/InvoiceGeneratorPro.exe').absolute()}")
    
    # Create distribution package
    if create_distribution_package():
        print("\n🎉 Ready for distribution!")
    
    # Test instructions
    test_executable()
    
    print("\n" + "=" * 50)
    print("Next steps:")
    print("1. Test the executable thoroughly")
    print("2. Test on a clean machine (without Python installed)")
    print("3. Create Gumroad listing")
    print("4. Profit! 💰")

if __name__ == "__main__":
    main()