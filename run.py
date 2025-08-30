#!/usr/bin/env python3
"""
Direct runner for Keyword Automator
This script runs the main application directly without creating subprocess chains
"""
import os
import sys
import traceback
import argparse

# Set up environment before any imports
current_dir = os.path.abspath(os.path.dirname(__file__))
src_dir = os.path.join(current_dir, 'src')

if os.path.isdir(src_dir):
    sys.path.insert(0, src_dir)

sys.path.insert(0, current_dir)

def run_app():
    """Run the application directly in this process"""
    try:
        # Import main module
        import main as main_module
        
        # Parse arguments
        parser = argparse.ArgumentParser(description="KeywordAutomator Direct Launcher")
        parser.add_argument('--minimized', action='store_true', help='Start minimized to system tray')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode')
        args, unknown = parser.parse_known_args()
        
        # Set up sys.argv for main module
        sys.argv = [sys.argv[0]] + unknown
        if args.minimized:
            sys.argv.append('--minimized')
        if args.debug:
            sys.argv.append('--debug')
        
        # Run main directly - no subprocess calls
        return main_module.main()
        
    except Exception as e:
        print(f"Error in run.py: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = run_app()
    sys.exit(exit_code or 0)
