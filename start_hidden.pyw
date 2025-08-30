#!/usr/bin/env python3
"""
Direct launcher for Keyword Automator - starts minimized
This script runs the main application directly without creating subprocess chains
"""
import sys
import os

# Set up environment before any imports
script_dir = os.path.abspath(os.path.dirname(__file__))
os.chdir(script_dir)

# Add paths to ensure imports work
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

src_dir = os.path.join(script_dir, 'src')
if os.path.isdir(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import and run main directly - no subprocess calls
import main as main_module

# Set up arguments for minimized start
sys.argv = [sys.argv[0], '--minimized']

# Add any additional arguments passed to this script
if len(sys.argv) > 1:
    sys.argv.extend(sys.argv[1:])

# Run directly in this process
if __name__ == "__main__":
    exit_code = main_module.main()
    sys.exit(exit_code or 0)
