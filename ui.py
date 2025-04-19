# filepath: d:\Autocompelete\ui.py
import tkinter as tk
from tkinter import messagebox
import config
import core
import threading
import os
import sys
from PIL import Image, ImageDraw

# Check if pystray is available
try:
    import pystray
    from pystray import MenuItem as item
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("pystray module not available - system tray functionality will be limited")

class KeywordAutomatorApp:
    def __init__(self):
        # Load configuration
        config.config = config.load_config()
        
        # Create a tkinter root for dialogs
        self.tk_root = tk.Tk()
        self.tk_root.title("Keyword Automator")
        self.tk_root.geometry("300x200")
        
        # Create a simple UI for the main window
        self.setup_main_window()
        
        # Create a stop event for threads
        self.stop_event = threading.Event()
        
        # Set up hotkey listener
        self.setup_hotkey_listener()
        
        # Set up system tray
        if PYSTRAY_AVAILABLE:
            self.setup_system_tray()
        
        # Set the protocol for when the window is closed (X button)
        self.tk_root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        print("Keyword Automator started")
        print(f"Press {config.config['hotkey']} or use the system tray icon to show the keyword input dialog")
    
    def setup_main_window(self):
        # Create a simple UI for the main window
        tk.Label(self.tk_root, text="Keyword Automator", font=("Arial", 14)).pack(pady=10)
        tk.Button(self.tk_root, text="Enter Keyword", command=self.show_input).pack(pady=5)
        tk.Button(self.tk_root, text="Settings", command=self.show_settings).pack(pady=5)
        tk.Button(self.tk_root, text="Minimize to Tray", command=self.minimize_to_tray).pack(pady=5)
        tk.Button(self.tk_root, text="Exit", command=self.exit_app).pack(pady=5)
    
    def create_icon_image(self):
        # Create a simple icon that's easy to see
        width = 64
        height = 64
        
        # Create a new image with transparent background
        image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a nice blue square
        dc.rectangle((4, 4, width-4, height-4), fill=(70, 130, 180))
        
        # Add text "KA" for Keyword Automator
        dc.text((20, 24), "KA", fill=(255, 255, 255))
        
        return image
    
    def setup_system_tray(self):
        # Function to restore window from system tray
        def restore_window(icon, item):
            icon.stop()
            self.restore_from_tray()
        
        # Create the icon and menu
        image = self.create_icon_image()
        menu = (
            item('Show Window', restore_window, default=True),
            item('Enter Keyword', lambda icon, item: self.trigger_callback('input')),
            item('Settings', lambda icon, item: self.trigger_callback('settings')),
            pystray.Menu.SEPARATOR,
            item('Exit', lambda icon, item: self.trigger_callback('exit')),
        )
        
        # Create the icon
        self.icon = pystray.Icon("KeywordAutomator", image, "Keyword Automator", menu)
        
        # Start the icon in a separate thread
        self.icon_thread = threading.Thread(target=self.run_icon)
        self.icon_thread.daemon = True
    
    def run_icon(self):
        try:
            self.icon.run()
        except Exception as e:
            print(f"Error running system tray icon: {e}")
    
    def minimize_to_tray(self):
        print("Minimizing to system tray")
        self.tk_root.withdraw()  # Hide the window
        
        # Start the system tray icon if it's not already running
        if PYSTRAY_AVAILABLE and not getattr(self, 'icon_running', False):
            self.icon_running = True
            self.icon_thread.start()
    
    def restore_from_tray(self):
        print("Restoring from system tray")
        self.tk_root.after(0, self.show_window)
        self.icon_running = False
    
    def show_window(self):
        self.tk_root.deiconify()
        self.tk_root.attributes('-topmost', True)
        self.tk_root.attributes('-topmost', False)
        self.tk_root.focus_force()
    
    def trigger_callback(self, action):
        if action == 'input':
            self.icon.stop()
            self.icon_running = False
            self.tk_root.after(0, self.show_input)
        elif action == 'settings':
            self.icon.stop()
            self.icon_running = False
            self.tk_root.after(0, self.show_settings)
        elif action == 'exit':
            self.icon.stop()
            self.icon_running = False
            self.tk_root.after(0, self.exit_app)
    
    def setup_hotkey_listener(self):
        try:
            from pynput import keyboard
            
            def on_activate():
                print("Hotkey activated")
                self.show_input()
            
            hotkeys = {config.config['hotkey']: on_activate}
            
            def hotkey_thread_func():
                with keyboard.GlobalHotKeys(hotkeys) as listener:
                    print(f"Hotkey listener started for {config.config['hotkey']}")                    
                    try:
                        while not self.stop_event.is_set():
                            listener.wait()  # Wait for hotkey events
                            # Add a small sleep to prevent high CPU usage
                            import time
                            time.sleep(0.1)
                    except Exception as e:
                        print(f"Error in hotkey listener: {e}")
            
            self.hotkey_thread = threading.Thread(target=hotkey_thread_func)
            self.hotkey_thread.daemon = True
            self.hotkey_thread.start()
        except ImportError:
            print("pynput module not available - hotkey functionality disabled")
    
    def show_input(self):
        InputDialog(self.tk_root, config.config['mappings'])
    
    def show_settings(self):
        SettingsWindow(self.tk_root)
    
    def exit_app(self):
        print("Exiting application")
        self.stop_event.set()
        if hasattr(self, 'icon') and self.icon:
            try:
                self.icon.stop()
            except:
                pass
        self.tk_root.quit()
        self.tk_root.destroy()
    
    def run(self):
        try:
            # Keep the application running
            self.tk_root.mainloop()
        except KeyboardInterrupt:
            self.exit_app()

class InputDialog(tk.Toplevel):
    def __init__(self, parent, mappings):
        super().__init__(parent)
        self.mappings = mappings
        self.title("Enter Keyword")
        self.geometry("300x100")
        self.attributes('-topmost', True)  # Keep window on top
        tk.Label(self, text="Enter keyword:").pack(pady=10)
        self.entry = tk.Entry(self)
        self.entry.pack(pady=5)
        self.entry.focus_set()
        self.entry.bind("<Return>", self.submit)
        self.grab_set()  # Make dialog modal

    def submit(self, event=None):
        keyword = self.entry.get().strip()
        if core.execute_command(keyword, self.mappings):
            messagebox.showinfo("Success", f"Command for '{keyword}' executed")
            self.destroy()
        else:
            messagebox.showerror("Error", "Keyword not found")
            self.entry.delete(0, tk.END)

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("400x300")
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.update_listbox()
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=5)
        tk.Button(button_frame, text="Add", command=self.add_mapping).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit", command=self.edit_mapping).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete", command=self.delete_mapping).pack(side=tk.LEFT, padx=5)
        self.grab_set()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for keyword in config.config['mappings']:
            self.listbox.insert(tk.END, f"{keyword} -> {config.config['mappings'][keyword]}")

    def add_mapping(self):
        dialog = MappingDialog(self, "Add Mapping")
        self.wait_window(dialog)
        if hasattr(dialog, 'result') and dialog.result:
            keyword, command = dialog.result
            if keyword in config.config['mappings']:
                messagebox.showerror("Error", "Keyword already exists")
            else:
                config.config['mappings'][keyword] = command
                config.save_config(config.config)
                self.update_listbox()

    def edit_mapping(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("Info", "Select a mapping to edit")
            return
        keyword = self.listbox.get(selected[0]).split(" -> ")[0]
        command = config.config['mappings'][keyword]
        dialog = MappingDialog(self, "Edit Mapping", (keyword, command))
        self.wait_window(dialog)
        if hasattr(dialog, 'result') and dialog.result:
            new_keyword, new_command = dialog.result
            if new_keyword != keyword and new_keyword in config.config['mappings']:
                messagebox.showerror("Error", "Keyword already exists")
            else:
                del config.config['mappings'][keyword]
                config.config['mappings'][new_keyword] = new_command
                config.save_config(config.config)
                self.update_listbox()

    def delete_mapping(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("Info", "Select a mapping to delete")
            return
        keyword = self.listbox.get(selected[0]).split(" -> ")[0]
        if messagebox.askyesno("Confirm Delete", f"Delete mapping for '{keyword}'?"):
            del config.config['mappings'][keyword]
            config.save_config(config.config)
            self.update_listbox()

class MappingDialog(tk.Toplevel):
    def __init__(self, parent, title, initial=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x150")
        self.attributes('-topmost', True)
        self.result = None
        
        tk.Label(self, text="Keyword:").pack(pady=5)
        self.keyword_entry = tk.Entry(self)
        self.keyword_entry.pack(pady=5, fill=tk.X, padx=10)
        
        tk.Label(self, text="Command:").pack(pady=5)
        self.command_entry = tk.Entry(self)
        self.command_entry.pack(pady=5, fill=tk.X, padx=10)
        
        if initial:
            keyword, command = initial
            self.keyword_entry.insert(0, keyword)
            self.command_entry.insert(0, command)
        
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.keyword_entry.focus_set()

    def on_ok(self):
        keyword = self.keyword_entry.get().strip()
        command = self.command_entry.get().strip()
        if keyword and command:
            self.result = (keyword, command)
            self.destroy()
        else:
            messagebox.showerror("Error", "Both fields are required")

# For standalone execution
if __name__ == "__main__":
    app = KeywordAutomatorApp()
    app.run()
