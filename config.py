import json
import os

CONFIG_FILE = 'scripts/config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
            # Handle migration from old config format to new format
            if 'global_hotkey' not in config and 'hotkey' in config:
                config['global_hotkey'] = config.pop('hotkey')
            
            # Migrate old mappings format to new format that includes hotkeys
            if 'mappings' in config:
                for keyword, value in list(config['mappings'].items()):
                    # If the mapping is a string (old format), convert to new format
                    if isinstance(value, str):
                        config['mappings'][keyword] = {
                            'command': value,
                            'hotkey': None,  # No hotkey assigned by default
                            'is_script': False
                        }
            
            return config
    else:
        default_config = {
            'global_hotkey': '<ctrl>+<alt>+k',
            'mappings': {}
        }
        save_config(default_config)
        return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)