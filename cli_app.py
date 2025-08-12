"""
Command Line Interface for Comprehensive Sanction Checker
Provides CLI access to sanction checking functionality
"""

import argparse
import sys
import json
import csv
import os
from datetime import datetime
from typing import List, Dict
import pandas as pd

from sanction_checker import SanctionChecker, SanctionMatch

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Royal Sanction Watch CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check a single entity
  python cli_app.py check "VESSEL_NAME" --type vessel

  # Check multiple entities from a file
  python cli_app.py bulk check input.csv --name-column name --output results.xlsx

  # Update cache
  python cli_app.py cache update

  # Show cache status
  python cli_app.py cache status

  # Test connections
  python cli_app.py test
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check a single entity')
    check_parser.add_argument('entity_name', help='Name of the entity to check')
    check_parser.add_argument('--type', choices=['auto', 'vessel', 'person', 'company'], 
                            default='auto', help='Entity type (default: auto)')
    check_parser.add_argument('--output', '-o', help='Output file (JSON format)')
    check_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Bulk check command
    bulk_parser = subparsers.add_parser('bulk', help='Bulk check operations')
    bulk_subparsers = bulk_parser.add_subparsers(dest='bulk_command', help='Bulk check commands')
    
    bulk_check_parser = bulk_subparsers.add_parser('check', help='Check multiple entities from file')
    bulk_check_parser.add_argument('input_file', help='Input file (CSV or Excel)')
    bulk_check_parser.add_argument('--name-column', required=True, help='Column containing entity names')
    bulk_check_parser.add_argument('--type-column', help='Column containing entity types')
    bulk_check_parser.add_argument('--output', '-o', required=True, help='Output file')
    bulk_check_parser.add_argument('--format', choices=['excel', 'csv', 'json'], 
                                 default='excel', help='Output format')
    bulk_check_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Cache commands
    cache_parser = subparsers.add_parser('cache', help='Cache management')
    cache_subparsers = cache_parser.add_subparsers(dest='cache_command', help='Cache commands')
    
    cache_update_parser = cache_subparsers.add_parser('update', help='Update all cached data')
    cache_update_parser.add_argument('--force', '-f', action='store_true', 
                                   help='Force update even if cache is fresh')
    
    cache_status_parser = cache_subparsers.add_parser('status', help='Show cache status')
    
    cache_clear_parser = cache_subparsers.add_parser('clear', help='Clear all cached data')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test connections to sanction sources')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize checker
    checker = SanctionChecker()
    
    try:
        if args.command == 'check':
            handle_single_check(checker, args)
        elif args.command == 'bulk':
            if args.bulk_command == 'check':
                handle_bulk_check(checker, args)
            else:
                bulk_parser.print_help()
        elif args.command == 'cache':
            if args.cache_command == 'update':
                handle_cache_update(checker, args)
            elif args.cache_command == 'status':
                handle_cache_status(checker)
            elif args.cache_command == 'clear':
                handle_cache_clear(checker)
            else:
                cache_parser.print_help()
        elif args.command == 'test':
            handle_test_connections(checker)
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def handle_single_check(checker: SanctionChecker, args):
    """Handle single entity check"""
    print(f"Checking entity: {args.entity_name} (type: {args.type})")
    
    # Perform check
    matches = checker.check_single_entity(args.entity_name, args.type)
    
    # Display results
    if matches:
        print(f"\n⚠️  Found {len(matches)} potential matches:")
        print("=" * 60)
        
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match.sanction_list} - {match.match_type} match")
            print(f"   Confidence: {match.confidence:.2f}")
            print(f"   Entity Type: {match.entity_type}")
            print(f"   Source: {match.source_url}")
            print(f"   Last Updated: {match.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if args.verbose:
                print("   Details:")
                for key, value in match.details.items():
                    if value and str(value).strip():
                        print(f"     {key}: {value}")
    else:
        print(f"\n✅ No matches found for '{args.entity_name}' in any sanctions lists")
    
    # Save to file if requested
    if args.output:
        save_single_results(args.entity_name, matches, args.output)
        print(f"\nResults saved to: {args.output}")

def handle_bulk_check(checker: SanctionChecker, args):
    """Handle bulk entity check"""
    print(f"Loading entities from: {args.input_file}")
    
    # Load data
    try:
        if args.input_file.endswith('.csv'):
            df = pd.read_csv(args.input_file)
        else:
            df = pd.read_excel(args.input_file)
    except Exception as e:
        print(f"Error loading file: {e}")
        return
    
    print(f"Loaded {len(df)} entities")
    
    # Validate columns
    if args.name_column not in df.columns:
        print(f"Error: Column '{args.name_column}' not found in file")
        print(f"Available columns: {', '.join(df.columns)}")
        return
    
    if args.type_column and args.type_column not in df.columns:
        print(f"Error: Column '{args.type_column}' not found in file")
        print(f"Available columns: {', '.join(df.columns)}")
        return
    
    # Prepare entities
    entities = []
    for _, row in df.iterrows():
        entity = {'name': str(row[args.name_column])}
        if args.type_column:
            entity['type'] = str(row[args.type_column])
        entities.append(entity)
    
    # Perform bulk check
    print(f"\nStarting bulk check of {len(entities)} entities...")
    results = {}
    
    for i, entity in enumerate(entities, 1):
        if args.verbose:
            print(f"Checking {i}/{len(entities)}: {entity['name']}")
        
        matches = checker.check_single_entity(entity['name'], entity.get('type', 'auto'))
        results[entity['name']] = matches
    
    # Generate report
    print(f"\nGenerating report in {args.format} format...")
    report_file = checker.generate_report(results, args.format)
    
    # Copy to requested location if different
    if args.output != report_file:
        import shutil
        shutil.copy2(report_file, args.output)
        os.remove(report_file)  # Remove temporary file
        report_file = args.output
    
    # Display summary
    display_bulk_summary(results)
    print(f"\nReport saved to: {report_file}")

def handle_cache_update(checker: SanctionChecker, args):
    """Handle cache update"""
    print("Updating cached data...")
    
    sources = ['OFAC', 'UK', 'EU', 'UN']
    
    for source in sources:
        print(f"Updating {source} data...")
        try:
            if source == 'OFAC':
                data = checker._fetch_ofac_data()
            elif source == 'UK':
                data = checker._fetch_uk_data()
            elif source == 'EU':
                data = checker._fetch_eu_data()
            elif source == 'UN':
                data = checker._fetch_un_data()
            
            if not data.empty:
                print(f"  ✅ {source}: {len(data)} records")
            else:
                print(f"  ⚠️  {source}: No data retrieved")
        
        except Exception as e:
            print(f"  ❌ {source}: Error - {e}")
    
    print("Cache update completed")

def handle_cache_status(checker: SanctionChecker):
    """Handle cache status display"""
    print("Cache Status:")
    print("=" * 40)
    
    sources = ['OFAC', 'UK', 'EU', 'UN']
    
    for source in sources:
        cache_file = os.path.join(checker.cache_dir, f"{source.lower()}_cache.csv")
        
        if os.path.exists(cache_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            age = datetime.now() - file_time
            
            # Check if cache is fresh
            is_fresh = age < checker.cache_duration
            
            status = "✅ Fresh" if is_fresh else "⚠️  Stale"
            print(f"{source:4} | {status} | Last updated: {file_time.strftime('%Y-%m-%d %H:%M')}")
            
            # Show file size
            size = os.path.getsize(cache_file)
            print(f"     | File size: {size:,} bytes")
        else:
            print(f"{source:4} | ❌ Not cached")
    
    print("\nCache directory:", checker.cache_dir)
    print("Cache duration:", checker.cache_duration)

def handle_cache_clear(checker: SanctionChecker):
    """Handle cache clear"""
    print("Clearing all cached data...")
    
    try:
        import shutil
        if os.path.exists(checker.cache_dir):
            shutil.rmtree(checker.cache_dir)
            os.makedirs(checker.cache_dir, exist_ok=True)
        print("✅ Cache cleared successfully")
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

def handle_test_connections(checker: SanctionChecker):
    """Handle connection testing"""
    print("Testing connections to sanction sources...")
    print("=" * 50)
    
    sources = ['OFAC', 'UK', 'EU', 'UN']
    
    for source in sources:
        print(f"Testing {source}...", end=" ")
        try:
            if source == 'OFAC':
                data = checker._fetch_ofac_data()
            elif source == 'UK':
                data = checker._fetch_uk_data()
            elif source == 'EU':
                data = checker._fetch_eu_data()
            elif source == 'UN':
                data = checker._fetch_un_data()
            
            if not data.empty:
                print(f"✅ Connected ({len(data)} records)")
            else:
                print("⚠️  Connected but no data")
        
        except Exception as e:
            print(f"❌ Failed - {e}")
    
    print("\nConnection test completed")

def save_single_results(entity_name: str, matches: List[SanctionMatch], output_file: str):
    """Save single check results to file"""
    results = {
        'entity_name': entity_name,
        'check_time': datetime.now().isoformat(),
        'total_matches': len(matches),
        'matches': []
    }
    
    for match in matches:
        match_data = {
            'sanction_list': match.sanction_list,
            'match_type': match.match_type,
            'confidence': match.confidence,
            'entity_type': match.entity_type,
            'source_url': match.source_url,
            'last_updated': match.last_updated.isoformat(),
            'details': match.details
        }
        results['matches'].append(match_data)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def display_bulk_summary(results: Dict[str, List[SanctionMatch]]):
    """Display summary of bulk check results"""
    total_entities = len(results)
    entities_with_matches = sum(1 for matches in results.values() if matches)
    total_matches = sum(len(matches) for matches in results.values())
    
    print("\nBulk Check Summary:")
    print("=" * 30)
    print(f"Total Entities: {total_entities}")
    print(f"Entities with Matches: {entities_with_matches}")
    print(f"Total Matches: {total_matches}")
    
    if total_entities > 0:
        match_rate = (entities_with_matches / total_entities) * 100
        print(f"Match Rate: {match_rate:.1f}%")
    
    # Count by sanction list
    if total_matches > 0:
        sanction_counts = {}
        for matches in results.values():
            for match in matches:
                sanction_list = match.sanction_list
                sanction_counts[sanction_list] = sanction_counts.get(sanction_list, 0) + 1
        
        print("\nMatches by Sanction List:")
        for sanction_list, count in sorted(sanction_counts.items()):
            print(f"  {sanction_list}: {count}")

if __name__ == "__main__":
    main() 