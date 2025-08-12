# Installation Guide

This guide provides detailed instructions for installing the Royal Sanction Watch on different operating systems.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection (for downloading dependencies and sanction data)

## Quick Installation (Linux/macOS)

1. **Download the application:**
   ```bash
   # If you have git installed
   git clone <repository-url>
   cd royal-sanction-watch
   
   # Or download and extract the ZIP file
   # Then navigate to the extracted directory
   ```

2. **Run the quick start script:**
   ```bash
   ./quick_start.sh
   ```

   This script will:
   - Check Python and pip installation
   - Install all required dependencies
   - Test the installation
   - Provide usage instructions

## Manual Installation

### Step 1: Verify Python Installation

Check if Python 3.8+ is installed:
```bash
python3 --version
# or
python --version
```

If Python is not installed, install it from [python.org](https://www.python.org/downloads/).

### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Or install individually if needed:
pip install requests pandas openpyxl beautifulsoup4 lxml Pillow
pip install fake-useragent urllib3 streamlit plotly numpy
```

### Step 3: Test Installation

```bash
python3 test_installation.py
```

### Step 4: Run the Application

```bash
# GUI interface
python3 main.py gui

# Web interface
python3 main.py web

# Command line interface
python3 main.py cli --help
```

## Operating System Specific Instructions

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-tk

# Install additional dependencies
sudo apt install python3-dev build-essential

# Install the application
cd royal-sanction-watch
pip3 install -r requirements.txt
```

### Linux (CentOS/RHEL/Fedora)

```bash
# Install Python and pip
sudo yum install python3 python3-pip python3-tkinter
# or for newer versions:
sudo dnf install python3 python3-pip python3-tkinter

# Install the application
cd royal-sanction-watch
pip3 install -r requirements.txt
```

### macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python

# Install the application
cd royal-sanction-watch
pip3 install -r requirements.txt
```

### Windows

1. **Install Python:**
   - Download Python from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Check "Install pip"

2. **Open Command Prompt or PowerShell:**
   ```cmd
   # Navigate to the application directory
   cd path\to\royal-sanction-watch

   # Install dependencies
   pip install -r requirements.txt

   # Test installation
   python test_installation.py

   # Run the application
   python main.py gui
   ```

## Virtual Environment (Recommended)

It's recommended to use a virtual environment to avoid conflicts with other Python packages:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py gui

# Deactivate when done
deactivate
```

## Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

#### Tkinter not available (Linux)
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# CentOS/RHEL
sudo yum install python3-tkinter

# Fedora
sudo dnf install python3-tkinter
```

#### Permission errors
```bash
# Make scripts executable
chmod +x main.py
chmod +x quick_start.sh
```

#### Network connectivity issues
- Check your internet connection
- Verify firewall settings
- Try using a different network

#### Memory issues with large files
- Use CLI interface for large bulk operations
- Process files in smaller batches
- Close other applications to free memory

### Getting Help

If you encounter issues:

1. Run the test script: `python3 test_installation.py`
2. Check the troubleshooting section in README.md
3. Verify all dependencies are installed: `pip list`
4. Check Python version: `python3 --version`

## Verification

After installation, verify everything works:

```bash
# Test basic functionality
python3 test_installation.py

# Test single entity check
python3 main.py cli check "TEST_VESSEL" --type vessel

# Test cache operations
python3 main.py cli cache status

# Test connections
python3 main.py cli test
```

## Next Steps

Once installation is complete:

1. **First Run:** Start with the GUI interface: `python3 main.py gui`
2. **Explore Features:** Try single entity checks and bulk operations
3. **Configure Settings:** Adjust cache duration and similarity thresholds
4. **Test with Real Data:** Use your own vessel/person/company lists
5. **Automate:** Use CLI for batch processing and automation

## Support

For additional support:
- Check the README.md file
- Review the help documentation in the web interface
- Open an issue on the project repository 