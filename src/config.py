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

def get_config_file_path():
    """Get the correct config file path, using a consistent location for executables"""
    # For PyInstaller executables, use a fixed location next to the exe
    if getattr(sys, 'frozen', False):
        # We're running from a PyInstaller bundle
        if hasattr(sys, '_MEIPASS'):
            # Directory-based build - store config next to the executable
            exe_dir = os.path.dirname(sys.executable)
            config_file = os.path.join(exe_dir, 'config.json')
        else:
            # Fallback for onefile build
            exe_dir = os.path.dirname(sys.executable)
            config_file = os.path.join(exe_dir, 'config.json')
        return config_file
    else:
        # For development, check if assets/config.json exists first
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_config = os.path.join(script_dir, 'assets', 'config.json')
        
        if os.path.exists(assets_config):
            return assets_config
        
        # Fall back to user config directory
        ensure_config_dir()
        return CONFIG_FILE

def load_config():
    """Load configuration with better error handling"""
    config_file = get_config_file_path()
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
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
                    'has_seen_welcome': False,
                    'wizard_completed': False
                }
                
                for key, value in default_values.items():
                    if key not in config:
                        config[key] = value
                
                logger.info(f"Configuration loaded successfully from: {config_file}")
                return config
        else:
            default_config = {
                'global_hotkey': '<ctrl>+<alt>+k',
                'startup_minimized': False,
                'launch_at_startup': True,
                'theme': 'system',
                'has_seen_welcome': False,
                'wizard_completed': False,
                'mappings': {}
            }
            save_config(default_config)
            logger.info(f"Created default configuration at: {config_file}")
            return default_config
            
    except Exception as e:
        logger.error(f"Error loading configuration from {config_file}: {e}")
        return {'global_hotkey': '<ctrl>+<alt>+k', 'mappings': {}, 'has_seen_welcome': False, 'wizard_completed': False}

def save_config(config):
    """Save configuration with better error handling"""
    config_file = get_config_file_path()
    
    # Ensure the directory exists
    config_dir = os.path.dirname(config_file)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Configuration saved successfully to: {config_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration to {config_file}: {e}")
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