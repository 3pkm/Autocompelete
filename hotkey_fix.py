# filepath: d:\Autocompelete\hotkey_fix_new.py
"""
This file fixes the hotkey listener issue in the UI module.
It will replace the problematic hotkey_thread_func with a corrected version.
"""
import threading
import time  # Ensure time is imported
import core  # Import core for executing commands

def setup_fixed_hotkey_listener(app, config, stop_event):
    """
    Sets up a properly working hotkey listener that doesn't cause the
    'AbstractListener.wait() takes 1 positional argument but 2 were given' error
    
    Now supports both the old 'hotkey' and new 'global_hotkey' configuration keys,
    as well as multiple per-keyword hotkeys.
    """
    try:
        from pynput import keyboard
        
        # Function to show the input dialog when global hotkey is pressed
        def on_activate():
            print("Global hotkey activated")
            app.show_input()
        
        # Start with an empty hotkeys dictionary
        hotkeys = {}
        
        # Add the global hotkey (check for both old and new config keys)
        if 'global_hotkey' in config:
            global_hotkey = config['global_hotkey']
            hotkeys[global_hotkey] = on_activate
        elif 'hotkey' in config:
            # For backward compatibility
            global_hotkey = config['hotkey']
            hotkeys[global_hotkey] = on_activate
        else:
            # Default if neither is found
            global_hotkey = '<ctrl>+<alt>+k'
            hotkeys[global_hotkey] = on_activate
            
        # Add per-keyword hotkeys if available
        if 'mappings' in config:
            for keyword, mapping_data in config['mappings'].items():
                if isinstance(mapping_data, dict) and mapping_data.get('hotkey'):
                    keyword_hotkey = mapping_data['hotkey']
                    
                    # Create a closure to preserve the keyword value
                    def create_hotkey_handler(kw):
                        def handler():
                            print(f"Hotkey activated for '{kw}'")
                            core.execute_command(kw, config['mappings'])
                        return handler
                    
                    # Add the hotkey
                    hotkeys[keyword_hotkey] = create_hotkey_handler(keyword)
        
        # Print all configured hotkeys
        print("Active hotkeys:")
        for hotkey in hotkeys:
            print(f"  {hotkey}")
        
        def hotkey_thread_func():
            with keyboard.GlobalHotKeys(hotkeys) as listener:
                print(f"Hotkey listener started with {len(hotkeys)} hotkeys")
                try:
                    # This is the key fix - we call wait() without parameters
                    # and use a separate sleep call to prevent high CPU usage
                    while not stop_event.is_set():
                        listener.wait()  # No parameters here
                        time.sleep(0.1)  # Sleep to reduce CPU usage
                except Exception as e:
                    print(f"Error in hotkey listener: {e}")
        
        hotkey_thread = threading.Thread(target=hotkey_thread_func)
        hotkey_thread.daemon = True
        hotkey_thread.start()
        return hotkey_thread
    except ImportError:
        print("pynput module not available - hotkey functionality disabled")
        return None
