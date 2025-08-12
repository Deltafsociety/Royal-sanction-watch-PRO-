#!/usr/bin/env python3
"""
Main launcher for Comprehensive Sanction Checker
Allows users to choose between different interfaces
"""

import sys
import os
import argparse

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(
        description="Royal Sanction Watch - Main Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available interfaces:
  gui      - Tkinter GUI application
  web      - Streamlit web application
  cli      - Command line interface

Examples:
  python main.py gui
  python main.py web
  python main.py cli check "VESSEL_NAME"
        """
    )
    
    parser.add_argument(
        'interface',
        choices=['gui', 'web', 'cli'],
        help='Interface to use'
    )
    
    parser.add_argument(
        'args',
        nargs=argparse.REMAINDER,
        help='Arguments to pass to the selected interface'
    )
    
    args = parser.parse_args()
    
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        if args.interface == 'gui':
            launch_gui()
        elif args.interface == 'web':
            launch_web()
        elif args.interface == 'cli':
            launch_cli(args.args)
    
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        print("Please install required packages: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching {args.interface} interface: {e}")
        sys.exit(1)

def launch_gui():
    """Launch the GUI application"""
    try:
        import tkinter as tk
        from gui_app import SanctionCheckerGUI
        
        print("Launching GUI application...")
        root = tk.Tk()
        app = SanctionCheckerGUI(root)
        root.mainloop()
    
    except ImportError as e:
        print(f"GUI dependencies not available: {e}")
        print("Please install tkinter or use a different interface")
        sys.exit(1)

def launch_web():
    """Launch the Streamlit web application"""
    try:
        import streamlit
        import subprocess
        
        print("Launching Streamlit web application...")
        print("The application will open in your default web browser.")
        print("Press Ctrl+C to stop the server.")
        
        # Launch streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    
    except ImportError as e:
        print(f"Streamlit not available: {e}")
        print("Please install streamlit: pip install streamlit")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStreamlit server stopped.")
    except Exception as e:
        print(f"Error launching Streamlit: {e}")
        sys.exit(1)

def launch_cli(cli_args):
    """Launch the CLI application"""
    try:
        from cli_app import main as cli_main
        
        # Set sys.argv to pass arguments to CLI
        original_argv = sys.argv
        sys.argv = ['cli_app.py'] + cli_args
        
        cli_main()
        
        # Restore original argv
        sys.argv = original_argv
    
    except ImportError as e:
        print(f"CLI dependencies not available: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 