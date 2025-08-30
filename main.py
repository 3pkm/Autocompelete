import os
import sys
import logging
import traceback
import argparse
import tempfile

from src import hotkey

# Platform-specific imports for file locking
if sys.platform == 'win32':
    import msvcrt
else:
    import fcntl

# Global lock file for singleton behavior
LOCK_FILE = None

def setup_basic_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def acquire_lock():
    """Acquire a file lock to prevent multiple instances"""
    global LOCK_FILE
    try:
        # Create lock file in temp directory
        lock_path = os.path.join(tempfile.gettempdir(), 'keywordautomator.lock')
        LOCK_FILE = open(lock_path, 'w')
        
        if sys.platform == 'win32':
            # Windows file locking
            try:
                msvcrt.locking(LOCK_FILE.fileno(), msvcrt.LK_NBLCK, 1)
                LOCK_FILE.write(str(os.getpid()))
                LOCK_FILE.flush()
                return True
            except IOError:
                LOCK_FILE.close()
                return False
        else:
            # Unix file locking
            try:
                fcntl.flock(LOCK_FILE.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                LOCK_FILE.write(str(os.getpid()))
                LOCK_FILE.flush()
                return True
            except IOError:
                LOCK_FILE.close()
                return False
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error acquiring lock: {e}")
        return True  # Allow startup if lock fails

def release_lock():
    """Release the file lock"""
    global LOCK_FILE
    if LOCK_FILE:
        try:
            if sys.platform == 'win32':
                msvcrt.locking(LOCK_FILE.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(LOCK_FILE.fileno(), fcntl.LOCK_UN)
            LOCK_FILE.close()
        except:
            pass

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

def safe_minimize_to_tray(app):
    """Safely minimize to tray with error handling"""
    try:
        logger = logging.getLogger(__name__)
        logger.info("Attempting to minimize to system tray...")
        app.minimize_to_tray()
        logger.info("Successfully minimized to system tray")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to minimize to tray during startup: {e}")
        # Don't show error dialog during startup, just log it
        print(f"Note: Could not minimize to system tray: {e}")

def main():
    parser = argparse.ArgumentParser(description="Keyword Automator - A productivity tool")
    parser.add_argument('--minimized', action='store_true', help='Start minimized to system tray')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--direct', action='store_true', help='Direct launch mode (internal use)')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check for existing instance (singleton behavior)
    if not acquire_lock():
        logger = logging.getLogger(__name__)
        logger.info("Another instance of KeywordAutomator is already running. Exiting.")
        
        # In direct launch mode, be more aggressive about showing the existing instance
        if args.direct:
            logger.info("Direct launch mode detected - attempting to activate existing instance")
        
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            
            if args.direct:
                messagebox.showinfo(
                    "Already Running",
                    "KeywordAutomator is already running.\n\n"
                    "The existing instance has been activated.\n"
                    "Check your system tray for the application icon."
                )
            else:
                messagebox.showinfo(
                    "Already Running",
                    "KeywordAutomator is already running.\n\n"
                    "Check your system tray for the application icon."
                )
            root.destroy()
        except:
            print("KeywordAutomator is already running. Check your system tray.")
        return 0
        
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
        
        # Only start minimized if explicitly requested via command line
        # Don't automatically minimize based on config to avoid blank screen
        start_minimized = args.minimized
        app = ui_enhanced.KeywordAutomatorApp(start_minimized=start_minimized)
        
        if start_minimized:
            logger.info("Application starting minimized to system tray (command line request)")
        else:
            logger.info("Application starting normally - window will be visible")
        
        logger.info("Starting application main loop")
        app.run()
        
        logger.info("Keyword Automator exited normally")
        release_lock()
        return 0
    
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        release_lock()
        
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
    
    finally:
        # Ensure lock is always released
        release_lock()

if __name__ == "__main__":
    setup_basic_logging()
    
    sys.exit(main())
