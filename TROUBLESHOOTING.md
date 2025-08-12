# Royal Sanction Watch - Troubleshooting Guide

## Common Issues and Solutions

### 🔑 OpenSanctions API Authentication Issues

**Problem:** `401 Client Error: Unauthorized` or `OpenSanctions API authentication failed`

**Solution:**
1. Get your free API key from: https://www.opensanctions.org/api/
2. Edit the `.env` file and replace `your_api_key_here` with your actual key
3. Or run the setup script: `python3 setup_api_key.py`

**Note:** The application works without an API key but with limited functionality (legacy sources only).

### 🌐 Network Connection Issues

**Problem:** `Failed to fetch OFAC data: 404 Client Error: Not Found`

**Solution:** This is normal - the application gracefully falls back to other sources. The OFAC vessel list URL changes periodically.

### 📊 Data Parsing Issues

**Problem:** `XML parsing failed for UN data`

**Solution:** This is handled automatically - the application continues with other sources. UN data format changes frequently.

### 🐍 Python Module Issues

**Problem:** `ModuleNotFoundError: No module named 'pandas'`

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 🖥️ GUI Launch Issues

**Problem:** `Error launching gui interface: expected str, bytes or os.PathLike object, not NoneType`

**Solution:** This was a bug that has been fixed. Make sure you're using the latest version.

## Performance Tips

### 🚀 Faster Searches
- Configure your OpenSanctions API key for best performance
- Use the CLI for bulk operations
- The application caches data to reduce API calls

### 📁 File Management
- Reports are saved in the current directory
- Cache files are stored in the `cache/` directory
- Logs are stored in the `logs/` directory

## Getting Help

### 📋 Check Installation
```bash
python3 test_installation.py
```

### 🔧 Test API Connection
```bash
python3 test_opensanctions.py
```

### 📖 View Logs
Check the `logs/` directory for detailed error information.

### 🌐 Online Resources
- OpenSanctions API: https://www.opensanctions.org/api/
- Documentation: https://www.opensanctions.org/docs/

## Application Status

### ✅ Working Features
- ✅ GUI interface
- ✅ Web interface (Streamlit)
- ✅ CLI interface
- ✅ OpenSanctions API integration
- ✅ OFAC data fetching (17,746+ records)
- ✅ Error handling and graceful fallbacks
- ✅ Configuration management
- ✅ Report generation

### ⚠️ Known Limitations
- UN data parsing may fail due to format changes
- Some legacy sources may have intermittent availability
- OpenSanctions API requires authentication for full functionality

### 🔄 Fallback Strategy
The application uses a multi-tier approach:
1. **Primary:** OpenSanctions API (requires key)
2. **Secondary:** OFAC data (direct download)
3. **Tertiary:** Other sources (UK, EU, UN)
4. **Graceful degradation:** Continue with available sources

## Quick Fixes

### Reset Configuration
```bash
cp env_example.txt .env
```

### Clear Cache
```bash
rm -rf cache/*
```

### Reinstall Dependencies
```bash
pip install -r requirements.txt --force-reinstall
```

### Test Everything
```bash
python3 test_installation.py && python3 test_opensanctions.py
``` 