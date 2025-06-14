"""
Enhanced hotkey module with improved reliability and additional features.
This module fixes the common hotkey listener issues and adds support for
hotkey combinations and various modifier keys.
"""

import logging
import re
from pynput import keyboard # Ensure pynput.keyboard is imported

# Get logger and ensure it's properly configured
logger = logging.getLogger(__name__)
# Ensure at least one handler exists to see the logs
if not logger.handlers and not logging.getLogger().handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

# Regular expression to parse hotkey combinations with modifiers
# HOTKEY_PATTERN = re.compile(r"<([^>]+)>\\+(?:<([^>]+)>\\+)*([^<>+]+)") # Not used with GlobalHotKeys string format

class HotkeyManager:
    """Manages global hotkeys with improved reliability"""

    def __init__(self, app, config_data, stop_event): # Renamed config to config_data
        self.app = app
        self.config_data = config_data # Store the actual config dictionary
        self.stop_event = stop_event # stop_event is kept but might be unused by GlobalHotKeys
        self.listener = None
        self.is_running = False
        self.hotkeys_callbacks = {} # To store {'hotkey_string': callback_function}

    def setup_all_hotkeys(self): # Renamed from setup_global_hotkey
        """Set up all hotkeys: the global activation hotkey and individual keyword hotkeys."""
        self.hotkeys_callbacks = {} # Reset callbacks

        # 1. Set up the global activation hotkey (e.g., to show input dialog)
        global_hotkey_str = self.config_data.get('global_hotkey')
        if global_hotkey_str:
            logger.info(f"Preparing global activation hotkey: {global_hotkey_str}")

            def on_global_hotkey_activated():
                logger.info(f"Global activation hotkey '{global_hotkey_str}' activated.")
                if self.app and hasattr(self.app, 'show_input') and callable(self.app.show_input):
                    if hasattr(self.app, 'tk_root') and hasattr(self.app.tk_root, 'after'):
                        self.app.tk_root.after(0, self.app.show_input)
                    else:
                        logger.warning("tk_root not available for .after(), calling show_input directly.")
                        self.app.show_input()
                else:
                    logger.error("App or app.show_input is not configured correctly for global hotkey.")
            
            self.hotkeys_callbacks[global_hotkey_str] = on_global_hotkey_activated
            logger.debug(f"Global activation hotkey callback prepared for: {global_hotkey_str}")
        else:
            logger.warning("Global activation hotkey is not defined in configuration.")

        # 2. Set up individual hotkeys for keyword mappings
        mappings = self.config_data.get('mappings', {})
        for keyword, details in mappings.items():
            if isinstance(details, dict):
                keyword_hotkey_str = details.get('hotkey')
                # Ensure hotkey is valid and not the placeholder "None" or empty
                if keyword_hotkey_str and keyword_hotkey_str.lower() != 'none' and keyword_hotkey_str.strip():
                    logger.info(f"Preparing hotkey '{keyword_hotkey_str}' for keyword '{keyword}'.")

                    # Need to use a closure to correctly capture the keyword for each callback
                    def create_keyword_callback(kw, khs):
                        def callback():
                            logger.info(f"Keyword hotkey '{khs}' for '{kw}' activated.")
                            if self.app and hasattr(self.app, 'execute_keyword') and callable(self.app.execute_keyword):
                                if hasattr(self.app, 'tk_root') and hasattr(self.app.tk_root, 'after'):
                                    # Schedule GUI update on the main thread
                                    self.app.tk_root.after(0, lambda k=kw: self.app.execute_keyword(k))
                                else:
                                    logger.warning(f"tk_root not available for .after(), calling execute_keyword for '{kw}' directly.")
                                    self.app.execute_keyword(kw)
                            else:
                                logger.error(f"App or app.execute_keyword for '{kw}' is not configured correctly.")
                        return callback

                    # Ensure no conflict with global hotkey or other keyword hotkeys
                    if keyword_hotkey_str in self.hotkeys_callbacks:
                        logger.warning(f"Hotkey conflict: '{keyword_hotkey_str}' for keyword '{keyword}' is already assigned. Skipping.")
                    else:
                        self.hotkeys_callbacks[keyword_hotkey_str] = create_keyword_callback(keyword, keyword_hotkey_str)
                        logger.debug(f"Callback for keyword hotkey '{keyword_hotkey_str}' prepared.")
        
        if not self.hotkeys_callbacks:
            logger.warning("No hotkeys (global or keyword-specific) were successfully prepared.")
            return False
        
        logger.info(f"Total hotkeys prepared: {len(self.hotkeys_callbacks)}. Keys: {list(self.hotkeys_callbacks.keys())}")
        return True

    def start_listener(self):
        """Start the hotkey listener for all configured hotkeys."""
        if not self.setup_all_hotkeys(): # Changed to setup_all_hotkeys
            logger.error("Failed to set up hotkeys. Listener not starting.")
            return None

        if not self.hotkeys_callbacks:
            logger.warning("No hotkeys configured. Listener not starting.")
            return None

        try:
            self.listener = keyboard.GlobalHotKeys(self.hotkeys_callbacks)
            self.listener.start() # Start the thread
            self.is_running = True
            logger.info(f"Global hotkey listener thread object created and started: {self.listener}")
            return self.listener # Return the thread object itself

        except Exception as e:
            logger.error(f"Error starting hotkey listener: {e}", exc_info=True)
            self.is_running = False
            if self.listener:
                try:
                    self.listener.stop()
                except Exception as stop_exc:
                    logger.error(f"Error trying to stop listener during startup failure: {stop_exc}")
            self.listener = None
            return None

    def stop_listener(self):
        """Stop the hotkey listener."""
        if self.listener and self.is_running:
            try:
                logger.info("Stopping hotkey listener...")
                self.listener.stop()
                self.is_running = False
                self.listener = None
                logger.info("Hotkey listener stopped.")
            except Exception as e:
                logger.error(f"Error stopping hotkey listener: {e}", exc_info=True)
        else:
            logger.debug("Hotkey listener was not running or not initialized.")


def setup_fixed_hotkey_listener(app, config, stop_event):
    """
    Sets up a properly working hotkey listener with enhanced features.

    This is the main entry point that should be called from the application.
    It creates a HotkeyManager instance and starts the listener.
    """
    try:
        logger.info(f"Setting up hotkey listener with config: {config}")
        
        try:
            # pynput.keyboard is imported at the top of the file
            pass
        except ImportError: # Should not happen if import at top is successful
            logger.error("pynput module not found. Hotkeys will not work.")
            # Consider showing a messagebox if UI is available and it's critical
            # from tkinter import messagebox
            # messagebox.showerror("Error", "pynput module not found. Hotkeys will not work.")
            return None
            
        manager = HotkeyManager(app, config, stop_event) # Pass config dict

        thread = manager.start_listener()

        if thread is None:
            logger.error("Hotkey listener thread could not be started.")
            return None

        app.hotkey_manager = manager
        
        if hasattr(manager, 'hotkeys_callbacks') and manager.hotkeys_callbacks:
            logger.info(f"Active global hotkeys: {list(manager.hotkeys_callbacks.keys())}")
        else:
            logger.info("No active global hotkeys configured or listener failed.")

        return thread
    except Exception as e:
        logger.error(f"Error setting up hotkey listener: {e}", exc_info=True)
        return None
