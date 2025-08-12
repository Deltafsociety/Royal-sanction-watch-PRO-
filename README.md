# Royal Sanction Watch

A powerful application to check vessels, persons, and companies against OFAC, UK, EU, and UN sanctions lists. Supports both single entity checks and bulk processing with multiple interface options.

## Features

- **OpenSanctions API Integration**: Primary data source using the comprehensive OpenSanctions API
- **Multi-Source Checking**: Check against OpenSanctions, OFAC, UK, EU, and UN sanctions lists
- **Multiple Interfaces**: GUI (Tkinter), Web (Streamlit), and CLI options
- **Bulk Processing**: Process large lists of entities efficiently using OpenSanctions matching API
- **Smart Matching**: Advanced fuzzy matching with confidence scores and entity type detection
- **Caching**: Intelligent caching to reduce API calls and improve performance
- **Multiple Output Formats**: Excel, CSV, and JSON report generation
- **Real-time Updates**: Automatic data refresh from official sources
- **Entity Type Detection**: Automatic detection of vessel, person, or company entities
- **API Key Management**: Secure configuration for OpenSanctions API access

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download the application:
```bash
git clone <repository-url>
cd royal-sanction-watch
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API keys (optional but recommended):
```bash
# Copy the example environment file
cp env_example.txt .env

# Edit .env file and add your OpenSanctions API key
# Get your API key from: https://www.opensanctions.org/api/
```

4. Verify installation:
```bash
python test_installation.py
```

## Usage

### Quick Start

The application provides three different interfaces:

#### 1. GUI Application (Recommended for beginners)
```bash
python main.py gui
```

#### 2. Web Application (Modern interface)
```bash
python main.py web
```

#### 3. Command Line Interface (For automation)
```bash
python main.py cli check "VESSEL_NAME"
```

### Single Entity Check

#### GUI/Web Interface
1. Launch the application
2. Enter the entity name
3. Select entity type (or leave as "auto")
4. Click "Check Entity"
5. Review results

#### CLI Interface
```bash
# Check a vessel
python main.py cli check "VESSEL_NAME" --type vessel

# Check a person
python main.py cli check "PERSON_NAME" --type person

# Check a company
python main.py cli check "COMPANY_NAME" --type company

# Auto-detect entity type
python main.py cli check "ENTITY_NAME" --type auto
```

### Bulk Entity Check

#### GUI/Web Interface
1. Go to "Bulk Check" tab
2. Upload CSV or Excel file
3. Configure column mappings
4. Start bulk check
5. Download results report

#### CLI Interface
```bash
# Check entities from CSV file
python main.py cli bulk check input.csv --name-column name --output results.xlsx

# Check entities from Excel file with type column
python main.py cli bulk check input.xlsx --name-column name --type-column type --output results.xlsx

# Generate JSON report
python main.py cli bulk check input.csv --name-column name --output results.json --format json
```

### Cache Management

#### CLI Commands
```bash
# Update all cached data
python main.py cli cache update

# Show cache status
python main.py cli cache status

# Clear all cached data
python main.py cli cache clear
```

### Connection Testing

```bash
# Test connections to all sanction sources
python main.py cli test
```

## Input File Formats

### CSV Format
```csv
name,type
VESSEL_NAME_1,vessel
PERSON_NAME_1,person
COMPANY_NAME_1,company
```

### Excel Format
| name | type |
|------|------|
| VESSEL_NAME_1 | vessel |
| PERSON_NAME_1 | person |
| COMPANY_NAME_1 | company |

## Output Formats

### Excel Report
- Multiple sheets with detailed results
- Summary statistics
- Match details with confidence scores

### CSV Report
- Single file with all results
- Comma-separated values
- Easy to import into other tools

### JSON Report
- Structured data format
- Detailed match information
- Suitable for API integration

## Supported Sanctions Lists

### OpenSanctions (Primary Source)
- **URL**: https://www.opensanctions.org/
- **API**: https://api.opensanctions.org/
- **Update Frequency**: Real-time
- **Coverage**: Comprehensive database including:
  - Sanctions lists from multiple jurisdictions
  - Politically Exposed Persons (PEPs)
  - Companies and organizations
  - Vessels and maritime entities
  - Addresses and identification documents

### OFAC (US Treasury) - Legacy Support
- **URL**: https://www.treasury.gov/ofac/downloads/
- **Update Frequency**: Daily
- **Coverage**: US sanctions against individuals, entities, and vessels

### UK Sanctions List - Legacy Support
- **URL**: https://www.gov.uk/government/publications/the-uk-sanctions-list
- **Update Frequency**: As needed
- **Coverage**: UK sanctions against individuals and entities

### EU Sanctions List - Legacy Support
- **URL**: https://www.dma.dk/
- **Update Frequency**: Regularly
- **Coverage**: EU sanctions against vessels and entities

### UN Security Council - Legacy Support
- **URL**: https://www.un.org/securitycouncil/content/un-sc-consolidated-list
- **Update Frequency**: As needed
- **Coverage**: UN sanctions against individuals and entities

## Configuration

### Cache Settings
- **Default Duration**: 24 hours
- **Location**: `./cache/` directory
- **Format**: CSV files per source

### Matching Settings
- **Similarity Threshold**: 0.7 (70%)
- **Match Types**: Exact, Partial, Fuzzy
- **Confidence Scoring**: 0.0 to 1.0

## Troubleshooting

### Common Issues

#### No Results Found
- Check spelling of entity names
- Try different variations of the name
- Verify the entity type is correct
- Ensure internet connection is available

#### Connection Errors
- Check your internet connection
- Try refreshing the cache
- Verify firewall settings
- Contact support if issues persist

#### File Upload Errors
- Ensure file format is supported (CSV, Excel)
- Check column names match expected format
- Verify file is not corrupted
- Check file size limits

#### Performance Issues
- Clear cache if it's too large
- Use CLI for large bulk operations
- Consider running during off-peak hours
- Check available system resources

### Error Messages

#### "Missing dependency"
```bash
pip install -r requirements.txt
```

#### "Cache directory not found"
```bash
python main.py cli cache update
```

#### "Column not found in file"
- Check column names in your input file
- Use `--verbose` flag for more details

## API Integration

The core `SanctionChecker` class can be imported and used in other Python applications:

```python
from sanction_checker import SanctionChecker

# Initialize checker
checker = SanctionChecker()

# Check single entity
matches = checker.check_single_entity("VESSEL_NAME", "vessel")

# Check multiple entities
entities = [
    {"name": "VESSEL_1", "type": "vessel"},
    {"name": "PERSON_1", "type": "person"}
]
results = checker.check_bulk_entities(entities)

# Generate report
report_file = checker.generate_report(results, "excel")
```

## Development

### Project Structure
```
royal-sanction-watch/
├── main.py              # Main launcher
├── sanction_checker.py  # Core checking logic
├── gui_app.py          # Tkinter GUI
├── streamlit_app.py    # Streamlit web app
├── cli_app.py          # Command line interface
├── requirements.txt    # Dependencies
├── README.md          # This file
└── cache/             # Cache directory (created automatically)
```

### Adding New Sanctions Sources

1. Update `sanction_sources` in `SanctionChecker.__init__()`
2. Add corresponding `_fetch_*_data()` method
3. Update the main checking loop in `check_single_entity()`
4. Test with the new source

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section above
- Review the help documentation in the web interface
- Open an issue on the project repository

## Disclaimer

This application is designed to assist with sanctions compliance but should not be the sole basis for compliance decisions. Always verify results against official sources and consult with legal professionals for compliance matters.

## Changelog

### Version 1.0.0
- Initial release
- Support for OFAC, UK, EU, and UN sanctions lists
- GUI, Web, and CLI interfaces
- Bulk processing capabilities
- Caching system
- Multiple output formats 