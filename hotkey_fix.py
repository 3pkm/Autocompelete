# filepath: d:\Autocompelete\hotkey_fix.py
"""
This file fixes the hotkey listener issue in the UI module.
It will replace the problematic hotkey_thread_func with a corrected version.
"""
import threading
import time

def setup_fixed_hotkey_listener(app, config, stop_event):
    """
    Sets up a properly working hotkey listener that doesn't cause the
    'AbstractListener.wait() takes 1 positional argument but 2 were given' error
    """
    try:
        from pynput import keyboard
        
        def on_activate():
            print("Hotkey activated")
            app.show_input()
        
        hotkeys = {config['hotkey']: on_activate}
        
        def hotkey_thread_func():
            with keyboard.GlobalHotKeys(hotkeys) as listener:
                print(f"Hotkey listener started for {config['hotkey']}")
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
