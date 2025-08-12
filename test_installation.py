#!/usr/bin/env python3
"""
Test script to verify installation and basic functionality
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    required_modules = [
        'requests',
        'pandas',
        'openpyxl',
        'beautifulsoup4',
        'lxml',
        'PIL',
        'fake_useragent',
        'urllib3',
        'streamlit',
        'plotly',
        'numpy',
        'dotenv'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            if module == 'beautifulsoup4':
                import bs4
            elif module == 'PIL':
                import PIL
            else:
                __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\nFailed to import: {', '.join(failed_imports)}")
        print("Please install missing dependencies: pip install -r requirements.txt")
        return False
    
    print("All imports successful!")
    return True

def test_sanction_checker():
    """Test the core sanction checker functionality"""
    print("\nTesting sanction checker...")
    
    try:
        from sanction_checker import SanctionChecker, SanctionMatch
        
        # Initialize checker
        checker = SanctionChecker()
        print("  ✅ SanctionChecker initialized")
        
        # Test entity type detection
        vessel_type = checker._detect_entity_type("EVER GIVEN")
        person_type = checker._detect_entity_type("JOHN SMITH")
        company_type = checker._detect_entity_type("ACME CORPORATION")
        
        print(f"  ✅ Entity type detection: vessel={vessel_type}, person={person_type}, company={company_type}")
        
        # Test text normalization
        normalized = checker._normalize_text("EVER GIVEN")
        print(f"  ✅ Text normalization: 'EVER GIVEN' -> '{normalized}'")
        
        # Test similarity calculation
        similarity = checker._calculate_similarity("EVER GIVEN", "EVER GIVEN")
        print(f"  ✅ Similarity calculation: {similarity}")
        
        # Test OpenSanctions API connection
        try:
            catalog = checker.opensanctions.get_catalog()
            if catalog.get('datasets'):
                print(f"  ✅ OpenSanctions API connection successful ({len(catalog['datasets'])} datasets available)")
            else:
                print("  ⚠️  OpenSanctions API connected but no datasets found")
        except Exception as e:
            print(f"  ⚠️  OpenSanctions API test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Sanction checker test failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import Config
        
        # Test configuration validation
        if Config.validate_config():
            print("  ✅ Configuration validation passed")
        else:
            print("  ⚠️  Configuration validation failed")
        
        # Print current configuration
        Config.print_config()
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_gui_components():
    """Test GUI components"""
    print("\nTesting GUI components...")
    
    try:
        import tkinter as tk
        print("  ✅ Tkinter available")
        
        # Test if we can create a basic window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        print("  ✅ Tkinter window creation successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ GUI test failed: {e}")
        return False

def test_streamlit():
    """Test Streamlit availability"""
    print("\nTesting Streamlit...")
    
    try:
        import streamlit
        print("  ✅ Streamlit available")
        return True
        
    except ImportError:
        print("  ❌ Streamlit not available")
        return False

def test_file_operations():
    """Test file operations"""
    print("\nTesting file operations...")
    
    try:
        import pandas as pd
        
        # Test CSV reading
        sample_file = "sample_data.csv"
        if os.path.exists(sample_file):
            df = pd.read_csv(sample_file)
            print(f"  ✅ CSV reading: {len(df)} rows loaded")
        else:
            print("  ⚠️  Sample data file not found")
        
        # Test Excel writing
        test_df = pd.DataFrame({'test': [1, 2, 3]})
        test_file = "test_output.xlsx"
        test_df.to_excel(test_file, index=False)
        
        if os.path.exists(test_file):
            os.remove(test_file)  # Clean up
            print("  ✅ Excel writing successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ File operations test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Royal Sanction Watch - Installation Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_sanction_checker,
        test_gui_components,
        test_streamlit,
        test_file_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Installation is successful.")
        print("\nYou can now run the application:")
        print("  python main.py gui     # GUI interface")
        print("  python main.py web     # Web interface")
        print("  python main.py cli     # Command line interface")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTo fix installation issues:")
        print("  pip install -r requirements.txt")
        print("  python test_installation.py")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 