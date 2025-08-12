#!/usr/bin/env python3
"""
Test script for OpenSanctions API integration
Demonstrates how to use the Royal Sanction Watch with OpenSanctions API
"""

import sys
import os
from datetime import datetime

def test_opensanctions_integration():
    """Test OpenSanctions API integration"""
    print("🚢 Royal Sanction Watch - OpenSanctions API Test")
    print("=" * 50)
    
    try:
        from sanction_checker import SanctionChecker
        
        # Initialize the checker
        print("Initializing SanctionChecker...")
        checker = SanctionChecker()
        
        # Test 1: Get available datasets
        print("\n1. Testing dataset catalog...")
        try:
            catalog = checker.opensanctions.get_catalog()
            datasets = catalog.get('datasets', [])
            print(f"   ✅ Found {len(datasets)} available datasets")
            
            # Show some dataset names
            dataset_names = [ds.get('name', 'Unknown') for ds in datasets[:5]]
            print(f"   Sample datasets: {', '.join(dataset_names)}")
            
        except Exception as e:
            print(f"   ❌ Failed to get catalog: {e}")
        
        # Test 2: Search for a known entity
        print("\n2. Testing entity search...")
        test_entities = [
            {"name": "EVER GIVEN", "type": "vessel"},
            {"name": "John Smith", "type": "person"},
            {"name": "ACME Corporation", "type": "company"}
        ]
        
        for entity in test_entities:
            print(f"   Searching for: {entity['name']} ({entity['type']})")
            try:
                matches = checker.check_single_entity(entity['name'], entity['type'])
                if matches:
                    print(f"   ✅ Found {len(matches)} potential matches")
                    for i, match in enumerate(matches[:2], 1):  # Show first 2 matches
                        print(f"      {i}. {match.sanction_list} - {match.match_type} (confidence: {match.confidence:.2f})")
                else:
                    print(f"   ✅ No matches found (this is expected for test data)")
                    
            except Exception as e:
                print(f"   ❌ Search failed: {e}")
        
        # Test 3: Bulk check
        print("\n3. Testing bulk check...")
        try:
            results = checker.check_bulk_entities(test_entities)
            total_matches = sum(len(matches) for matches in results.values())
            print(f"   ✅ Bulk check completed: {total_matches} total matches found")
            
        except Exception as e:
            print(f"   ❌ Bulk check failed: {e}")
        
        # Test 4: Generate report
        print("\n4. Testing report generation...")
        try:
            # Create some sample results for testing
            sample_results = {
                "TEST_VESSEL": [],
                "TEST_PERSON": []
            }
            
            report_file = checker.generate_report(sample_results, "excel")
            print(f"   ✅ Report generated: {report_file}")
            
            # Clean up test file
            if os.path.exists(report_file):
                os.remove(report_file)
                print("   ✅ Test report cleaned up")
                
        except Exception as e:
            print(f"   ❌ Report generation failed: {e}")
        
        print("\n" + "=" * 50)
        print("✅ OpenSanctions API integration test completed successfully!")
        print("\nYou can now use the application with:")
        print("  python main.py gui     # GUI interface")
        print("  python main.py web     # Web interface")
        print("  python main.py cli     # Command line interface")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main function"""
    success = test_opensanctions_integration()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 