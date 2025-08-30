import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import sys
import json
import logging
import time
from PIL import Image, ImageTk, ImageDraw

# Enhanced imports with better error handling
try:
    from . import config as config_module, core, tray_fix, hotkey
    from .utils import CommandHistory, CommandCategoryManager, ResourceManager, detect_common_applications
    from .error_handler import report_error, ErrorCategory, error_reporter
    from .documentation import DocumentationSystem
    from .onboarding import OnboardingWizard
    from .enhanced_input import EnhancedInputDialog
except ImportError as e:
    logging.error(f"Import error: {e}")
    # Fallback imports
    try:
        import src.config as config_module
        import src.core as core
        import src.tray_fix as tray_fix
        import src.hotkey as hotkey
        from src.utils import CommandHistory, CommandCategoryManager, ResourceManager, detect_common_applications
        from src.error_handler import report_error, ErrorCategory, error_reporter
        from src.documentation import DocumentationSystem
        from src.onboarding import OnboardingWizard
        from src.enhanced_input import EnhancedInputDialog
    except ImportError as e2:
        logging.error(f"Fallback import also failed: {e2}")
        # Final fallback
        try:
            import config as config_module
            import core
            import hotkey
            import tray_fix
        except ImportError:
            logging.error("Failed to import required modules. Check your installation.")
            messagebox.showerror(
                "Import Error",
                "Failed to import required modules. The application may not function correctly.",
            )

logger = logging.getLogger(__name__)

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
    def __init__(self, start_minimized=False):
        self.app_config = config_module.load_config()
        self.app_version = "1.0.0" # Added version
        self.github_repo_url = "https://github.com/3pkm/Autocompelete" # Updated URL
        
        # Initialize enhanced systems
        try:
            self.command_history = CommandHistory()
            self.category_manager = CommandCategoryManager()
            self.resource_manager = ResourceManager()
            self.documentation_system = DocumentationSystem(self)
            
            # Register cleanup
            self.resource_manager.register_cleanup(
                self.cleanup_application,
                "Main application cleanup"
            )
        except Exception as e:
            report_error(e, ErrorCategory.SYSTEM, "initialization",
                        user_message="Some advanced features may not work properly.")

        # Handle Tkinter initialization with graceful fallback
        try:
            # Clear problematic TCL environment variables
            import os
            if 'TCL_LIBRARY' in os.environ:
                del os.environ['TCL_LIBRARY']
            if 'TK_LIBRARY' in os.environ:
                del os.environ['TK_LIBRARY']
                
            self.tk_root = tk.Tk()
        except Exception as e:
            logger.error(f"Failed to initialize Tkinter: {e}")
            # Run console mode instead
            self._run_console_mode()
            return

        self.setup_main_window()

        self.stop_event = threading.Event()

        self.setup_hotkey_listener()

        if PYSTRAY_AVAILABLE:
            self.setup_system_tray()

        self.tk_root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        if self.app_config.get("launch_at_startup", False):
            config_module.set_launch_at_startup(True)

        # Handle startup behavior - always show window normally unless explicitly minimized via command line
        # Ignore config startup_minimized setting to avoid confusion (only honor command line parameter)
        if start_minimized:
            # Only minimize if explicitly requested via command line parameter
            self.after_id = self.tk_root.after(100, self.minimize_to_tray)
            logger.info("Application minimized to system tray (command line request)")
        else:
            # Always show the window normally for regular startup
            logger.info("Starting application normally - window will be visible")
            
            # Show onboarding wizard for new users
            if not self.app_config.get("wizard_completed", False) and not self.app_config.get("has_seen_welcome", False):
                # Always show the window first for new users, then run wizard
                logger.info("First time user detected - showing onboarding wizard")
                self.tk_root.deiconify()
                self.tk_root.after(500, self.show_onboarding_wizard)
            else:
                # For existing users, ensure the window is visible and stays visible
                # Force the window to be visible immediately after all setup is complete
                self.tk_root.after(10, self.ensure_window_visible)
                
                # Show a brief notification about the hotkey for users if configured
                if not self.app_config.get("startup_notification_shown", False):
                    self.tk_root.after(1000, self.show_startup_notification)

    def ensure_window_visible(self):
        """Ensure the main window is visible and brought to front"""
        try:
            # Multiple attempts to ensure window visibility
            self.tk_root.deiconify()  # Show window if iconified
            self.tk_root.state('normal')  # Set to normal state
            self.tk_root.lift()  # Bring to front
            self.tk_root.focus_force()  # Force focus
            self.tk_root.attributes('-topmost', True)  # Temporarily make topmost
            self.tk_root.update()  # Process pending events
            self.tk_root.after(100, lambda: self.tk_root.attributes('-topmost', False))  # Remove topmost after delay
            
            # Additional visibility enforcement
            self.tk_root.wm_attributes('-alpha', 1.0)  # Ensure full opacity
            
            # Center the window on screen if it's not visible
            self.tk_root.update_idletasks()
            x = (self.tk_root.winfo_screenwidth() // 2) - (self.tk_root.winfo_width() // 2)
            y = (self.tk_root.winfo_screenheight() // 2) - (self.tk_root.winfo_height() // 2)
            self.tk_root.geometry(f"+{x}+{y}")
            
            logger.info("Window visibility ensured - window should now be visible and centered")
        except Exception as e:
            logger.error(f"Error ensuring window visibility: {e}")
            # Fallback: at least try basic visibility
            try:
                self.tk_root.deiconify()
                self.tk_root.lift()
            except:
                pass

    def add_tooltip(self, widget, text):
        """Add a tooltip to a widget"""
        try:
            def on_enter(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                # Apply theme to tooltip
                if hasattr(self, 'current_theme') and self.current_theme == 'dark':
                    tooltip.configure(bg='#2d2d2d')
                    label_bg = '#2d2d2d'
                    label_fg = '#ffffff'
                else:
                    tooltip.configure(bg='#ffffe0')
                    label_bg = '#ffffe0'
                    label_fg = '#000000'
                
                label = tk.Label(tooltip, text=text, bg=label_bg, fg=label_fg,
                               relief='solid', borderwidth=1, wraplength=200,
                               justify='left', font=('Arial', 8))
                label.pack()
                widget.tooltip = tooltip
                
            def on_leave(event):
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
                    delattr(widget, 'tooltip')
                    
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
        except Exception as e:
            logger.warning(f"Failed to add tooltip: {e}")

    def add_context_help(self):
        """Add context help tooltips to UI elements"""
        try:
            if hasattr(self, 'keywords_tree'):
                self.add_tooltip(self.keywords_tree, 
                    "Your keyword mappings. Double-click to edit, right-click for options.")
            
            if hasattr(self, 'input_entry'):
                self.add_tooltip(self.input_entry, 
                    "Type keywords or commands here. Press Enter to execute.")
            
            if hasattr(self, 'add_button'):
                self.add_tooltip(self.add_button, 
                    "Add a new keyword mapping.")
            
            if hasattr(self, 'edit_button'):
                self.add_tooltip(self.edit_button, 
                    "Edit the selected keyword mapping.")
            
            if hasattr(self, 'delete_button'):
                self.add_tooltip(self.delete_button, 
                    "Delete the selected keyword mapping.")
                    
            if hasattr(self, 'category_filter_combo'):
                self.add_tooltip(self.category_filter_combo, 
                    "Filter keywords by category. Select 'All' to show everything.")
                    
            if hasattr(self, 'search_entry'):
                self.add_tooltip(self.search_entry, 
                    "Search through your keywords and commands.")
                    
        except Exception as e:
            logger.warning(f"Failed to add context help: {e}")

    def _run_console_mode(self):
        """Fallback console interface when GUI is not available"""
        print("\n" + "="*60)
        print("KEYWORD AUTOMATOR - CONSOLE MODE")
        print("="*60)
        print("GUI is not available due to system limitations.")
        print("Using console interface instead.")
        print()
        
        try:
            mappings = self.app_config.get("mappings", {})
            
            if not mappings:
                print("No keyword mappings found. Please configure via config file.")
                return
            
            print("Available commands:")
            for i, (keyword, mapping) in enumerate(mappings.items(), 1):
                command = mapping.get("command", "Unknown") if isinstance(mapping, dict) else str(mapping)
                print(f"  {i:2d}. {keyword:<20} -> {command[:50]}")
            
            print(f"\nTotal: {len(mappings)} commands available")
            print("Type keyword, number, or 'help' for more options:")
            
            while True:
                try:
                    choice = input("\nKeyword> ").strip()
                    
                    if choice.lower() in ['exit', 'quit', 'q']:
                        break
                    elif choice.lower() == 'help':
                        print("\nCommands:")
                        print("  help     - Show this help")
                        print("  list     - List all keywords")
                        print("  history  - Show command history")
                        print("  quit     - Exit application")
                        continue
                    elif choice.lower() == 'list':
                        for keyword in mappings.keys():
                            print(f"  {keyword}")
                        continue
                    elif choice.lower() == 'history':
                        if hasattr(self, 'command_history'):
                            recent = self.command_history.get_recent(10)
                            print(f"Recent commands: {recent}")
                        continue
                    
                    # Handle number or keyword
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(mappings):
                            keyword = list(mappings.keys())[idx]
                        else:
                            print(f"Invalid number. Choose 1-{len(mappings)}")
                            continue
                    else:
                        keyword = choice
                    
                    if keyword in mappings:
                        print(f"Executing: {keyword}")
                        import core
                        success = core.execute_command(keyword, mappings)
                        if success:
                            print("✓ Command executed successfully!")
                            if hasattr(self, 'command_history'):
                                self.command_history.add_command(keyword)
                        else:
                            print("✗ Command execution failed!")
                    else:
                        print(f"Unknown keyword: {keyword}")
                        similar = [k for k in mappings.keys() if choice.lower() in k.lower()]
                        if similar:
                            print(f"Did you mean: {', '.join(similar[:3])}")
                        
                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except EOFError:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    print(f"Error: {e}")
            
        except Exception as e:
            print(f"Console interface error: {e}")
            logger.error(f"Console mode failed: {e}")

    def cleanup_application(self):
        """Clean up application resources"""
        try:
            # Stop hotkey listener
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                self.hotkey_manager.stop_listener()
            
            # Stop system tray
            if hasattr(self, 'icon') and hasattr(self.icon, 'stop'):
                self.icon.stop()
            
            # Save any pending data
            if hasattr(self, 'command_history'):
                self.command_history.save_history()
            
            logger.info("Application cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def show_onboarding_wizard(self):
        """Show the onboarding wizard for new users"""
        try:
            wizard = OnboardingWizard(self)
        except Exception as e:
            report_error(e, ErrorCategory.UI, "wizard_error",
                        user_message="Failed to show setup wizard. You can configure manually in Settings.")
            # Fallback to welcome dialog
            self.show_welcome_dialog()

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

        # Try to configure background, but catch errors for widgets that don't support it
        try:
            toplevel.configure(bg=colors["bg"])
        except tk.TclError:
            # Some Toplevel widgets don't support bg configuration
            pass

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

        # Set window icon for both taskbar and title bar
        try:
            icon_path = self.resource_path("assets/icon.ico")
            # For Windows: set both iconbitmap and iconphoto for better compatibility
            self.tk_root.iconbitmap(icon_path)
            
            # Also set iconphoto for taskbar (works better on some Windows versions)
            try:
                from PIL import Image, ImageTk
                icon_image = Image.open(icon_path)
                # Resize to common icon sizes for better display
                icon_sizes = [(16, 16), (32, 32), (48, 48)]
                icon_photos = []
                for size in icon_sizes:
                    resized = icon_image.resize(size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(resized)
                    icon_photos.append(photo)
                
                # Set the iconphoto (this helps with taskbar icon)
                self.tk_root.iconphoto(True, *icon_photos)
                # Store references to prevent garbage collection
                self._icon_photos = icon_photos
                logger.info(f"Successfully set window icon from: {icon_path}")
            except Exception as e2:
                logger.warning(f"Failed to set iconphoto: {e2}")
                
        except Exception as e:
            logger.error(f"Error loading main window icon: {e}")
            # Try fallback icon creation
            self.set_fallback_window_icon()

    def set_fallback_window_icon(self):
        """Set a fallback icon when the main icon file is not available"""
        try:
            from PIL import Image, ImageDraw, ImageTk
            # Create a simple icon
            size = (32, 32)
            image = Image.new("RGBA", size, (52, 152, 219, 255))  # Blue background
            draw = ImageDraw.Draw(image)
            
            # Draw a simple "KA" text
            draw.text((8, 8), "KA", fill=(255, 255, 255, 255))
            
            # Convert to PhotoImage and set
            photo = ImageTk.PhotoImage(image)
            self.tk_root.iconphoto(True, photo)
            self._fallback_icon = photo  # Keep reference
            logger.info("Set fallback window icon")
        except Exception as e:
            logger.error(f"Failed to set fallback icon: {e}")

    def set_dialog_icon(self, dialog_window):
        """Set the custom icon for dialog windows"""
        try:
            icon_path = self.resource_path("assets/icon.ico")
            dialog_window.iconbitmap(icon_path)
            
            # Also set iconphoto for dialogs
            if hasattr(self, '_icon_photos') and self._icon_photos:
                dialog_window.iconphoto(True, *self._icon_photos)
            else:
                # Create icon photos if not already created
                from PIL import Image, ImageTk
                icon_image = Image.open(icon_path)
                photo = ImageTk.PhotoImage(icon_image.resize((32, 32), Image.Resampling.LANCZOS))
                dialog_window.iconphoto(True, photo)
                
        except Exception as e:
            logger.error(f"Error setting dialog icon: {e}")
            # Set fallback for dialog
            try:
                if hasattr(self, '_fallback_icon'):
                    dialog_window.iconphoto(True, self._fallback_icon)
            except:
                pass

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
        help_menu.add_command(label="Help & Documentation", command=self.open_documentation)
        help_menu.add_command(label="Getting Started", command=lambda: self.documentation_system.show_help_window("getting_started"))
        help_menu.add_command(label="Troubleshooting", command=lambda: self.documentation_system.show_help_window("troubleshooting"))
        help_menu.add_separator()
        help_menu.add_command(label="Setup Wizard", command=self.show_onboarding_wizard)
        help_menu.add_command(label="Check for Updates", command=self.check_updates)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_keyboard_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="View Error Log", command=self.view_error_log)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.tk_root.config(menu=menu_bar)

        # Create the main frame and content
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

        # Keywords frame with category support
        keywords_frame = ttk.LabelFrame(main_frame, text="Your Keywords", padding="10")
        keywords_frame.pack(fill="both", expand=True, pady=10)

        # Category filter frame
        filter_frame = ttk.Frame(keywords_frame)
        filter_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(filter_frame, text="Category:").pack(side="left", padx=(0, 5))
        
        self.category_filter_var = tk.StringVar(value="All")
        self.category_filter = ttk.Combobox(
            filter_frame, 
            textvariable=self.category_filter_var,
            state="readonly",
            width=20
        )
        self.category_filter.pack(side="left", padx=(0, 10))
        self.category_filter.bind("<<ComboboxSelected>>", self.on_category_filter_changed)

        # Search frame
        ttk.Label(filter_frame, text="Search:").pack(side="left", padx=(10, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side="left", padx=(0, 5))
        search_entry.bind("<KeyRelease>", self.on_search_changed)

        ttk.Button(filter_frame, text="Clear", command=self.clear_search).pack(side="left", padx=5)

        columns = ("Keyword", "Command", "Category", "Hotkey")
        self.keywords_tree = ttk.Treeview(
            keywords_frame, columns=columns, show="headings"
        )

        for col in columns:
            self.keywords_tree.heading(col, text=col)
            if col == "Command":
                self.keywords_tree.column(col, width=200)
            elif col == "Category":
                self.keywords_tree.column(col, width=120)
            elif col == "Hotkey":
                self.keywords_tree.column(col, width=100)
            else:
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
        
        # Add context help tooltips
        self.tk_root.after(100, self.add_context_help)
        
        # Ensure the window is visible and properly drawn
        self.tk_root.update_idletasks()
        self.tk_root.deiconify()
        self.tk_root.lift()
        self.tk_root.focus_force()

    def update_keywords_list(self):
        """Update the keywords treeview with current mappings and category support"""
        # Clear existing items
        for item in self.keywords_tree.get_children():
            self.keywords_tree.delete(item)

        mappings = self.app_config.get("mappings", {})
        
        # Update category filter options
        categories = set(["All"])
        for keyword, value in mappings.items():
            if isinstance(value, dict):
                category = value.get("category", "Other")
                categories.add(category)
        
        # Update category filter
        self.category_filter['values'] = sorted(list(categories))
        
        # Get current filters
        selected_category = self.category_filter_var.get()
        search_text = self.search_var.get().lower()
        
        # Populate filtered items
        for keyword, value in mappings.items():
            if isinstance(value, dict):
                command = value.get("command", "")
                hotkey = value.get("hotkey", "None")
                category = value.get("category", "Other")
            else:
                # Legacy support
                command = value
                hotkey = "None"
                category = "Other"

            # Apply filters
            if selected_category != "All" and category != selected_category:
                continue
                
            if search_text and search_text not in keyword.lower() and search_text not in command.lower():
                continue

            if len(command) > 50:
                command = command[:47] + "..."

            self.keywords_tree.insert("", "end", values=(keyword, command, category, hotkey))

    def on_category_filter_changed(self, event=None):
        """Handle category filter change"""
        self.update_keywords_list()

    def on_search_changed(self, event=None):
        """Handle search text change"""
        self.update_keywords_list()

    def clear_search(self):
        """Clear search filter"""
        self.search_var.set("")
        self.update_keywords_list()

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

    def show_welcome_dialog(self):
        """Show a welcome dialog for first-time users."""
        welcome_win = tk.Toplevel(self.tk_root)
        welcome_win.title("Welcome to Keyword Automator!")
        welcome_win.geometry("450x350")
        welcome_win.resizable(False, False)
        welcome_win.transient(self.tk_root) # Keep on top of main window
        welcome_win.grab_set() # Modal

        # Set custom icon for this dialog
        self.set_dialog_icon(welcome_win)

        self.apply_theme_to_toplevel(welcome_win)

        main_frame = ttk.Frame(welcome_win, padding="20")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Welcome to Keyword Automator!", font=("Arial", 16, "bold")).pack(pady=(0,10))
        
        welcome_text = ( 
            "Quickly launch apps, scripts, and commands using custom keywords.\n\n" \
            "Here's how to get started:\n\n" \
            "1. Add Keywords: Go to Settings (or click 'Add New Keyword') to define your keywords and the commands they run. You can also assign specific hotkeys!\n\n" \
            "2. Use Global Hotkey: Press Ctrl+Alt+K (default) to open the input dialog, type your keyword, and hit Enter.\n\n" \
            "3. System Tray: The app runs in the system tray for easy access. Right-click the icon for options.\n\n" \
            "Explore the settings to customize themes, startup behavior, and more!"
        )        
        
        text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10, relief="flat", state="disabled") 
        text_area.configure(font=("Arial", 10))
        text_area.pack(fill="both", expand=True, pady=(0,15))
        
        # Temporarily enable to insert text, then disable
        text_area.configure(state="normal")
        text_area.insert(tk.END, welcome_text)
        text_area.configure(state="disabled")

        # Apply theme to text_area explicitly if needed
        colors = THEME_COLORS.get(self.current_theme, THEME_COLORS["light"])
        text_area.configure(bg=colors["entry_bg"], fg=colors["fg"]) 

        def on_continue():
            self.app_config["has_seen_welcome"] = True
            config_module.save_config(self.app_config)
            welcome_win.destroy()

        continue_button = ttk.Button(main_frame, text="Got it! Let's Start", command=on_continue)
        continue_button.pack(pady=(10,0))

        welcome_win.protocol("WM_DELETE_WINDOW", on_continue) # Also mark as seen if closed
        self.tk_root.wait_window(welcome_win)

    def show_about_dialog(self):
        """Show the About dialog."""
        about_win = tk.Toplevel(self.tk_root)
        about_win.title("About Keyword Automator")
        about_win.geometry("400x250")
        about_win.resizable(False, False)
        about_win.transient(self.tk_root)
        about_win.grab_set()

        # Set custom icon for this dialog
        self.set_dialog_icon(about_win)

        self.apply_theme_to_toplevel(about_win)

        main_frame = ttk.Frame(about_win, padding="20")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Keyword Automator", font=("Arial", 16, "bold")).pack(pady=(0,5))
        ttk.Label(main_frame, text=f"Version: {self.app_version}").pack()
        ttk.Label(main_frame, text="Created by: [Prakhar Jaiswal/3pkm]").pack(pady=(10,0)) # TODO: Update this
        
        repo_label = ttk.Label(main_frame, text="GitHub Repository", foreground="blue", cursor="hand2")
        repo_label.pack(pady=(5,15))
        repo_label.bind("<Button-1>", lambda e: self.open_link(self.github_repo_url))

        # Simple way to make it look like a link
        f = tk.font.Font(repo_label, repo_label.cget("font"))
        f.configure(underline = True)
        repo_label.configure(font=f)

        ttk.Label(main_frame, text="A simple tool to boost your productivity.").pack()

        close_button = ttk.Button(main_frame, text="Close", command=about_win.destroy)
        close_button.pack(pady=(20,0))

    def open_link(self, url):
        """Open a URL in the default web browser."""
        try:
            import webbrowser
            webbrowser.open_new_tab(url)
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            messagebox.showerror("Error", f"Could not open link: {url}")

    def create_icon_image(self):
        """Create an icon image for the system tray"""
        try:
            # Try multiple possible icon paths for different deployment scenarios
            possible_paths = [
                # PyInstaller bundled resource
                self.resource_path(os.path.join("assets", "icon.ico")),
                # Alternative PyInstaller path
                self.resource_path("icon.ico"),
                # Development paths
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico"),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.ico"),
                # Direct path for development
                "assets/icon.ico",
                "icon.ico"
            ]

            for icon_path in possible_paths:
                if os.path.exists(icon_path):
                    logger.info(f"Loading tray icon from: {icon_path}")
                    try:
                        icon_image = Image.open(icon_path)
                        # Resize to appropriate size for system tray (16x16 or 32x32)
                        icon_image = icon_image.resize((32, 32), Image.Resampling.LANCZOS)
                        return icon_image
                    except Exception as e:
                        logger.warning(f"Failed to load tray icon from {icon_path}: {e}")
                        continue

            logger.warning(f"Icon not found in any of the expected paths: {possible_paths}")
        except Exception as e:
            logger.error(f"Error loading tray icon: {e}")
            
        # Create fallback icon with better design
        logger.info("Creating fallback tray icon")
        icon_size = (32, 32)
        image = Image.new("RGBA", icon_size, (52, 152, 219, 255))  # Blue background
        dc = ImageDraw.Draw(image)

        # Draw border
        dc.rectangle(
            (1, 1, icon_size[0] - 2, icon_size[1] - 2),
            fill=None,
            outline=(255, 255, 255, 255),
            width=2,
        )

        # Draw "KA" text for Keyword Automator
        try:
            # Try to use a system font
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        dc.text((8, 10), "KA", fill=(255, 255, 255, 255), font=font)

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
            # Hide the main window first
            self.tk_root.withdraw()
            
            # Stop any existing tray icon
            if hasattr(self, "icon") and hasattr(self.icon, "stop"):
                try:
                    self.icon.stop()
                    logger.info("Stopped previous system tray icon")
                except Exception as e:
                    logger.error(f"Error stopping previous tray icon: {e}")
            
            # Create new tray icon with better error handling for PyInstaller
            if PYSTRAY_AVAILABLE:
                try:
                    # Create the icon directly instead of using threading for better PyInstaller compatibility
                    self.icon = tray_fix.create_fresh_tray_icon(
                        self, self.create_icon_image(), "Keyword Automator"
                    )
                    
                    # Start the icon in a more PyInstaller-friendly way
                    import threading
                    def run_icon_safe():
                        try:
                            logger.info("Starting system tray icon...")
                            self.icon.run()
                        except Exception as e:
                            logger.error(f"Error running tray icon: {e}")
                            # Try fallback on error
                            self.create_fallback_tray()
                    
                    tray_thread = threading.Thread(target=run_icon_safe, daemon=True)
                    tray_thread.start()
                    
                    logger.info("Created new system tray icon (pystray)")
                    
                except Exception as e:
                    logger.error(f"Error creating pystray icon: {e}")
                    self.create_fallback_tray()
            else:
                logger.info("pystray not available, using fallback")
                self.create_fallback_tray()
                
            logger.info("Application minimized to system tray")
            
        except Exception as e:
            logger.error(f"Error in minimize_to_tray: {e}", exc_info=True)
            # If tray fails completely, show the window again
            try:
                self.tk_root.deiconify()
                messagebox.showerror(
                    "System Tray Error", 
                    "Could not minimize to system tray. The application will remain visible.\n\n"
                    f"Error: {str(e)}"
                )
            except:
                # Last resort - just print error
                print(f"Failed to minimize to tray: {e}")
    
    def create_fallback_tray(self):
        """Create a fallback tray implementation"""
        try:
            fallback_tray = tray_fix.FallbackSystemTray(self)
            fallback_tray.run_in_thread()
            self.icon = fallback_tray
            logger.info("Created fallback system tray icon")
        except Exception as e:
            logger.error(f"Even fallback tray failed: {e}")
            # Show a notification that the app is running
            try:
                import tkinter as tk
                from tkinter import messagebox
                messagebox.showinfo(
                    "Keyword Automator", 
                    "The application is running in the background.\n"
                    "Use Ctrl+Alt+K to access it."
                )
            except:
                pass

    def safe_minimize_to_tray(self):
        """Safely minimize to tray with user feedback if it fails"""
        try:
            self.minimize_to_tray()
        except Exception as e:
            logger.error(f"Failed to minimize to tray: {e}")
            # If tray fails, show a notification and keep window visible
            try:
                messagebox.showinfo(
                    "Keyword Automator", 
                    "System tray is not available.\n\n"
                    "The application will remain visible.\n"
                    f"Use the global hotkey {self.app_config.get('global_hotkey', '<ctrl>+<alt>+k')} "
                    "to quickly access the input dialog."
                )
            except:
                pass

    def show_startup_notification(self):
        """Show a brief notification about how to use the application"""
        try:
            from tkinter import messagebox
            global_hotkey = self.app_config.get('global_hotkey', '<ctrl>+<alt>+k')
            messagebox.showinfo(
                "Keyword Automator Ready", 
                f"Keyword Automator is ready to use!\n\n"
                f"• Press {global_hotkey} anytime to run commands\n"
                f"• Right-click the system tray icon for quick access\n"
                f"• Use the File menu to add new keywords\n\n"
                "This message will only show once."
            )
            # Mark that we've shown this notification
            self.app_config["startup_notification_shown"] = True
            config_module.save_config(self.app_config)
        except Exception as e:
            logger.error(f"Error showing startup notification: {e}")

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

    def show_simple_input_fallback(self):
        """Fallback to simple input dialog"""
        input_dialog = InputDialog(self.tk_root, self.app_config.get("mappings", {}))
        input_dialog.parent_app = self
        self.tk_root.wait_window(input_dialog)

    def execute_keyword(self, keyword):
        """Execute the command associated with a keyword"""
        logger.info(f"Attempting to execute keyword: {keyword}")
        try:
            mappings = self.app_config.get("mappings", {})
            if keyword not in mappings:
                logger.warning(f"Keyword '{keyword}' not found in mappings")
                self.status_var.set(f"Keyword not found: {keyword}")
                
                # Show enhanced error dialog with suggestions
                self.show_keyword_not_found_dialog(keyword)
                return False
            
            # Add to command history
            if hasattr(self, 'command_history'):
                self.command_history.add_command(keyword)
            
            success = core.execute_command(keyword, mappings)
            if success:
                self.status_var.set(f"Executed: {keyword}")
                return True
            else:
                self.status_var.set(f"Failed to execute: {keyword}")
                report_error(
                    RuntimeError(f"Command execution failed: {keyword}"),
                    ErrorCategory.COMMAND_EXECUTION,
                    "execution_failed",
                    context={"keyword": keyword, "mapping": mappings.get(keyword)},
                    user_message=f"Failed to execute '{keyword}'. Check the command configuration."
                )
                return False
        except Exception as e:
            logger.error(f"Error executing keyword '{keyword}': {e}", exc_info=True)
            self.status_var.set(f"Error: {e}")
            report_error(
                e,
                ErrorCategory.COMMAND_EXECUTION,
                "general",
                context={"keyword": keyword},
                user_message=f"An error occurred while executing '{keyword}'."
            )
            return False

    def show_keyword_not_found_dialog(self, keyword):
        """Show enhanced dialog when keyword is not found"""
        # Suggest similar keywords
        mappings = self.app_config.get("mappings", {})
        suggestions = []
        
        # Find similar keywords
        for existing_keyword in mappings.keys():
            if keyword.lower() in existing_keyword.lower() or existing_keyword.lower() in keyword.lower():
                suggestions.append(existing_keyword)
        
        # Show dialog with suggestions
        dialog = tk.Toplevel(self.tk_root)
        dialog.title("Keyword Not Found")
        dialog.geometry("400x300")
        dialog.transient(self.tk_root)
        dialog.grab_set()
        
        # Set custom icon for this dialog
        self.set_dialog_icon(dialog)
        
        if hasattr(self, "apply_theme_to_toplevel"):
            self.apply_theme_to_toplevel(dialog)
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Error message
        ttk.Label(main_frame, text=f"❌ Keyword '{keyword}' not found", 
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        if suggestions:
            ttk.Label(main_frame, text="Did you mean:", 
                     font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 5))
            
            suggestions_frame = ttk.Frame(main_frame)
            suggestions_frame.pack(fill="x", pady=(0, 15))
            
            for suggestion in suggestions[:5]:  # Show up to 5 suggestions
                def create_suggestion_callback(s):
                    return lambda: (dialog.destroy(), self.execute_keyword(s))
                
                ttk.Button(suggestions_frame, text=suggestion, 
                          command=create_suggestion_callback(suggestion)).pack(fill="x", pady=2)
        
        # Action buttons
        ttk.Label(main_frame, text="Or you can:", font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 5))
        
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill="x", pady=5)
        
        def add_keyword():
            dialog.destroy()
            self.show_mapping_dialog()
        
        def open_settings():
            dialog.destroy()
            self.show_settings()
        
        ttk.Button(action_frame, text="Add This Keyword", command=add_keyword).pack(fill="x", pady=2)
        ttk.Button(action_frame, text="Open Settings", command=open_settings).pack(fill="x", pady=2)
        ttk.Button(action_frame, text="Cancel", command=dialog.destroy).pack(fill="x", pady=2)

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

    def view_error_log(self):
        """View the error log file"""
        try:
            if hasattr(error_reporter, 'log_file_path') and os.path.exists(error_reporter.log_file_path):
                if sys.platform == 'win32':
                    os.startfile(error_reporter.log_file_path)
                else:
                    import subprocess
                    subprocess.run(['open', error_reporter.log_file_path])
            else:
                messagebox.showinfo("No Log File", "No error log file found.")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open log file: {e}")

    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts help dialog"""
        try:
            shortcuts_window = tk.Toplevel(self.tk_root)
            shortcuts_window.title("Keyboard Shortcuts")
            shortcuts_window.geometry("500x400")
            shortcuts_window.resizable(True, True)
            shortcuts_window.transient(self.tk_root)
            shortcuts_window.grab_set()
            
            # Set custom icon for this dialog
            self.set_dialog_icon(shortcuts_window)
            
            # Apply theme
            if hasattr(self, "apply_theme_to_toplevel"):
                self.apply_theme_to_toplevel(shortcuts_window)
            
            # Center the window
            shortcuts_window.geometry("500x400+{}+{}".format(
                self.tk_root.winfo_x() + 50,
                self.tk_root.winfo_y() + 50
            ))
            
            # Create main frame with scrollbar
            main_frame = ttk.Frame(shortcuts_window, padding="10")
            main_frame.pack(fill="both", expand=True)
            
            # Title
            title_label = ttk.Label(main_frame, text="Keyboard Shortcuts", 
                                  font=("Arial", 14, "bold"))
            title_label.pack(pady=(0, 10))
            
            # Create scrollable text widget
            text_frame = ttk.Frame(main_frame)
            text_frame.pack(fill="both", expand=True)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, height=15, width=50)
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Shortcuts content
            shortcuts_text = """GLOBAL SHORTCUTS:
• Application hotkey (configurable): Show/Hide Keyword Automator
• Escape: Close current dialog
• F1: Open help documentation

MAIN WINDOW:
• Enter: Execute command in input field
• Ctrl+N: Add new keyword mapping
• Ctrl+E: Edit selected keyword
• Delete: Delete selected keyword
• Ctrl+F: Focus on search box
• Ctrl+R: Refresh keywords list
• Ctrl+T: Toggle between light/dark theme
• Ctrl+S: Open settings
• Ctrl+Q: Quit application

KEYWORD LIST:
• Double-click: Edit keyword mapping
• Right-click: Open context menu
• Arrow keys: Navigate through list
• Space: Run selected keyword
• F2: Rename selected keyword

INPUT FIELD:
• Tab: Show autocomplete suggestions
• Arrow up/down: Navigate command history
• Ctrl+L: Clear input field
• Ctrl+A: Select all text

MAPPING DIALOG:
• Tab: Move between fields
• Alt+A: Auto-detect category
• Ctrl+S: Save mapping
• Escape: Cancel and close

CATEGORY FILTERING:
• Ctrl+1-9: Switch to category 1-9
• Ctrl+0: Show all categories
• Ctrl+Shift+C: Clear category filter

TIPS:
• Use partial keyword matches for quick access
• Commands are executed in the background by default
• Use the "Run as Administrator" option for system commands
• Categories help organize your commands efficiently
"""
            
            text_widget.insert("1.0", shortcuts_text)
            text_widget.configure(state="disabled")
            
            # Apply theme to text widget
            if hasattr(self, "current_theme") and self.current_theme == "dark":
                text_widget.configure(bg="#2d2d2d", fg="#ffffff", 
                                    insertbackground="#ffffff")
            
            # Close button
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=(10, 0))
            
            ttk.Button(button_frame, text="Close", 
                      command=shortcuts_window.destroy).pack()
            
            # Focus on window
            shortcuts_window.focus_set()
            
        except Exception as e:
            logger.error(f"Failed to show keyboard shortcuts: {e}")
            messagebox.showerror("Error", f"Failed to show keyboard shortcuts: {e}")

    def open_documentation(self):
        """Open the enhanced documentation system"""
        try:
            self.documentation_system.show_help_window()
        except Exception as e:
            report_error(e, ErrorCategory.UI, "documentation_error",
                        user_message="Failed to open documentation. Using fallback help.")
            self.show_built_in_docs()

    def show_built_in_docs(self):
        """Show built-in documentation"""
        docs_window = tk.Toplevel(self.tk_root)
        docs_window.title("Keyword Automator Documentation")
        docs_window.geometry("700x500")
        docs_window.transient(self.tk_root)

        # Set custom icon for this dialog
        self.set_dialog_icon(docs_window)

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
        """Show the enhanced keyword input dialog"""
        # Restore window if minimized
        self.restore_from_tray()

        try:
            # Create and show enhanced input dialog
            input_dialog = EnhancedInputDialog(self, self.app_config.get("mappings", {}))
            
            # Wait for the dialog to close
            self.tk_root.wait_window(input_dialog)
            
        except Exception as e:
            # Fallback to simple input dialog
            logger.error(f"Failed to show enhanced input dialog: {e}")
            report_error(e, ErrorCategory.UI, "dialog_error", 
                        user_message="Using simple input dialog as fallback.")
            self.show_simple_input_fallback()

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
        dialog = MappingDialog(self, dialog_title, initial)
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
            try:
                # Use resource manager for cleanup
                if hasattr(self, 'resource_manager'):
                    self.resource_manager.cleanup_all()
                else:
                    # Fallback cleanup
                    self.cleanup_application()
                
                # Stop all threads
                self.stop_event.set()

                # Exit the application
                self.tk_root.quit()
                
            except Exception as e:
                logger.error(f"Error during application exit: {e}")
                # Force exit if cleanup fails
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

        # Set custom icon for this dialog
        if hasattr(self.parent_app, 'set_dialog_icon'):
            self.parent_app.set_dialog_icon(self)

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

        # Set custom icon for this dialog
        if hasattr(self.parent_app, 'set_dialog_icon'):
            self.parent_app.set_dialog_icon(self)

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

        # Set custom icon for this dialog
        if hasattr(self.parent_app, 'set_dialog_icon'):
            self.parent_app.set_dialog_icon(self)

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

        # Category
        ttk.Label(form_frame, text="Category:").grid(
            row=4, column=0, sticky="w", padx=5, pady=5
        )
        category_frame = ttk.Frame(form_frame)
        category_frame.grid(row=4, column=1, sticky="we", padx=5, pady=5)
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, width=25)
        self.category_combo.pack(side="left", fill="x", expand=True)
        
        # Get existing categories from parent app
        existing_categories = set()
        if hasattr(self.parent_app, 'category_manager'):
            existing_categories = self.parent_app.category_manager.get_all_categories()
        elif 'mappings' in self.config_data:
            for mapping in self.config_data['mappings'].values():
                if 'category' in mapping and mapping['category']:
                    existing_categories.add(mapping['category'])
        
        # Set combobox values
        self.category_combo['values'] = sorted(list(existing_categories))
        
        # Auto-detect button
        ttk.Button(category_frame, text="Auto", 
                  command=self.auto_detect_category, width=6).pack(side="right", padx=(5,0))

        # Command type - script or simple command
        ttk.Label(form_frame, text="Type:").grid(
            row=5, column=0, sticky="w", padx=5, pady=5
        )

        type_frame = ttk.Frame(form_frame)
        type_frame.grid(row=5, column=1, sticky="w", padx=5, pady=5)

        self.is_script_var = tk.BooleanVar()
        ttk.Radiobutton(
            type_frame, text="Simple Command", variable=self.is_script_var, value=False
        ).pack(side="left", padx=5)
        ttk.Radiobutton(
            type_frame, text="Script", variable=self.is_script_var, value=True
        ).pack(side="left", padx=5)

        # Additional options
        options_frame = ttk.LabelFrame(form_frame, text="Advanced Options")
        options_frame.grid(row=6, column=0, columnspan=2, sticky="we", padx=5, pady=10)

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
        button_frame.grid(row=7, column=0, columnspan=2, sticky="e", padx=5, pady=10)

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
            self.category_var.set(self.mapping_details.get("category", ""))
            self.is_script_var.set(self.mapping_details.get("is_script", False))
            self.run_as_admin_var.set(self.mapping_details.get("run_as_admin", False))
            self.show_window_var.set(self.mapping_details.get("show_window", True))

    def auto_detect_category(self):
        """Auto-detect category based on command"""
        command = self.command_entry.get("1.0", tk.END).strip()
        if not command:
            messagebox.showinfo("Auto-detect", "Please enter a command first.", parent=self)
            return
        
        # Use category manager if available
        if hasattr(self.parent_app, 'category_manager'):
            try:
                # Use detect_category method with keyword and command
                keyword = self.keyword_entry.get().strip() or "temp"
                category = self.parent_app.category_manager.detect_category(keyword, command)
                if category:
                    self.category_var.set(category)
                    messagebox.showinfo("Category Detected", f"Category set to: {category}", parent=self)
                else:
                    messagebox.showinfo("Auto-detect", "Could not detect category automatically.", parent=self)
            except Exception as e:
                messagebox.showwarning("Error", f"Failed to auto-detect category: {e}", parent=self)
        else:
            # Fallback basic detection
            command_lower = command.lower()
            if any(app in command_lower for app in ['notepad', 'word', 'excel', 'powerpoint']):
                category = "Applications"
            elif any(cmd in command_lower for cmd in ['dir', 'ls', 'cd', 'mkdir']):
                category = "File Management"
            elif any(net in command_lower for net in ['ping', 'curl', 'wget']):
                category = "Network"
            else:
                category = "General"
            
            self.category_var.set(category)
            messagebox.showinfo("Category Detected", f"Category set to: {category}", parent=self)

    def save_mapping(self):
        """Save the keyword mapping"""
        keyword = self.keyword_entry.get().strip()
        command = self.command_entry.get("1.0", tk.END).strip() # Get text from Text widget
        hotkey = self.hotkey_entry.get().strip()
        category = self.category_var.get().strip()
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

        # Validate hotkey format if provided
        if hotkey:
            # Use hotkey validator if available
            if hasattr(self.parent_app, 'resource_manager') and hasattr(self.parent_app.resource_manager, 'hotkey_validator'):
                try:
                    is_valid, error_msg = self.parent_app.resource_manager.hotkey_validator.validate_hotkey_format(hotkey)
                    if not is_valid:
                        messagebox.showwarning("Invalid Hotkey", error_msg, parent=self)
                        return
                except Exception:
                    # Fallback validation
                    if "+" not in hotkey:
                        messagebox.showwarning(
                            "Invalid Format",
                            "Hotkey should be in format: <modifier>+<key> (e.g., <ctrl>+<alt>+k)",
                        )
                        return
            else:
                # Basic validation
                if "+" not in hotkey:
                    messagebox.showwarning(
                        "Invalid Format",
                        "Hotkey should be in format: <modifier>+<key> (e.g., <ctrl>+<alt>+k)",
                    )
                    return

        # Auto-detect category if not provided
        if not category and hasattr(self.parent_app, 'category_manager'):
            try:
                category = self.parent_app.category_manager.detect_category(keyword, command) or "General"
            except Exception:
                category = "General"
        elif not category:
            category = "General"

        # Create the mapping object
        mapping = {
            "command": command,
            "hotkey": hotkey if hotkey else None,
            "category": category,
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
            "category": category,
            "is_script": is_script,
            "run_as_admin": run_as_admin,
            "show_window": show_window,
            "hotkey": hotkey if hotkey else "None", # Store "None" if empty
        }

        if hasattr(self.parent_app, 'category_manager'):
            try:
                self.parent_app.category_manager.add_command_to_category(keyword, category)
            except Exception as e:
                logger.warning(f"Failed to update category manager: {e}")

        if config_module.save_config(self.config_data):
            messagebox.showinfo("Mapping Saved", "Mapping saved successfully.", parent=self)
            self.result = True
            self.parent_app.update_keywords_list()

            self.destroy()
        else:
            messagebox.showerror("Save Error", "Failed to save the mapping. Please try again.")
