import tkinter as tk
import os
from tkinter import messagebox

class SystemTrayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter System Tray Test")
        
        # Withdraw the window to make it invisible
        self.root.withdraw()
        
        # Make sure it appears on top when shown
        self.root.attributes("-topmost", True)
        
        # Create a simple button
        tk.Button(root, text="Hide to System Tray", command=self.hide_window).pack(padx=20, pady=20)
        tk.Button(root, text="Exit", command=self.exit_app).pack(padx=20, pady=10)
        
        # Create system tray icon using Tkinter's protocols
        self.setup_tray()
        
        # Show window on start
        self.root.deiconify()
        print("Window should now be visible - will minimize to tray in 5 seconds")
        self.root.after(5000, self.hide_window)

    def setup_tray(self):
        # This creates a taskbar icon when minimized
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Create a right-click menu for the taskbar icon
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Show Window", command=self.show_window)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.exit_app)
        
        # Bind taskbar icon click to show the window
        self.root.bind("<Map>", lambda e: print("Window mapped (shown)"))
        self.root.bind("<Unmap>", lambda e: print("Window unmapped (hidden)"))
        
        print("Tray setup complete")

    def show_window(self):
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.attributes("-topmost", False)
        print("Window shown")

    def hide_window(self):
        self.root.withdraw()
        messagebox.showinfo("System Tray", "Application minimized to system tray\nLook for it in the taskbar!")
        print("Window hidden to system tray")

    def exit_app(self):
        print("Exiting application")
        self.root.destroy()

if __name__ == "__main__":
    print("Current directory:", os.getcwd())
    print("Starting Tkinter System Tray Test")
    root = tk.Tk()
    app = SystemTrayApp(root)
    root.mainloop()
