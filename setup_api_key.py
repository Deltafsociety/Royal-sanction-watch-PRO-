#!/usr/bin/env python3
"""
Royal Sanction Watch - API Key Setup Script

This script helps you set up your OpenSanctions API key for enhanced functionality.
"""

import os
import sys
from pathlib import Path

def main():
    print("🔑 Royal Sanction Watch - API Key Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found. Creating from template...")
        example_file = Path("env_example.txt")
        if example_file.exists():
            os.system("cp env_example.txt .env")
            print("✅ Created .env file from template")
        else:
            print("❌ env_example.txt not found. Please create .env file manually.")
            return
    
    # Read current API key
    api_key = None
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("OPENSANCTIONS_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return
    
    if api_key and api_key != "your_api_key_here":
        print(f"✅ API key already configured: {api_key[:10]}...")
        print("You can update it by editing the .env file")
    else:
        print("❌ No API key configured")
        print("\nTo get your API key:")
        print("1. Visit: https://www.opensanctions.org/api/")
        print("2. Sign up for a free account")
        print("3. Get your API key")
        print("4. Edit the .env file and replace 'your_api_key_here' with your actual key")
        
        # Offer to open the URL
        try:
            import webbrowser
            open_browser = input("\nWould you like to open the API registration page? (y/n): ").lower()
            if open_browser == 'y':
                webbrowser.open("https://www.opensanctions.org/api/")
        except ImportError:
            pass
    
    print("\n📝 Current .env configuration:")
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if "API_KEY" in key:
                        display_value = value.strip()[:10] + "..." if len(value.strip()) > 10 else value.strip()
                    else:
                        display_value = value.strip()
                    print(f"  {key}: {display_value}")
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
    
    print("\n✅ Setup complete!")
    print("You can now run the application:")
    print("  python3 main.py gui     # GUI interface")
    print("  python3 main.py web     # Web interface")
    print("  python3 main.py cli     # Command line interface")

if __name__ == "__main__":
    main() 