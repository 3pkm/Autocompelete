# filepath: d:\Autocompelete\main_enhanced.py
import wx
import threading
import config
import ui as ui  
import hotkey_fix as hotkey_fix  

class KeywordAutomatorFrame(wx.Frame):
    def __init__(self):
        super(KeywordAutomatorFrame, self).__init__(None, title="Keyword Automator", size=(1, 1))
        
        # Load configuration
        config.config = config.load_config()
        
        # Create a stop event for clean shutdown
        self.stop_event = threading.Event()
        
        # Set up the fixed hotkey listener (modified to support multiple hotkeys)
        self.hotkey_thread = hotkey_fix.setup_fixed_hotkey_listener(
            self, config.config, self.stop_event
        )
        
        # Create and run UI module's app in a separate thread
        self.ui_app_thread = threading.Thread(target=self.run_ui_app)
        self.ui_app_thread.daemon = True
        self.ui_app_thread.start()
        
        # Hide the wx frame (we're using the UI module's interface)
        self.Hide()
        
        print("Application initialized and running with enhanced UI module")
        print(f"Press {config.config.get('global_hotkey', '<ctrl>+<alt>+k')} to show the keyword input dialog")
        print("The system tray icon should be visible now")
    
    def run_ui_app(self):
        # Create and run the UI module's KeywordAutomatorApp
        self.ui_app = ui.KeywordAutomatorApp()
        self.ui_app.run()
    
    def show_input(self):
        # Method called by the hotkey listener
        if hasattr(self, 'ui_app'):
            wx.CallAfter(self.ui_app.show_input)
    
    def on_exit(self):
        print("Exiting application")
        self.stop_event.set()
        
        # Ensure UI app is closed properly
        if hasattr(self, 'ui_app'):
            self.ui_app.exit_app()
        
        self.Close()
        wx.GetApp().ExitMainLoop()

class KeywordAutomatorApp(wx.App):
    def OnInit(self):
        self.frame = KeywordAutomatorFrame()
        return True

def main():
    app = KeywordAutomatorApp(False)
    app.MainLoop()

if __name__ == "__main__":
    main()
