import tkinter as tk
from tkinter import messagebox, scrolledtext
import config
import core
import threading
import os
import sys
from PIL import Image, ImageDraw

# Check if pystray is available
# Add this to the top of your file, after other imports
try:
    import tray
except ImportError:
    print("tray_fix module not found - using built-in solution")

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
        
        # Get the global hotkey from config
        global_hotkey = config.config.get('global_hotkey', '<ctrl>+<alt>+k')
        print(f"Press {global_hotkey} to show the keyword input dialog")
        print("The system tray icon should be visible now")
        
        # Print all configured hotkeys
        self.print_active_hotkeys()
    
    def print_active_hotkeys(self):
        """Print out all active hotkeys in the application"""
        print("\nActive hotkeys:")
        
        # Global hotkey
        global_hotkey = config.config.get('global_hotkey', '<ctrl>+<alt>+k')
        print(f"  {global_hotkey} -> Show keyword input dialog")
        
        # Individual keyword hotkeys
        for keyword, mapping_data in config.config['mappings'].items():
            if isinstance(mapping_data, dict) and mapping_data.get('hotkey'):
                hotkey = mapping_data['hotkey']
                command = mapping_data['command']
                cmd_preview = command[:30] + ('...' if len(command) > 30 else '')
                print(f"  {hotkey} -> {keyword}: {cmd_preview}")
    
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
        
        # Add text "KA" for Keyword Automator        dc.text((20, 24), "KA", fill=(255, 255, 255))
        
        return image
        
    def create_menu(self):
        """Create the system tray menu"""
        # Function to restore window from system tray
        def restore_window(icon, item):
            icon.stop()
            self.restore_from_tray()
        
        # Create and return the menu
        return (
            item('Show Window', restore_window, default=True),
            item('Enter Keyword', lambda icon, item: self.trigger_callback('input')),
            item('Settings', lambda icon, item: self.trigger_callback('settings')),
            pystray.Menu.SEPARATOR,
            item('Exit', lambda icon, item: self.trigger_callback('exit')),
        )
        
    def setup_system_tray(self):
        # Store the icon image for later use
        self.tray_image = self.create_icon_image()
        
        # Don't create the icon here - we'll create a fresh one each time in minimize_to_tray
    
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
            
            # Use the tray_fix module if available, otherwise use inline solution
            try:
                if 'tray_fix' in sys.modules:
                    # Use our specialized module
                    tray.run_tray_icon_in_thread(self)
                else:
                    # Create a fresh icon instance each time
                    def restore_window(icon, item):
                        icon.stop()
                        self.restore_from_tray()
                    
                    # Create the menu
                    menu = (
                        item('Show Window', restore_window, default=True),
                        item('Enter Keyword', lambda icon, item: self.trigger_callback('input')),
                        item('Settings', lambda icon, item: self.trigger_callback('settings')),
                        pystray.Menu.SEPARATOR,
                        item('Exit', lambda icon, item: self.trigger_callback('exit')),
                    )
                    
                    # Create a fresh icon for each minimization
                    self.icon = pystray.Icon("KeywordAutomator", self.create_icon_image(), 
                                           "Keyword Automator", menu)
                    
                    # Create a new thread for this instance
                    icon_thread = threading.Thread(target=self.run_icon)
                    icon_thread.daemon = True
                    icon_thread.start()
            except Exception as e:
                print(f"Error creating tray icon: {e}")
    
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
            
            # Create a function to show the input dialog (for the global hotkey)
            def show_input_dialog():
                print("Global hotkey activated")
                self.show_input()
            
            # Create the hotkeys dictionary starting with the global hotkey
            global_hotkey = config.config.get('global_hotkey', '<ctrl>+<alt>+k')
            hotkeys = {global_hotkey: show_input_dialog}
            
            # Add hotkeys for each keyword mapping that has a hotkey defined
            for keyword, mapping_data in config.config['mappings'].items():
                if isinstance(mapping_data, dict) and mapping_data.get('hotkey'):
                    hotkey = mapping_data['hotkey']
                    
                    # Create a closure to execute the command for this specific keyword
                    def create_hotkey_handler(kw):
                        def handler():
                            print(f"Hotkey activated for '{kw}'")
                            core.execute_command(kw, config.config['mappings'])
                        return handler
                    
                    # Add the hotkey to our dictionary
                    hotkeys[hotkey] = create_hotkey_handler(keyword)
            
            def hotkey_thread_func():
                with keyboard.GlobalHotKeys(hotkeys) as listener:
                    print(f"Hotkey listener started with {len(hotkeys)} hotkeys")                    
                    try:
                        # This is the key fix - we call wait() without parameters
                        # and use a separate sleep call to prevent high CPU usage
                        while not self.stop_event.is_set():
                            listener.wait()  # No parameters here
                            time.sleep(0.1)  # Sleep to reduce CPU usage
                    except Exception as e:
                        print(f"Error in hotkey listener: {e}")
            
            self.hotkey_thread = threading.Thread(target=hotkey_thread_func)
            self.hotkey_thread.daemon = True
            self.hotkey_thread.start()
        except ImportError:
            print("pynput module not available - hotkey functionality disabled")
            return None
    
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
        self.geometry("600x400")
        self.listbox = tk.Listbox(self, font=("Courier New", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.update_listbox()
        
        # Add a frame for global hotkey setting
        global_hotkey_frame = tk.Frame(self)
        global_hotkey_frame.pack(fill=tk.X, pady=5, padx=5)
        tk.Label(global_hotkey_frame, text="Global Hotkey:").pack(side=tk.LEFT)
        self.global_hotkey_entry = tk.Entry(global_hotkey_frame)
        global_hotkey = config.config.get('global_hotkey', '<ctrl>+<alt>+k')
        self.global_hotkey_entry.insert(0, global_hotkey)
        self.global_hotkey_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        tk.Button(global_hotkey_frame, text="Set", command=self.set_global_hotkey).pack(side=tk.LEFT, padx=5)
        
        # Add a frame for buttons
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=5)
        tk.Button(button_frame, text="Add", command=self.add_mapping).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit", command=self.edit_mapping).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete", command=self.delete_mapping).pack(side=tk.LEFT, padx=5)
        
        self.grab_set()
        
    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for keyword in config.config['mappings']:
            mapping_data = config.config['mappings'][keyword]
            if isinstance(mapping_data, dict):
                command = mapping_data.get('command', '')
                hotkey = mapping_data.get('hotkey', 'None')
                is_script = mapping_data.get('is_script', False)
                script_indicator = "[Script]" if is_script else "[Command]"
                display_text = f"{keyword} → {script_indicator} → [{hotkey or 'No hotkey'}] → {command[:30]}{'...' if len(command) > 30 else ''}"
            else:
                # Legacy format support
                display_text = f"{keyword} → [Command] → [No hotkey] → {mapping_data}"
            self.listbox.insert(tk.END, display_text)
            
    def set_global_hotkey(self):
        """Set the global hotkey and save the configuration"""
        new_hotkey = self.global_hotkey_entry.get().strip()
        if new_hotkey:
            config.config['global_hotkey'] = new_hotkey
            config.save_config(config.config)
            messagebox.showinfo("Success", "Global hotkey updated. Restart required to apply changes.")
            self.restart_required()

    def add_mapping(self):
        dialog = MappingDialog(self, "Add Mapping")
        self.wait_window(dialog)
        if hasattr(dialog, 'result') and dialog.result:
            keyword, mapping_data = dialog.result
            if keyword in config.config['mappings']:
                messagebox.showerror("Error", "Keyword already exists")
            else:
                config.config['mappings'][keyword] = mapping_data
                config.save_config(config.config)
                self.update_listbox()
                # Restart the app to apply new hotkeys if a hotkey was set
                if mapping_data.get('hotkey'):
                    self.restart_required()

    def edit_mapping(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("Info", "Select a mapping to edit")
            return
        
        # Get the keyword from the selected item (first part before the arrow)
        selected_text = self.listbox.get(selected[0])
        keyword = selected_text.split(" → ")[0].strip()
        
        # Get the mapping data
        mapping_data = config.config['mappings'][keyword]
        
        # Convert old format to new format if needed
        if not isinstance(mapping_data, dict):
            mapping_data = {
                'command': mapping_data,
                'hotkey': None,
                'is_script': False
            }
        
        dialog = MappingDialog(self, "Edit Mapping", (keyword, mapping_data))
        self.wait_window(dialog)
        
        if hasattr(dialog, 'result') and dialog.result:
            new_keyword, new_mapping_data = dialog.result
            if new_keyword != keyword and new_keyword in config.config['mappings']:
                messagebox.showerror("Error", "Keyword already exists")
            else:
                # Check if a hotkey was added, changed, or removed
                old_hotkey = mapping_data.get('hotkey')
                new_hotkey = new_mapping_data.get('hotkey')
                hotkey_changed = old_hotkey != new_hotkey
                
                # Update the config
                del config.config['mappings'][keyword]
                config.config['mappings'][new_keyword] = new_mapping_data
                config.save_config(config.config)
                self.update_listbox()
                
                # Restart required if hotkey changed
                if hotkey_changed:
                    self.restart_required()

    def delete_mapping(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("Info", "Select a mapping to delete")
            return
        
        selected_text = self.listbox.get(selected[0])
        keyword = selected_text.split(" → ")[0].strip()
        
        if messagebox.askyesno("Confirm Delete", f"Delete mapping for '{keyword}'?"):
            # Check if the mapping has a hotkey
            mapping_data = config.config['mappings'][keyword]
            has_hotkey = isinstance(mapping_data, dict) and mapping_data.get('hotkey')
            
            # Delete the mapping
            del config.config['mappings'][keyword]
            config.save_config(config.config)
            self.update_listbox()
            
            # Restart required if we deleted a mapping with a hotkey
            if has_hotkey:
                self.restart_required()
    def restart_required(self):
        """Show a message that restart is required to apply hotkey changes"""
        if messagebox.askyesno("Restart Required", 
                             "Hotkey changes require restarting the application. Restart now?"):
            # Find the root application object
            # Start from self.master and navigate up until we find the KeywordAutomatorApp instance
            root = self.master
            while root and not hasattr(root, 'exit_app'):
                if hasattr(root, 'master'):
                    root = root.master
                else:
                    root = None
            
            # Exit the current instance if we found the root
            if root and hasattr(root, 'exit_app'):
                root.after(500, root.exit_app)
            else:
                # Fallback if we can't find the root
                self.master.after(500, lambda: os._exit(0))
            
            # Start a new instance
            import sys
            import subprocess
            subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "main_enhanced.py")])

class MappingDialog(tk.Toplevel):
    def __init__(self, parent, title, initial=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("600x400")
        self.attributes('-topmost', True)
        self.result = None
        
        # Add scrollbar and frames
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Keyword field
        keyword_frame = tk.Frame(main_frame)
        keyword_frame.pack(fill=tk.X, pady=5)
        tk.Label(keyword_frame, text="Keyword:", width=15, anchor='w').pack(side=tk.LEFT)
        self.keyword_entry = tk.Entry(keyword_frame)
        self.keyword_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Hotkey field
        hotkey_frame = tk.Frame(main_frame)
        hotkey_frame.pack(fill=tk.X, pady=5)
        tk.Label(hotkey_frame, text="Hotkey (optional):", width=15, anchor='w').pack(side=tk.LEFT)
        self.hotkey_entry = tk.Entry(hotkey_frame)
        self.hotkey_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add a help label for hotkey format
        help_text = "Format: <ctrl>+<alt>+<key> (e.g., <ctrl>+<alt>+b)"
        tk.Label(hotkey_frame, text=help_text, fg="gray").pack(side=tk.LEFT, padx=5)
        
        # Is script checkbox
        script_frame = tk.Frame(main_frame)
        script_frame.pack(fill=tk.X, pady=5)
        self.is_script_var = tk.BooleanVar()
        script_check = tk.Checkbutton(script_frame, text="Complex script (multi-line PowerShell script)", 
                                        variable=self.is_script_var)
        script_check.pack(side=tk.LEFT)
        
        # Command field with scrollbar (text widget instead of entry for multi-line support)
        tk.Label(main_frame, text="Command/Script:", anchor='w').pack(fill=tk.X, pady=5)
        
        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.command_text = tk.Text(text_frame, height=10, wrap=tk.WORD, 
                                   yscrollcommand=scrollbar.set)
        self.command_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.command_text.yview)
        
        # Example button
        example_frame = tk.Frame(main_frame)
        example_frame.pack(fill=tk.X, pady=5)
        tk.Button(example_frame, text="Insert PowerShell Example", 
                 command=self.insert_example).pack(side=tk.LEFT)
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        tk.Button(button_frame, text="OK", command=self.on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)
        
        # Initialize with provided values if editing
        if initial:
            keyword, mapping_data = initial
            self.keyword_entry.insert(0, keyword)
            
            if isinstance(mapping_data, dict):
                # New format
                if mapping_data.get('hotkey'):
                    self.hotkey_entry.insert(0, mapping_data['hotkey'])
                
                self.is_script_var.set(mapping_data.get('is_script', False))
                self.command_text.insert('1.0', mapping_data.get('command', ''))
            else:
                # Old format
                self.command_text.insert('1.0', mapping_data)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.keyword_entry.focus_set()
    
    def insert_example(self):
        """Insert a PowerShell script example into the command text area"""
        example = """Start-Process "code"
Start-Sleep -Seconds 3
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("env{\\}Scripts{\\}activate{ENTER}")"""
        self.command_text.delete('1.0', tk.END)
        self.command_text.insert('1.0', example)
        self.is_script_var.set(True)

    def on_ok(self):
        keyword = self.keyword_entry.get().strip()
        hotkey = self.hotkey_entry.get().strip() or None  # None if empty
        command = self.command_text.get('1.0', tk.END).strip()
        is_script = self.is_script_var.get()
        
        if keyword and command:
            # Return the result in the new format
            self.result = (keyword, {
                'command': command,
                'hotkey': hotkey,
                'is_script': is_script
            })
            self.destroy()
        else:
            messagebox.showerror("Error", "Keyword and command are required")

# For standalone execution
if __name__ == "__main__":
    import time  # Make sure time is imported for the hotkey listener
    app = KeywordAutomatorApp()
    app.run()


