import json
import os
import appdirs
import logging
import sys

APP_NAME = "KeywordAutomator"
APP_AUTHOR = "Prakhar Jaiswal"
CONFIG_DIR = appdirs.user_config_dir(APP_NAME, APP_AUTHOR)
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
LOG_FILE = os.path.join(CONFIG_DIR, 'app.log')

def setup_logging():
    """Setup logging to file and console"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def ensure_config_dir():
    """Ensure the configuration directory exists"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        logger.info(f"Created configuration directory: {CONFIG_DIR}")

def load_config():
    """Load configuration with better error handling"""
    ensure_config_dir()
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                
                if 'global_hotkey' not in config and 'hotkey' in config:
                    config['global_hotkey'] = config.pop('hotkey')

                if 'mappings' in config:
                    for keyword, value in list(config['mappings'].items()):

                        if isinstance(value, str):
                            config['mappings'][keyword] = {
                                'command': value,
                                'hotkey': None,
                                'is_script': False,
                                'run_as_admin': False,
                                'show_window': True
                            }

                        elif isinstance(value, dict):
                            if 'run_as_admin' not in value:
                                value['run_as_admin'] = False
                            if 'show_window' not in value:
                                value['show_window'] = True
                
                default_values = {
                    'startup_minimized': False,
                    'launch_at_startup': True,
                    'theme': 'system',
                    'has_seen_welcome': False
                }
                
                for key, value in default_values.items():
                    if key not in config:
                        config[key] = value
                
                logger.info("Configuration loaded successfully")
                return config
        else:
            default_config = {
                'global_hotkey': '<ctrl>+<alt>+k',
                'startup_minimized': False,
                'launch_at_startup': True,
                'theme': 'system',
                'has_seen_welcome': False,
                'mappings': {}
            }
            save_config(default_config)
            logger.info("Created default configuration")
            return default_config
            
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {'global_hotkey': '<ctrl>+<alt>+k', 'mappings': {}}

def save_config(config):
    """Save configuration with better error handling"""
    ensure_config_dir()
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info("Configuration saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False

def set_launch_at_startup(enable=True):
    """Configure the application to launch at system startup"""
    if sys.platform == 'win32':
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    if getattr(sys, 'frozen', False):
                        app_path = f'"{sys.executable}" --minimized'
                    else:
                        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        hidden_script = os.path.join(script_dir, "start_hidden.pyw")
                        pythonw_exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                        app_path = f'"{pythonw_exe}" "{hidden_script}"'
                    
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, app_path)
                    logger.info(f"Added {APP_NAME} to startup registry with path: {app_path}")
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                        logger.info(f"Removed {APP_NAME} from startup registry")
                    except FileNotFoundError:
                        pass
            return True
        except Exception as e:
            logger.error(f"Error setting launch at startup: {e}")
            return False
    else:
        logger.warning("Launch at startup not implemented for this platform")
        return False

config = None