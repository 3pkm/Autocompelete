import os
import sys
import subprocess
import traceback
import argparse
import main as main_module

def run_app():
    try:
        current_dir = os.path.abspath(os.path.dirname(__file__))
        
        src_dir = os.path.join(current_dir, 'src')
        if os.path.isdir(src_dir):
            sys.path.insert(0, src_dir)
        
        sys.path.insert(0, current_dir)
        
        

        parser = argparse.ArgumentParser(description="KeywordAutomator Launcher")
        parser.add_argument('--minimized', action='store_true', help='Start minimized to system tray')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode')
        args, unknown = parser.parse_known_args()
        
        sys.argv = [sys.argv[0]] + unknown
        if args.minimized:
            sys.argv.append('--minimized')
        if args.debug:
            sys.argv.append('--debug')
        
        main_module.main()
    except Exception as e:
        print(f"Error in run.py: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_app()
