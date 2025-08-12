#!/bin/bash

# Quick Start Script for Comprehensive Sanction Checker
# This script will install dependencies and test the installation

echo "🚢 Royal Sanction Watch - Quick Start"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies. Please check the error messages above."
    exit 1
fi

    echo "✅ Dependencies installed successfully!"

    # Setup environment file
    echo ""
    echo "🔧 Setting up configuration..."
    if [ ! -f .env ]; then
        if [ -f env_example.txt ]; then
            cp env_example.txt .env
            echo "✅ Created .env file from template"
            echo "   Please edit .env file to add your OpenSanctions API key"
            echo "   Get your API key from: https://www.opensanctions.org/api/"
        else
            echo "⚠️  env_example.txt not found, skipping .env setup"
        fi
    else
        echo "✅ .env file already exists"
    fi

    # Test installation
    echo ""
    echo "🧪 Testing installation..."
    python3 test_installation.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "You can now run the application using:"
    echo "  python3 main.py gui     # GUI interface"
    echo "  python3 main.py web     # Web interface"
    echo "  python3 main.py cli     # Command line interface"
    echo ""
    echo "For help, run:"
    echo "  python3 main.py --help"
else
    echo ""
    echo "❌ Installation test failed. Please check the error messages above."
    exit 1
fi 