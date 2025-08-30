#!/usr/bin/env python3
"""
Direct launcher for Keyword Automator that avoids process chains.
This script launches the main application directly without intermediate processes.
"""

import os
import sys
import logging

def setup_environment():
    """Set up the Python environment and paths"""
    # Get the directory where this script is located
    script_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Add the script directory to Python path
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Add src directory to Python path
    src_dir = os.path.join(script_dir, 'src')
    if os.path.isdir(src_dir) and src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    # Change to the script directory to ensure relative paths work
    os.chdir(script_dir)

def launch_application(minimized=False, debug=False):
    """Launch the main application directly"""
    try:
        # Setup environment first
        setup_environment()
        
        # Import main module after path setup
        import main as main_module
        
        # Prepare command line arguments
        original_argv = sys.argv.copy()
        sys.argv = [sys.argv[0]]  # Reset argv to just script name
        
        if minimized:
            sys.argv.append('--minimized')
        if debug:
            sys.argv.append('--debug')
        
        sys.argv.append('--direct')  # Mark as direct launch
        
        # Launch the main application
        exit_code = main_module.main()
        
        # Restore original argv
        sys.argv = original_argv
        
        return exit_code or 0
        
    except Exception as e:
        print(f"Error launching application: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Direct Keyword Automator Launcher")
    parser.add_argument('--minimized', action='store_true', 
                       help='Start minimized to system tray')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set up basic logging for the launcher
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    exit_code = launch_application(
        minimized=args.minimized,
        debug=args.debug
    )
    
    sys.exit(exit_code)
