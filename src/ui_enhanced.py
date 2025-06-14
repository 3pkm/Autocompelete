import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import sys
import json
import logging
import time
from PIL import Image, ImageTk, ImageDraw

from src import config, hotkey
from . import hotkey

logger = logging.getLogger(__name__)

try:
    from src import config as config_module, core, tray_fix
except ImportError:
    try:
        from . import config as config_module, core, tray_fix
    except ImportError:
        try:
            import config as config_module
            import core
            import src.hotkey as hotkey
            import tray_fix
        except ImportError:
            logger.error("Failed to import required modules. Check your installation.")
            messagebox.showerror(
                "Import Error",
                "Failed to import required modules. The application may not function correctly.",
            )

try:
    import pystray
    from pystray import MenuItem as item

    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    logger.warning(
        "pystray module not available - system tray functionality will be limited"
    )

THEME_COLORS = {
    "light": {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "highlight_bg": "#e0e0e0",
        "highlight_fg": "#000000",
        "button_bg": "#e0e0e0",
        "button_fg": "#000000",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "treeview_bg": "#ffffff",
        "treeview_fg": "#000000",
        "treeview_selected_bg": "#0078d7",
        "treeview_selected_fg": "#ffffff",
        "menu_bg": "#f0f0f0",
        "menu_fg": "#000000",
    },
    "dark": {
        "bg": "#2e2e2e",
        "fg": "#ffffff",
        "highlight_bg": "#3e3e3e",
        "highlight_fg": "#ffffff",
        "button_bg": "#3e3e3e",
        "button_fg": "#ffffff",
        "entry_bg": "#1e1e1e",
        "entry_fg": "#ffffff",
        "treeview_bg": "#2e2e2e",
        "treeview_fg": "#ffffff",
        "treeview_selected_bg": "#0078d7",
        "treeview_selected_fg": "#ffffff",
        "menu_bg": "#2e2e2e",
        "menu_fg": "#ffffff",
    },
}


class KeywordAutomatorApp:
    def __init__(self):
        self.app_config = config_module.load_config()

        self.tk_root = tk.Tk()

        self.setup_main_window()

        self.stop_event = threading.Event()

        self.setup_hotkey_listener()

        if PYSTRAY_AVAILABLE:
            self.setup_system_tray()

        self.tk_root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        if self.app_config.get("launch_at_startup", False):
            config_module.set_launch_at_startup(True)

        if self.app_config.get("startup_minimized", False):
            self.after_id = self.tk_root.after(100, self.minimize_to_tray)

        if not self.app_config.get("has_seen_welcome", False):
            self.tk_root.after(500, self.show_welcome_dialog)

        logger.info("Keyword Automator started")

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

        return os.path.join(base_path, relative_path)

    def apply_theme(self, theme_name):
        """Apply a color theme to the application"""
        if theme_name == "system":
            try:
                import darkdetect

                theme_name = "dark" if darkdetect.isDark() else "light"
            except ImportError:
                theme_name = "light"

        colors = THEME_COLORS.get(theme_name, THEME_COLORS["light"])

        style = ttk.Style()

        style.configure("TFrame", background=colors["bg"])
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        style.configure(
            "TButton", background=colors["button_bg"], foreground=colors["button_fg"]
        )
        style.configure(
            "TEntry", fieldbackground=colors["entry_bg"], foreground=colors["entry_fg"]
        )
        style.configure(
            "TCheckbutton", background=colors["bg"], foreground=colors["fg"]
        )
        style.configure("TNotebook", background=colors["bg"], foreground=colors["fg"])
        style.configure(
            "TNotebook.Tab",
            background=colors["button_bg"],
            foreground=colors["button_fg"],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", colors["highlight_bg"])],
            foreground=[("selected", colors["highlight_fg"])],
        )

        style.configure(
            "Treeview",
            background=colors["treeview_bg"],
            foreground=colors["treeview_fg"],
            fieldbackground=colors["treeview_bg"],
        )
        style.map(
            "Treeview",
            background=[("selected", colors["treeview_selected_bg"])],
            foreground=[("selected", colors["treeview_selected_fg"])],
        )

        style.configure(
            "TScrollbar", background=colors["bg"], troughcolor=colors["entry_bg"]
        )

        self.tk_root.configure(bg=colors["bg"])

        self._configure_menu_colors(self.tk_root, colors)

        self.current_theme = theme_name

        self.app_config["theme"] = theme_name
        config_module.save_config(self.app_config)

    def _configure_menu_colors(self, widget, colors):
        """Configure menu colors recursively"""
        try:
            if hasattr(widget, "configure") and hasattr(widget, "winfo_class"):
                if widget.winfo_class() == "Menu":
                    widget.configure(
                        background=colors["menu_bg"],
                        foreground=colors["menu_fg"],
                        activebackground=colors["highlight_bg"],
                        activeforeground=colors["highlight_fg"],
                    )
                    for i in range(
                        widget.index("end") + 1
                        if widget.index("end") is not None
                        else 0
                    ):
                        if widget.type(i) == "cascade":
                            cascade = widget.entrycget(i, "menu")
                            if cascade:
                                self._configure_menu_colors(cascade, colors)
        except Exception as e:
            logger.debug(f"Error configuring menu colors: {e}")

    def apply_theme_to_toplevel(self, toplevel, colors=None):
        """Apply theme to a toplevel window"""
        if colors is None:
            colors = THEME_COLORS.get(self.current_theme, THEME_COLORS["light"])

        toplevel.configure(bg=colors["bg"])

        if hasattr(toplevel, "menu") and toplevel.menu:
            self._configure_menu_colors(toplevel.menu, colors)

        for child in toplevel.winfo_children():
            if child.winfo_class() == "Menu":
                self._configure_menu_colors(child, colors)
            elif child.winfo_class() in (
                "TFrame",
                "TLabel",
                "TButton",
                "TEntry",
                "TCheckbutton",
            ):
                pass
            elif hasattr(child, "configure"):
                if child.winfo_class() in ("Frame", "Toplevel", "Label", "Button"):
                    child.configure(bg=colors["bg"], fg=colors["fg"])
                elif child.winfo_class() in ("Entry", "Text", "ScrolledText"):
                    child.configure(
                        bg=colors["entry_bg"],
                        fg=colors["entry_fg"],
                        insertbackground=colors["fg"],
                    )

            if hasattr(child, "winfo_children"):
                for subchild in child.winfo_children():
                    if hasattr(subchild, "configure"):
                        self.apply_theme_to_toplevel(subchild, colors)

    def setup_main_window(self):
        """Set up the main application window"""
        self.apply_theme(self.app_config.get("theme", "system"))

        self.tk_root.title("Keyword Automator")
        self.tk_root.geometry("600x500")
        self.tk_root.minsize(500, 400)

        try:
            icon_path = self.resource_path("assets/icon.ico")
            self.tk_root.iconbitmap(icon_path)
        except Exception as e:
            logger.error(f"Error loading icon: {e}")

        menu_bar = tk.Menu(self.tk_root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Import Settings", command=self.import_settings)
        file_menu.add_command(label="Export Settings", command=self.export_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        menu_bar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menu_bar, tearoff=0)
        self.theme_var = tk.StringVar(value=self.app_config.get("theme", "system"))
        view_menu.add_radiobutton(
            label="System Theme",
            variable=self.theme_var,
            value="system",
            command=lambda: self.change_theme("system"),
        )
        view_menu.add_radiobutton(
            label="Light Theme",
            variable=self.theme_var,
            value="light",
            command=lambda: self.change_theme("light"),
        )
        view_menu.add_radiobutton(
            label="Dark Theme",
            variable=self.theme_var,
            value="dark",
            command=lambda: self.change_theme("dark"),
        )
        menu_bar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.open_documentation)
        help_menu.add_command(label="Check for Updates", command=self.check_updates)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.tk_root.config(menu=menu_bar)

        main_frame = ttk.Frame(self.tk_root, padding="10")
        main_frame.pack(fill="both", expand=True)

        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))

        ttk.Label(
            title_frame, text="Keyword Automator", font=("Arial", 16, "bold")
        ).pack(side="top")
        ttk.Label(
            title_frame, text="Boost your productivity with custom keywords and hotkeys"
        ).pack(side="top")

        actions_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding="10")
        actions_frame.pack(fill="x", pady=10)

        ttk.Button(
            actions_frame, text="Add New Keyword", command=self.show_settings
        ).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="Enter Keyword", command=self.show_input).pack(
            side="left", padx=5
        )
        ttk.Button(actions_frame, text="Settings", command=self.show_settings).pack(
            side="left", padx=5
        )

        keywords_frame = ttk.LabelFrame(main_frame, text="Your Keywords", padding="10")
        keywords_frame.pack(fill="both", expand=True, pady=10)

        columns = ("Keyword", "Command", "Hotkey")
        self.keywords_tree = ttk.Treeview(
            keywords_frame, columns=columns, show="headings"
        )

        for col in columns:
            self.keywords_tree.heading(col, text=col)
            self.keywords_tree.column(col, width=100)

        tree_scroll_y = ttk.Scrollbar(
            keywords_frame, orient="vertical", command=self.keywords_tree.yview
        )
        tree_scroll_x = ttk.Scrollbar(
            keywords_frame, orient="horizontal", command=self.keywords_tree.xview
        )
        self.keywords_tree.configure(
            yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set
        )

        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.pack(side="bottom", fill="x")
        self.keywords_tree.pack(side="left", fill="both", expand=True)

        self.keywords_tree.bind("<Double-1>", self.on_keyword_double_click)

        self.context_menu = tk.Menu(self.keywords_tree, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_selected_keyword)
        self.context_menu.add_command(
            label="Delete", command=self.delete_selected_keyword
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Run Now", command=self.run_selected_keyword
        )

        self.keywords_tree.bind("<Button-3>", self.show_context_menu)

        self.update_keywords_list()

        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.tk_root, textvariable=self.status_var, relief="sunken", anchor="w"
        )
        status_bar.pack(side="bottom", fill="x")

    def update_keywords_list(self):
        """Update the keywords treeview with current mappings"""
        for item in self.keywords_tree.get_children():
            self.keywords_tree.delete(item)

        mappings = self.app_config.get("mappings", {})
        for keyword, value in mappings.items():
            if isinstance(value, dict):
                command = value.get("command", "")
                hotkey = value.get("hotkey", "None")
            else:
                # Legacy support
                command = value
                hotkey = "None"

            if len(command) > 50:
                command = command[:47] + "..."

            self.keywords_tree.insert("", "end", values=(keyword, command, hotkey))

    def on_keyword_double_click(self, event):
        """Handle double-click on a keyword in the treeview"""
        self.edit_selected_keyword()

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        iid = self.keywords_tree.identify_row(event.y)
        if iid:
            self.keywords_tree.selection_set(iid)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def edit_selected_keyword(self):
        """Edit the selected keyword"""
        selection = self.keywords_tree.selection()
        if selection:
            item = selection[0]
            values = self.keywords_tree.item(item, "values")
            if values:
                keyword = values[0]
                self.show_mapping_dialog(edit_keyword=keyword)

    def delete_selected_keyword(self):
        """Delete the selected keyword"""
        selection = self.keywords_tree.selection()
        if selection:
            item = selection[0]
            values = self.keywords_tree.item(item, "values")
            if values:
                keyword = values[0]
                if messagebox.askyesno(
                    "Confirm Delete",
                    f"Are you sure you want to delete the keyword '{keyword}'?",
                ):
                    if keyword in self.app_config.get("mappings", {}):
                        del self.app_config["mappings"][keyword]
                        config_module.save_config(self.app_config)

                        self.update_keywords_list()

                        self.setup_hotkey_listener()

    def run_selected_keyword(self):
        """Run the command for the selected keyword"""
        selection = self.keywords_tree.selection()
        if selection:
            item = selection[0]
            values = self.keywords_tree.item(item, "values")
            if values:
                keyword = values[0]
                self.execute_keyword(keyword)

    def create_icon_image(self):
        """Create an icon image for the system tray"""
        try:
            possible_paths = [
                self.resource_path("assets\\icon.ico"),
                self.resource_path("icon.ico"),
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico"
                ),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.ico"),
                "D:\\Autocompelete\\icon.ico",
            ]

            for icon_path in possible_paths:
                if os.path.exists(icon_path):
                    logger.info(f"Loading icon from: {icon_path}")
                    return Image.open(icon_path)

            logger.warning(f"Icon not found in any of the expected paths")
        except Exception as e:
            logger.error(f"Error loading icon: {e}")
        logger.info("Creating fallback icon")
        icon_size = (64, 64)
        image = Image.new("RGB", icon_size, (0, 128, 255))
        dc = ImageDraw.Draw(image)

        dc.rectangle(
            (2, 2, icon_size[0] - 3, icon_size[1] - 3),
            fill=(0, 128, 255),
            outline=(255, 255, 255),
            width=2,
        )

        dc.text((20, 20), "KA", fill=(255, 255, 255))

        return image
        image = Image.new("RGB", icon_size, color=(52, 152, 219))
        return image

    def setup_system_tray(self):
        """Set up the system tray icon"""
        if PYSTRAY_AVAILABLE:
            self.icon = tray_fix.create_fresh_tray_icon(
                self, self.create_icon_image(), "Keyword Automator"
            )
        else:
            self.icon = tray_fix.FallbackSystemTray(self)

    def run_icon(self):
        """Run the system tray icon"""
        try:
            self.icon.run()
        except Exception as e:
            logger.error(f"Error running system tray icon: {e}")

    def minimize_to_tray(self):
        """Minimize the application to system tray"""
        try:

            self.tk_root.withdraw()
            
            if hasattr(self, "icon") and hasattr(self.icon, "stop"):
                try:
                    self.icon.stop()
                    logger.info("Stopped previous system tray icon")
                except Exception as e:
                    logger.error(f"Error stopping previous tray icon: {e}")
            
            if PYSTRAY_AVAILABLE:
                try:
                    tray_thread = tray_fix.run_tray_icon_in_thread(self)
                    if tray_thread:
                        logger.info("Created new system tray icon (pystray)")
                    else:
                        raise Exception("Tray thread creation failed")
                except Exception as e:
                    logger.error(f"Error creating pystray icon: {e}")
                    fallback_tray = tray_fix.FallbackSystemTray(self)
                    fallback_tray.run_in_thread()
                    self.icon = fallback_tray
                    logger.info("Created fallback system tray icon")
            else:
                fallback_tray = tray_fix.FallbackSystemTray(self)
                fallback_tray.run_in_thread()
                self.icon = fallback_tray
                logger.info("Created fallback system tray icon (pystray not available)")
                
            logger.info("Application minimized to system tray")
        except Exception as e:
            logger.error(f"Error in minimize_to_tray: {e}", exc_info=True)
            try:
                self.tk_root.deiconify()
                messagebox.showerror(
                    "System Tray Error", 
                    "Could not minimize to system tray. The application will remain open."
                )
            except Exception:
                pass

    def restore_from_tray(self):
        """Restore the window from system tray"""
        try:
            if hasattr(self, "icon") and hasattr(self.icon, "stop"):
                try:
                    self.icon.stop()
                    logger.info("Stopped system tray icon")
                except Exception as e:
                    logger.error(f"Error stopping tray icon: {e}")
            
            self.tk_root.deiconify()
            self.tk_root.state('normal')
            self.tk_root.lift()
            self.tk_root.focus_force()
            self.tk_root.attributes('-topmost', True)
            self.tk_root.update()
            self.tk_root.attributes('-topmost', False)
            logger.info("Window restored from system tray")
        except Exception as e:
            logger.error(f"Error in restore_from_tray: {e}", exc_info=True)
            try:
                self.tk_root.deiconify()
                self.tk_root.update()
            except Exception as e2:
                logger.error(f"Critical error restoring window: {e2}", exc_info=True)

    def trigger_callback(self, action):
        """Trigger a callback action from the system tray menu"""
        logger.info(f"Tray icon action triggered: {action}")
        try:
            if action == "input":
                self.tk_root.after(100, self.show_input)
            elif action == "settings":
                # Restore window first, then show settings
                self.tk_root.after(100, lambda: [self.restore_from_tray(), self.show_settings()])
            elif action == "exit":
                # Schedule exit on the main thread to avoid threading issues
                self.tk_root.after(100, self.exit_app)
            else:
                # For any custom actions like running quick commands
                if action.startswith("run_"):
                    keyword = action[4:]  # Remove 'run_' prefix
                    self.tk_root.after(100, lambda k=keyword: self.execute_keyword(k))
        except Exception as e:
            logger.error(f"Error in trigger_callback for action '{action}': {e}", exc_info=True)
            # Try to show an error message but don't raise more exceptions
            try:
                messagebox.showerror("Action Error", f"Error executing {action}: {e}")
            except:
                pass

    def setup_hotkey_listener(self):
        """Set up the hotkey listener"""
        if hasattr(self, "hotkey_manager") and self.hotkey_manager and hasattr(self.hotkey_manager, "stop_listener"):
            self.hotkey_manager.stop_listener()

        # Pass the instance's config dictionary to the HotkeyManager
        self.hotkey_thread = hotkey.setup_fixed_hotkey_listener(
            self, self.app_config, self.stop_event # Pass self.app_config
        )
        if self.hotkey_thread:
            logger.info("Hotkey listener started successfully")
            # Print active hotkeys
            if hasattr(self, "hotkey_manager") and hasattr(
                self.hotkey_manager, "hotkeys"
            ):
                active_hotkeys = list(self.hotkey_manager.hotkeys.keys())
                logger.info(f"Active hotkeys: {active_hotkeys}")
                self.status_var.set(f"Active hotkeys: {', '.join(active_hotkeys)}")
        else:
            logger.warning("Failed to start hotkey listener")
            self.status_var.set("Warning: Hotkey functionality is disabled")

    def execute_keyword(self, keyword):
        """Execute the command associated with a keyword"""
        logger.info(f"Attempting to execute keyword: {keyword}")
        try:
            mappings = self.app_config.get("mappings", {})
            if keyword not in mappings:
                logger.warning(f"Keyword '{keyword}' not found in mappings")
                self.status_var.set(f"Keyword not found: {keyword}")
                messagebox.showerror(
                    "Keyword Error",
                    f"The keyword '{keyword}' is not defined in your settings.",
                )
                return False
            
            success = core.execute_command(keyword, mappings)
            if success:
                self.status_var.set(f"Executed: {keyword}")
                return True
            else:
                self.status_var.set(f"Failed to execute: {keyword}")
                messagebox.showerror(
                    "Execution Error",
                    f"Failed to execute the command for the keyword: {keyword}",
                )
                return False
        except Exception as e:
            logger.error(f"Error executing keyword '{keyword}': {e}", exc_info=True)
            self.status_var.set(f"Error: {e}")
            messagebox.showerror(
                "Execution Error",
                f"An error occurred while executing '{keyword}':\n\n{e}"
            )
            return False

    def get_config(self):
        """Return the current configuration dictionary"""
        return self.app_config # Return instance's config

    def change_theme(self, theme_name):
        """Change the application theme"""
        self.apply_theme(theme_name)
        # Save the theme preference in the instance config (apply_theme already does this)
        # self.app_config["theme"] = theme_name
        # config_module.save_config(self.app_config)

    def import_settings(self):
        """Import settings from a JSON file"""
        file_path = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        )

        if file_path:
            try:
                with open(file_path, "r") as f:
                    imported_config = json.load(f)
                    # Validate imported config (basic check)
                    if isinstance(imported_config, dict) and "mappings" in imported_config:
                        self.app_config = imported_config # Update instance config
                        config_module.save_config(self.app_config) # Save the new instance config
                        self.update_keywords_list()
                        self.apply_theme(self.app_config.get("theme", "system")) # Apply new theme
                        # Restart hotkey listener to apply potential global hotkey changes
                        self.setup_hotkey_listener()
                        messagebox.showinfo(
                            "Import Successful", "Settings imported successfully."
                        )
                    else:
                        messagebox.showerror(
                            "Import Error",
                            "The selected file does not contain valid settings.",
                        )

            except Exception as e:
                logger.error(f"Error importing settings: {e}")
                messagebox.showerror("Import Error", f"Failed to import settings: {e}")

    def export_settings(self):
        """Export current settings to a JSON file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Export Settings As",
            initialfile="keyword_automator_settings.json",
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(self.app_config, f, indent=4) # Use self.app_config
                messagebox.showinfo(
                    "Export Successful", "Settings exported successfully."
                )

            except Exception as e:
                logger.error(f"Error exporting settings: {e}")
                messagebox.showerror("Export Error", f"Failed to export settings: {e}")

    def open_documentation(self):
        """Open the documentation"""
        # Check if there's a local docs file
        docs_path = self.resource_path("docs/index.html")
        if os.path.exists(docs_path):
            # Open the local documentation
            import webbrowser

            webbrowser.open(f"file://{os.path.abspath(docs_path)}")
        else:
            # Fallback to showing built-in documentation
            self.show_built_in_docs()

    def show_built_in_docs(self):
        """Show built-in documentation"""
        docs_window = tk.Toplevel(self.tk_root)
        docs_window.title("Keyword Automator Documentation")
        docs_window.geometry("700x500")
        docs_window.transient(self.tk_root)

        # Apply current theme
        self.apply_theme_to_toplevel(docs_window)

        # Create a scrolled text widget
        text = scrolledtext.ScrolledText(docs_window, wrap=tk.WORD)
        text.pack(fill="both", expand=True, padx=10, pady=10)

        # Set colors based on current theme
        colors = THEME_COLORS.get(self.current_theme, THEME_COLORS["light"])
        text.configure(
            bg=colors["entry_bg"], fg=colors["entry_fg"], insertbackground=colors["fg"]
        )

        # Insert documentation content
        docs_content = """# Keyword Automator Documentation

## Introduction
Keyword Automator lets you define custom keywords that can be triggered anytime to execute commands or scripts.

## Key Features
- Trigger commands with custom keywords
- Assign global hotkeys to keywords
- Run scripts (PowerShell, Python, Batch)
- System tray integration
- Dark and light themes

## Basic Usage
1. Press Ctrl+Alt+K (default global hotkey) to open the keyword input dialog
2. Type your keyword and press Enter
3. The associated command will execute

## Managing Keywords
- Open Settings to add, edit, or delete keywords
- Each keyword can be associated with a command or script
- You can also assign a hotkey to trigger the keyword directly

## Advanced Features
- Scripts: Set the "Is Script" option to run complex scripts
- Admin Rights: Enable "Run as Administrator" for commands that need elevated privileges
- Window Visibility: Toggle "Show Window" to control whether command windows are shown

## Keyboard Shortcuts
- Global Activation: Ctrl+Alt+K (customizable)
- Individual keywords can have their own hotkeys

## Tips and Tricks
- Use scripts for complex operations
- Export your settings as a backup
- Set up your most frequently used commands
"""
        text.insert(tk.END, docs_content)
        text.configure(state="disabled")  # Make it read-only

    def check_updates(self):
        """Check for updates"""
        # This would typically connect to a server to check for updates
        # For now, we'll just show a placeholder message
        messagebox.showinfo(
            "Updates", "You are using the latest version of Keyword Automator."
        )

    def show_about(self):
        """Show about dialog"""
        about_text = """Keyword Automator v1.0

A productivity tool that lets you define keywords to trigger commands and scripts.

© 2025 KeywordAutomator
        """
        messagebox.showinfo("About", about_text)

    def show_welcome_dialog(self):
        """Show the first-run welcome dialog"""
        # ... (ensure this dialog doesn't cause issues, uses self.app_config if needed for 'has_seen_welcome')
        # ...
        # Mark as seen in instance config
        self.app_config["has_seen_welcome"] = True # Use self.app_config
        config_module.save_config(self.app_config) # Pass self.app_config to save

    def show_input(self):
        """Show the keyword input dialog"""
        # Restore window if minimized
        self.restore_from_tray()

        # Create and show input dialog
        input_dialog = InputDialog(self.tk_root, self.app_config.get("mappings", {}))
        
        # Explicitly set the parent app reference for the dialog
        input_dialog.parent_app = self
        
        # Wait for the dialog to close
        self.tk_root.wait_window(input_dialog)

    def show_settings(self):
        """Show the settings dialog"""
        # Restore window if minimized
        self.restore_from_tray()

        # Create and show settings dialog
        settings_dialog = SettingsWindow(self) # Pass self (KeywordAutomatorApp instance)
        self.tk_root.wait_window(settings_dialog)

        # Refresh the UI
        self.update_keywords_list()

        # Restart hotkey listener to apply changes
        self.setup_hotkey_listener()

    def show_mapping_dialog(self, edit_keyword=None):
        """Show dialog to add or edit a keyword mapping"""
        # Get the initial mapping if editing
        initial = None
        if edit_keyword and edit_keyword in self.app_config.get("mappings", {}):
            initial = {
                "keyword": edit_keyword,
                "mapping": self.app_config["mappings"][edit_keyword],
            }

        # Show the dialog
        dialog_title = "Edit Keyword" if edit_keyword else "Add Keyword"
        dialog = MappingDialog(self.tk_root, dialog_title, initial)
        self.tk_root.wait_window(dialog)

        # Refresh UI and hotkeys if changes were made
        if dialog.result:
            self.update_keywords_list()
            self.setup_hotkey_listener()

    def exit_app(self):
        """Exit the application"""
        if messagebox.askyesno(
            "Exit", "Are you sure you want to exit Keyword Automator?"
        ):
            # Stop all threads
            self.stop_event.set()

            # Stop tray icon if running
            if hasattr(self, "icon") and hasattr(self.icon, "stop"):
                try:
                    self.icon.stop()
                except:
                    pass

            # Exit the application
            self.tk_root.quit()

    def run(self):
        """Run the application"""
        self.tk_root.mainloop()


class InputDialog(tk.Toplevel):
    """Dialog for entering a keyword"""

    def __init__(self, parent, mappings=None):
        super().__init__(parent)
        
        # Try to get parent app instance for config and settings
        self.parent_app = parent
        
        # Get mappings from parent if available
        if mappings is None and hasattr(self.parent_app, 'app_config'):
            try:
                # Try to get mappings from the parent app's config
                mappings = self.parent_app.app_config.get('mappings', {})
            except Exception as e:
                logger.error(f"Error getting mappings from parent app: {e}")
                mappings = {}
                
        self.mappings = mappings

        # Apply theme
        if hasattr(self.parent_app, "apply_theme_to_toplevel") and hasattr(
            self.parent_app, "current_theme"
        ):
            self.parent_app.apply_theme_to_toplevel(self)

        self.title("Enter Keyword")
        self.geometry("350x150")
        self.resizable(False, False)
        self.transient(parent)  # Keep on top of parent
        self.grab_set()  # Modal behavior

        # Center the dialog
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        self_width = 350
        self_height = 150
        x = parent_x + (parent_width // 2) - (self_width // 2)
        y = parent_y + (parent_height // 2) - (self_height // 2)
        self.geometry(f"{self_width}x{self_height}+{x}+{y}")

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Enter the keyword to execute:").pack(
            pady=(0, 10)
        )

        self.keyword_entry = ttk.Entry(main_frame, width=40)
        self.keyword_entry.pack(pady=5)
        self.keyword_entry.focus_set()  # Set focus to entry

        # Bind Enter key to the submit action
        self.keyword_entry.bind("<Return>", self.submit)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        # Use self.submit for the button command, not self.callback directly
        submit_button = ttk.Button(
            button_frame, text="Execute", command=self.submit
        )
        submit_button.pack(side="left", padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side="left", padx=5)

        # Close with Escape key
        self.bind("<Escape>", lambda e: self.destroy())

    def submit(self, event=None):  # Added event=None for direct calls
        """Handle keyword submission"""
        keyword = self.keyword_entry.get().strip()
        if keyword:
            try:
                # Try to execute using parent app first (more reliable)
                if hasattr(self.parent_app, 'execute_keyword'):
                    self.parent_app.execute_keyword(keyword)
                    self.destroy()
                    return
                    
                # Fallback to mappings if provided and parent app method not available
                if self.mappings and keyword in self.mappings:
                    from src import core
                    core.execute_command(keyword, self.mappings)
                    self.destroy()
                    return
                    
                messagebox.showwarning(
                    "Keyword Not Found", f"The keyword '{keyword}' was not found.", parent=self
                )
            except Exception as e:
                logger.error(f"Error executing keyword: {e}")
                messagebox.showerror("Execution Error", f"Error: {e}", parent=self)
        else:
            messagebox.showwarning(
                "Input Required", "Please enter a keyword.", parent=self
            )


class SettingsWindow(tk.Toplevel):
    """Settings dialog with tabbed interface"""

    def __init__(self, parent_app): # parent_app is KeywordAutomatorApp instance
        super().__init__(parent_app.tk_root) # Master is parent_app.tk_root
        self.title("Settings")
        self.geometry("700x600")
        self.transient(parent_app.tk_root) # Transient to parent_app.tk_root
        self.grab_set()
        
        # Get parent app and config
        self.parent_app = parent_app # Store the KeywordAutomatorApp instance
        self.config_data = self.parent_app.app_config # Access app_config from parent_app

        # Apply theme from parent
        if hasattr(self.parent_app, "apply_theme_to_toplevel"):
            self.parent_app.apply_theme_to_toplevel(self)

        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Mappings tab
        self.mappings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mappings_frame, text="Keywords")

        # Hotkeys tab
        self.hotkeys_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.hotkeys_frame, text="Hotkeys")

        # General settings tab
        self.general_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.general_frame, text="General")

        # Setup mappings interface
        self.setup_mappings_tab()

        # Setup hotkeys interface
        self.setup_hotkeys_tab()

        # Setup general settings
        self.setup_general_tab()

        # Bottom buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Import", command=self.import_settings).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Export", command=self.export_settings).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(
            side="right", padx=5
        )

    def setup_mappings_tab(self):
        """Set up the mappings (keywords) tab"""
        # Create a frame for the listbox and buttons
        list_frame = ttk.Frame(self.mappings_frame)
        list_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Create a listbox for the mappings
        ttk.Label(list_frame, text="Keywords:").pack(anchor="w")

        # Create a treeview instead of a simple listbox
        columns = ("Keyword", "Command", "Hotkey")
        self.mappings_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # Define column headings
        for col in columns:
            self.mappings_tree.heading(col, text=col)
            self.mappings_tree.column(col, width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.mappings_tree.yview
        )
        self.mappings_tree.configure(yscrollcommand=scrollbar.set)

        # Pack the treeview and scrollbar
        self.mappings_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Double-click to edit
        self.mappings_tree.bind("<Double-1>", lambda e: self.edit_mapping())

        # Create buttons
        buttons_frame = ttk.Frame(self.mappings_frame)
        buttons_frame.pack(side="right", fill="y", padx=10, pady=10)

        ttk.Button(buttons_frame, text="Add", command=self.add_mapping).pack(
            fill="x", pady=2
        )
        ttk.Button(buttons_frame, text="Edit", command=self.edit_mapping).pack(
            fill="x", pady=2
        )
        ttk.Button(buttons_frame, text="Delete", command=self.delete_mapping).pack(
            fill="x", pady=2
        )

        # Update the listbox
        self.update_mappings_tree()

    def setup_hotkeys_tab(self):
        """Set up the hotkeys tab"""
        # Global hotkey frame
        global_frame = ttk.LabelFrame(self.hotkeys_frame, text="Global Hotkey")
        global_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(global_frame, text="Global activation hotkey:").pack(
            anchor="w", padx=10, pady=(10, 5)
        )

        hotkey_frame = ttk.Frame(global_frame)
        hotkey_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.global_hotkey_var = tk.StringVar(
            value=self.config_data.get("global_hotkey", "<ctrl>+<alt>+k")
        )
        ttk.Entry(hotkey_frame, textvariable=self.global_hotkey_var, width=30).grid(
            row=0, column=0, sticky="we", padx=5
        )
        # Use grid for the button as well, consistent with the Entry widget
        ttk.Button(hotkey_frame, text="Set", command=self.set_global_hotkey).grid(
            row=0, column=1, padx=5
        )

        ttk.Label(
            global_frame, text="Format: <modifier>+<key> (e.g., <ctrl>+<alt>+k)"
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # Per-keyword hotkeys frame
        keyword_frame = ttk.LabelFrame(self.hotkeys_frame, text="Keyword Hotkeys")
        keyword_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(
            keyword_frame,
            text="You can assign hotkeys to individual keywords in the Keywords tab.",
        ).pack(anchor="w", padx=10, pady=10)

    def setup_general_tab(self):
        """Set up the general settings tab"""
        # Startup options
        startup_frame = ttk.LabelFrame(self.general_frame, text="Startup Options")
        startup_frame.pack(fill="x", padx=10, pady=10)

        # Launch at startup
        self.launch_at_startup_var = tk.BooleanVar(
            value=self.config_data.get("launch_at_startup", True)
        )
        ttk.Checkbutton(
            startup_frame,
            text="Launch at system startup",
            variable=self.launch_at_startup_var,
        ).pack(anchor="w", padx=10, pady=10)

        # Start minimized
        self.startup_minimized_var = tk.BooleanVar(
            value=self.config_data.get("startup_minimized", False)
        )
        ttk.Checkbutton(
            startup_frame,
            text="Start minimized to system tray",
            variable=self.startup_minimized_var,
        ).pack(anchor="w", padx=10, pady=10)

        # Appearance options
        appearance_frame = ttk.LabelFrame(self.general_frame, text="Appearance")
        appearance_frame.pack(fill="x", padx=10, pady=10)

        # Theme selection
        ttk.Label(appearance_frame, text="Theme:").pack(
            anchor="w", padx=10, pady=(10, 5)
        )

        self.theme_var = tk.StringVar(value=self.config_data.get("theme", "system"))
        theme_frame = ttk.Frame(appearance_frame)
        theme_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Radiobutton(
            theme_frame, text="System", variable=self.theme_var, value="system"
        ).pack(side="left", padx=5)
        ttk.Radiobutton(
            theme_frame, text="Light", variable=self.theme_var, value="light"
        ).pack(side="left", padx=5)
        ttk.Radiobutton(
            theme_frame, text="Dark", variable=self.theme_var, value="dark"
        ).pack(side="left", padx=5)

    def update_mappings_tree(self):
        """Update the mappings treeview"""
        # Clear existing items
        for item in self.mappings_tree.get_children():
            self.mappings_tree.delete(item)

        # Add current mappings using the parent app's config
        mappings = self.config_data.get("mappings", {})
        for keyword, value in mappings.items():
            if isinstance(value, dict):
                command = value.get("command", "")
                hotkey = value.get("hotkey", "None")
            else:
                # Legacy support
                command = value
                hotkey = "None"

            # Truncate long commands for display
            if len(command) > 50:
                command = command[:47] + "..."

            self.mappings_tree.insert("", "end", values=(keyword, command, hotkey))

    def set_global_hotkey(self):
        """Set the global hotkey"""
        new_hotkey = self.global_hotkey_var.get().strip()

        if not new_hotkey:
            messagebox.showwarning("Invalid Hotkey", "Please enter a valid hotkey.")
            return

        # Basic validation
        if "+" not in new_hotkey:
            messagebox.showwarning(
                "Invalid Format",
                "Hotkey should be in format: <modifier>+<key> (e.g., <ctrl>+<alt>+k)",
            )
            return

        # Update config (use self.config_data which refers to parent_app.app_config)
        self.config_data["global_hotkey"] = new_hotkey
        config_module.save_config(self.config_data) # Save the updated config_data

        # Flag that restart is required
        self.restart_required()

    def add_mapping(self):
        """Add a new keyword mapping"""
        # Pass self.parent_app (KeywordAutomatorApp instance) to MappingDialog
        # Pass title and None for initial_mapping_data
        dialog = MappingDialog(self.parent_app, "Add Keyword", None)
        self.wait_window(dialog)

        if dialog.result: # Assuming dialog sets a result attribute
            # Refresh the mappings list
            self.update_mappings_tree()

    def edit_mapping(self):
        """Edit an existing keyword mapping"""
        selection = self.mappings_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a keyword to edit.")
            return

        # Get the selected keyword
        item = selection[0]
        values = self.mappings_tree.item(item, "values")
        if values:
            keyword = values[0]

            # Get the mapping data from self.config_data
            mappings = self.config_data.get("mappings", {})
            if keyword in mappings:
                initial_data = {"keyword": keyword, "mapping": mappings[keyword]}

                # Show edit dialog, passing self.parent_app, title, and initial_data
                dialog = MappingDialog(self.parent_app, "Edit Keyword", initial_data)
                self.wait_window(dialog)

                if dialog.result: # Assuming dialog sets a result attribute
                    # Refresh the mappings list
                    self.update_mappings_tree()

    def delete_mapping(self):
        """Delete an existing keyword mapping"""
        selection = self.mappings_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a keyword to delete.")
            return

        # Get the selected keyword
        item = selection[0]
        values = self.mappings_tree.item(item, "values")
        if values:
            keyword = values[0]

            # Confirm deletion
            if messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete the keyword '{keyword}'?",
            ):
                # Delete from self.config_data
                mappings = self.config_data.get("mappings", {})
                if keyword in mappings:
                    del mappings[keyword]
                    config_module.save_config(self.config_data) # Save the updated self.config_data

                    # Refresh the mappings list
                    self.update_mappings_tree()

    def import_settings(self):
        """Import settings from a JSON file"""
        app = self.parent_app # Use self.parent_app
        if hasattr(app, "import_settings"):
            app.import_settings()

            # Refresh the UI
            self.update_mappings_tree()

    def export_settings(self):
        """Export settings to a JSON file"""
        app = self.parent_app # Use self.parent_app
        if hasattr(app, "export_settings"):
            app.export_settings()

    def restart_required(self):
        """Show a message that restart is required"""
        messagebox.showinfo(
            "Restart Required",
            "Some changes require restarting the hotkey listener. "
            "This will happen automatically when you click OK.",
        )

    def on_ok(self):
        """Apply settings and close the dialog"""
        # Save general settings
        # Ensure we are updating the config on the parent_app instance
        self.parent_app.app_config["launch_at_startup"] = self.launch_at_startup_var.get()
        self.parent_app.app_config["startup_minimized"] = self.startup_minimized_var.get()
        self.parent_app.app_config["theme"] = self.theme_var.get()

        # Apply launch at startup setting
        config_module.set_launch_at_startup(self.parent_app.app_config["launch_at_startup"])

        # Save config using the parent_app's config
        config_module.save_config(self.parent_app.app_config)

        # Apply theme change
        if hasattr(self.parent_app, "apply_theme"):
            self.parent_app.apply_theme(self.parent_app.app_config["theme"])

        # Close the dialog
        self.destroy()


class MappingDialog(tk.Toplevel):
    """Dialog for adding or editing a keyword mapping"""

    def __init__(self, parent_app, title, initial_mapping_data=None): # parent_app is KeywordAutomatorApp instance
        super().__init__(parent_app.tk_root)
        self.parent_app = parent_app
        self.config_data = parent_app.app_config # Get config from parent app instance
        self.result = False # To indicate if changes were saved

        # Determine if editing or adding
        if initial_mapping_data and "keyword" in initial_mapping_data:
            self.edit_keyword = initial_mapping_data["keyword"]
            self.original_keyword = initial_mapping_data["keyword"] # Store original for renaming checks
            self.mapping_details = initial_mapping_data.get("mapping", {})
        else:
            self.edit_keyword = None
            self.original_keyword = None
            self.mapping_details = {}

        # Apply theme
        if hasattr(self.parent_app, "apply_theme_to_toplevel") and hasattr(
            self.parent_app, "current_theme"
        ):
            self.parent_app.apply_theme_to_toplevel(self)

        self.title(title) # Use the passed title
        self.geometry("500x450") # Adjusted height for Text widget
        self.resizable(False, False)
        self.transient(parent_app.tk_root)  # Keep on top of parent
        self.grab_set()  # Modal behavior

        # Center the dialog
        parent_x = parent_app.tk_root.winfo_x()
        parent_y = parent_app.tk_root.winfo_y()
        parent_width = parent_app.tk_root.winfo_width()
        parent_height = parent_app.tk_root.winfo_height()
        self_width = 500
        self_height = 400
        x = parent_x + (parent_width // 2) - (self_width // 2)
        y = parent_y + (parent_height // 2) - (self_height // 2)
        self.geometry(f"{self_width}x{self_height}+{x}+{y}")

        # Mapping form
        form_frame = ttk.Frame(self, padding="10")
        form_frame.pack(fill="both", expand=True)

        # Keyword
        ttk.Label(form_frame, text="Keyword:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.keyword_entry = ttk.Entry(form_frame, width=30)
        self.keyword_entry.grid(row=0, column=1, sticky="we", padx=5, pady=5)

        # Command - Changed to tk.Text
        ttk.Label(form_frame, text="Command:").grid(
            row=1, column=0, sticky="nw", padx=5, pady=5 # sticky nw for label
        )
        self.command_entry = tk.Text(form_frame, width=40, height=5, wrap=tk.WORD) # Use tk.Text
        self.command_entry.grid(row=1, column=1, sticky="we", padx=5, pady=5)
        # Add a scrollbar for the Text widget
        command_scrollbar = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=self.command_entry.yview)
        command_scrollbar.grid(row=1, column=2, sticky="ns", pady=5)
        self.command_entry.config(yscrollcommand=command_scrollbar.set)


        # Hotkey
        ttk.Label(form_frame, text="Hotkey (optional):").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.hotkey_entry = ttk.Entry(form_frame, width=30)
        self.hotkey_entry.grid(row=2, column=1, sticky="we", padx=5, pady=5)
        ttk.Label(
            form_frame, text="Format: <modifier>+<key> (e.g., <ctrl>+<alt>+k)"
        ).grid(row=3, column=1, sticky="w", padx=5)

        # Command type - script or simple command
        ttk.Label(form_frame, text="Type:").grid(
            row=4, column=0, sticky="w", padx=5, pady=5
        )

        type_frame = ttk.Frame(form_frame)
        type_frame.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        self.is_script_var = tk.BooleanVar()
        ttk.Radiobutton(
            type_frame, text="Simple Command", variable=self.is_script_var, value=False
        ).pack(side="left", padx=5)
        ttk.Radiobutton(
            type_frame, text="Script", variable=self.is_script_var, value=True
        ).pack(side="left", padx=5)

        # Additional options
        options_frame = ttk.LabelFrame(form_frame, text="Advanced Options")
        options_frame.grid(row=5, column=0, columnspan=2, sticky="we", padx=5, pady=10)

        # Run as admin
        self.run_as_admin_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text="Run as Administrator", variable=self.run_as_admin_var
        ).pack(anchor="w", padx=10, pady=5)

        # Show window
        self.show_window_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Show command window", variable=self.show_window_var
        ).pack(anchor="w", padx=10, pady=5)

        # Save/Cancel buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, sticky="e", padx=5, pady=10)

        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(
            side="right", padx=5
        )
        ttk.Button(button_frame, text="Save", command=self.save_mapping).pack(
            side="right", padx=5
        )

        # Load existing mapping data if editing
        if self.edit_keyword is not None:
            self.keyword_entry.insert(0, self.edit_keyword)
            # Use self.mapping_details populated earlier
            self.command_entry.delete("1.0", tk.END) # Clear before inserting
            self.command_entry.insert(tk.END, self.mapping_details.get("command", ""))
            self.hotkey_entry.insert(0, self.mapping_details.get("hotkey", ""))
            self.is_script_var.set(self.mapping_details.get("is_script", False))
            self.run_as_admin_var.set(self.mapping_details.get("run_as_admin", False))
            self.show_window_var.set(self.mapping_details.get("show_window", True))

    def save_mapping(self):
        """Save the keyword mapping"""
        keyword = self.keyword_entry.get().strip()
        command = self.command_entry.get("1.0", tk.END).strip() # Get text from Text widget
        hotkey = self.hotkey_entry.get().strip()
        is_script = self.is_script_var.get()
        run_as_admin = self.run_as_admin_var.get()
        show_window = self.show_window_var.get()

        # Validate
        if not keyword:
            messagebox.showwarning("Invalid Input", "Please enter a keyword.")
            return

        if not command:
            messagebox.showwarning("Invalid Input", "Please enter a command or script.")
            return

        # Validate hotkey format
        if hotkey and "+" not in hotkey:
            messagebox.showwarning(
                "Invalid Format",
                "Hotkey should be in format: <modifier>+<key> (e.g., <ctrl>+<alt>+k)",
            )
            return

        # Create the mapping object
        mapping = {
            "command": command,
            "hotkey": hotkey if hotkey else None,
            "is_script": is_script,
            "run_as_admin": run_as_admin,
            "show_window": show_window,
        }

        # Check if we're modifying an existing keyword or adding a new one
        old_keyword = None
        if self.edit_keyword and "keyword" in self.edit_keyword:
            old_keyword = self.edit_keyword

        # If editing an existing keyword with a different name, remove the old one
        if (
            old_keyword
            and old_keyword != keyword
            and old_keyword in self.config_data.get("mappings", {})
        ):
            del self.config_data["mappings"][old_keyword]

        # Ensure mappings dict exists in instance config
        if "mappings" not in self.config_data: # Use self.config_data
            self.config_data["mappings"] = {}

        # If editing and keyword changed, remove old entry
        if self.edit_keyword and self.edit_keyword != keyword:
            if self.edit_keyword in self.config_data["mappings"]:
                del self.config_data["mappings"][self.edit_keyword]

        self.config_data["mappings"][keyword] = { # Use self.config_data
            "command": command,
            "is_script": is_script,
            "run_as_admin": run_as_admin,
            "show_window": show_window,
            "hotkey": hotkey if hotkey else "None", # Store "None" if empty
        }

        if config_module.save_config(self.config_data): # Pass the modified dict
            messagebox.showinfo("Mapping Saved", "Mapping saved successfully.", parent=self)
            self.result = True # Indicate success
            self.parent_app.update_keywords_list()
            # No need to restart hotkey listener here unless individual mapping hotkeys are implemented
            # self.parent_app.setup_hotkey_listener()
            self.destroy()
        else:
            messagebox.showerror("Save Error", "Failed to save the mapping. Please try again.")
