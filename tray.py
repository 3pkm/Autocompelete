import threading
import pystray
from pystray import MenuItem as item

def create_fresh_tray_icon(app, image, title):
    """
    Creates a fresh tray icon instance each time.
    This fixes the 'invalid handle' error when minimizing to tray multiple times.
    """
    # Function to restore window from system tray
    def restore_window(icon, item):
        icon.stop()
        app.restore_from_tray()
    
    # Create the menu
    menu = (
        item('Show Window', restore_window, default=True),
        item('Enter Keyword', lambda icon, item: app.trigger_callback('input')),
        item('Settings', lambda icon, item: app.trigger_callback('settings')),
        pystray.Menu.SEPARATOR,
        item('Exit', lambda icon, item: app.trigger_callback('exit')),
    )
    
    # Create a fresh icon instance
    return pystray.Icon(title, image, title, menu)

def run_tray_icon_in_thread(app):
    """
    Creates a fresh icon instance and runs it in a new thread.
    This should be called each time the application is minimized to tray.
    """
    # Create a fresh icon instance
    app.icon = create_fresh_tray_icon(app, app.create_icon_image(), "Keyword Automator")
    
    # Create and start a new thread for this instance
    icon_thread = threading.Thread(target=app.run_icon)
    icon_thread.daemon = True
    icon_thread.start()
    
    # Return the thread in case it's needed
    return icon_thread
