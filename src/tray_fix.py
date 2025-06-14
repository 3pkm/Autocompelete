import threading
import pystray
from pystray import MenuItem as item
import tkinter as tk
import logging
import os
import sys

# Get logger
logger = logging.getLogger(__name__)

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def create_fresh_tray_icon(app, image, title):
    """
    Creates a fresh tray icon instance each time.
    This fixes the 'invalid handle' error when minimizing to tray multiple times.
    """
    def restore_window(icon, item):
        try:
            icon.stop()
            app.restore_from_tray()
        except Exception as e:
            logger.error(f"Error in restore_window: {e}")

    def show_notification(icon, title, message):
        try:
            icon.notify(title, message)
        except Exception as e:
            logger.error(f"Error in show_notification: {e}")

    menu_items = [
        item('Show Window', restore_window, default=True),
        item('Enter Keyword', lambda icon, item: app.trigger_callback('input')),
        item('Settings', lambda icon, item: app.trigger_callback('settings')),
        pystray.Menu.SEPARATOR,
        item('Exit', lambda icon, item: app.trigger_callback('exit')),
    ]

    try:
        if hasattr(app, 'app_config') and isinstance(app.app_config, dict):
            mappings = app.app_config.get('mappings', {})
        else:
            mappings = app.get_config().get('mappings', {}) if hasattr(app, 'get_config') else {}
            
        if mappings:
            quick_items = []
            for i, keyword in enumerate(list(mappings.keys())[:5]):
                def create_command(kw):
                    return lambda icon, item: app.execute_keyword(kw)
                
                quick_items.append(item(keyword, create_command(keyword)))
            
            if quick_items:
                quick_menu = pystray.Menu(*quick_items)
                menu_items.insert(2, item('Quick Commands', quick_menu))
    except Exception as e:
        logger.error(f"Error creating quick commands menu: {e}")
    
    menu = pystray.Menu(*menu_items)
    
    return pystray.Icon(title, image, title, menu)

def run_tray_icon_in_thread(app):
    """
    Creates a fresh icon instance and runs it in a new thread.
    This should be called each time the application is minimized to tray.
    """
    try:
        app.icon = create_fresh_tray_icon(app, app.create_icon_image(), "Keyword Automator")
        
        icon_thread = threading.Thread(target=app.run_icon)
        icon_thread.daemon = True
        icon_thread.start()
        
        logger.info("Tray icon started successfully")
        return icon_thread
    except Exception as e:
        logger.error(f"Error running tray icon: {e}", exc_info=True)
        try:
            fallback = FallbackSystemTray(app)
            return fallback.run_in_thread()
        except Exception as e2:
            logger.error(f"Fallback tray icon also failed: {e2}", exc_info=True)
        return None

class FallbackSystemTray:
    """Fallback system tray implementation for platforms where pystray is not available"""
    
    def __init__(self, app):
        self.app = app
        self.is_running = False
        self.thread = None
        self.dummy_window = None
    
    def create_tray_icon(self):
        """Create a minimal fallback tray using Tkinter"""
        self.dummy_window = tk.Toplevel()
        self.dummy_window.title("Keyword Automator")
        self.dummy_window.geometry("1x1+0+0")
        self.dummy_window.withdraw()
        
        self.dummy_window.iconify()
        
        self.menu = tk.Menu(self.dummy_window, tearoff=0)
        self.menu.add_command(label="Show Window", command=self.app.restore_from_tray)
        self.menu.add_command(label="Enter Keyword", command=lambda: self.app.trigger_callback('input'))
        self.menu.add_command(label="Settings", command=lambda: self.app.trigger_callback('settings'))
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=lambda: self.app.trigger_callback('exit'))
        
        self.dummy_window.bind("<Button-3>", self.show_menu)
        
        self.dummy_window.bind("<Double-Button-1>", lambda e: self.app.restore_from_tray())
        
        self.is_running = True
    
    def show_menu(self, event):
        """Show the right-click menu"""
        self.menu.tk_popup(event.x_root, event.y_root)
    
    def run(self):
        """Run the fallback tray icon"""
        self.create_tray_icon()
        self.dummy_window.mainloop()
    
    def run_in_thread(self):
        """Run the fallback tray in a separate thread"""
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
        return self.thread
    
    def stop(self):
        """Stop the fallback tray"""
        if self.is_running and self.dummy_window:
            self.dummy_window.quit()
            self.dummy_window.destroy()
            self.is_running = False