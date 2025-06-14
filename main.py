import os
import sys
import logging
import traceback
import argparse

from src import hotkey

def setup_basic_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger(__name__)
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error",
            f"An unexpected error occurred:\n\n{exc_value}\n\n"
            f"Please check the log file for details."
        )
        root.destroy()
    except:
        print(f"ERROR: {exc_value}", file=sys.stderr)
        print(f"See log file for details.", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Keyword Automator - A productivity tool")
    parser.add_argument('--minimized', action='store_true', help='Start minimized to system tray')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Keyword Automator v1.0")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Command line arguments: {sys.argv}")
    
    sys.excepthook = handle_exception
    
    if not getattr(sys, 'frozen', False):

        current_dir = os.path.abspath(os.path.dirname(__file__))

        src_dir = os.path.join(current_dir, 'src')
        if os.path.isdir(src_dir) and src_dir not in sys.path:
            sys.path.insert(0, src_dir)
            logger.info(f"Added {src_dir} to Python path")
    
    try:
        try:
            from src import config as config_module
            logger.info("Successfully imported config module from src")
        except ImportError as e1:
            logger.error(f"Failed to import config from src: {e1}")
              
            try:
                
                from . import config as config_module
                logger.info("Successfully imported config module with relative import")
            except ImportError as e2:
                logger.error(f"Failed to import config with relative import: {e2}")
                
                try:
                    current_dir = os.path.abspath(os.path.dirname(__file__))
                    src_dir = os.path.join(current_dir, 'src')
                    if src_dir not in sys.path:
                        sys.path.insert(0, src_dir)
                    from src import config as config_module
                    logger.info("Successfully imported config after path adjustment")
                except ImportError as e3:
                    logger.error(f"All import attempts failed: {e3}")
                    messagebox.showerror(
                        "Critical Error", 
                        "Failed to import essential modules. The application cannot start."
                    )
                    return 1
        try:
            from src import ui_enhanced, tray_fix
            logger.info("Successfully imported required modules from src package")
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                import src.ui_enhanced as ui_enhanced
                import src.hotkey as hotkey
                import src.tray_fix as tray_fix
                logger.info("Successfully imported required modules using absolute paths")
            except ImportError as e2:
                logger.error(f"Failed to import required modules using absolute paths: {e2}")
                try:
                    import tkinter as tk
                    from tkinter import messagebox
                    messagebox.showerror(
                        "Import Error", 
                        "Failed to import required modules. The application may not function correctly."
                    )
                except:
                    print("Failed to import required modules. The application may not function correctly.")
        
        config_module.setup_logging()
        logger = logging.getLogger(__name__)
        
        current_app_config_data = config_module.load_config()
        if current_app_config_data is None:
            logger.error("Failed to load configuration in main.py. Using default config.")
            current_app_config_data = {
                'global_hotkey': '<ctrl>+<alt>+k',
                'startup_minimized': False,
                'mappings': {}
            }
        
        logger.info("Creating application instance")
        app = ui_enhanced.KeywordAutomatorApp()
        
        if args.minimized or current_app_config_data.get('startup_minimized', False):
            logger.info("Application will start minimized to system tray")
            app.tk_root.after(500, app.minimize_to_tray)
        
        logger.info("Starting application main loop")
        app.run()
        
        logger.info("Keyword Automator exited normally")
        return 0
    
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Startup Error",
                f"Failed to start Keyword Automator:\n\n{e}\n\n"
                f"Please check the log file for details."
            )
            root.destroy()
        except:
            print(f"ERROR: {e}", file=sys.stderr)
        
        return 1

if __name__ == "__main__":
    setup_basic_logging()
    
    sys.exit(main())
