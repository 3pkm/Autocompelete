"""
Enhanced input dialog with auto-completion and smart suggestions.
Provides real-time command suggestions and history-based autocomplete.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Optional, Dict, Any

try:
    from .utils import CommandHistory
    from .error_handler import report_error, ErrorCategory
except ImportError:
    # Fallback for standalone execution
    from utils import CommandHistory
    from error_handler import report_error, ErrorCategory

logger = logging.getLogger(__name__)

class EnhancedInputDialog(tk.Toplevel):
    """Enhanced input dialog with autocomplete and suggestions"""

    def __init__(self, parent_app, mappings: Optional[Dict] = None):
        super().__init__(parent_app.tk_root)
        
        # Store references
        self.parent_app = parent_app
        
        # Get mappings from parent if available
        if mappings is None and hasattr(self.parent_app, 'app_config'):
            try:
                mappings = self.parent_app.app_config.get('mappings', {})
            except Exception as e:
                logger.error(f"Error getting mappings from parent app: {e}")
                mappings = {}
                
        self.mappings = mappings or {}
        
        # Initialize command history
        self.command_history = CommandHistory()
        
        # UI state
        self.suggestions_visible = False
        self.selected_suggestion_index = -1
        self.suggestions_list = []
        
        self.setup_dialog()
        self.create_widgets()
        self.setup_events()
        
        # Set custom icon for this dialog
        if hasattr(self.parent_app, 'set_dialog_icon'):
            self.parent_app.set_dialog_icon(self)
        
        # Apply theme
        if hasattr(self.parent_app, "apply_theme_to_toplevel"):
            self.parent_app.apply_theme_to_toplevel(self)
        
        # Focus and show
        self.focus_and_show()

    def setup_dialog(self):
        """Setup dialog properties"""
        self.title("Run Command - KeywordAutomator")
        self.geometry("400x60")  # Start small, will expand for suggestions
        self.resizable(True, False)
        self.transient(self.parent_app.tk_root)
        self.grab_set()
        
        # Center the dialog
        self.center_dialog()
        
        # Style the dialog
        self.configure(relief="solid", bd=1)
        
        # Bind escape to close
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-w>", lambda e: self.destroy())

    def center_dialog(self):
        """Center dialog on screen or parent"""
        self.update_idletasks()
        
        try:
            parent_x = self.parent_app.tk_root.winfo_x()
            parent_y = self.parent_app.tk_root.winfo_y()
            parent_width = self.parent_app.tk_root.winfo_width()
            parent_height = self.parent_app.tk_root.winfo_height()
            
            x = parent_x + (parent_width // 2) - (self.winfo_width() // 2)
            y = parent_y + (parent_height // 2) - (self.winfo_height() // 2)
        except:
            # Fallback to screen center
            x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
            y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        
        self.geometry(f"+{x}+{y}")

    def create_widgets(self):
        """Create dialog widgets"""
        # Main container
        self.main_frame = ttk.Frame(self, padding="8")
        self.main_frame.pack(fill="both", expand=True)
        
        # Input frame
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill="x")
        
        # Icon and label
        ttk.Label(input_frame, text="🔍", font=("Segoe UI", 12)).pack(side="left", padx=(0, 5))
        ttk.Label(input_frame, text="Run:", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        
        # Entry widget
        self.keyword_entry = ttk.Entry(
            input_frame, 
            font=("Segoe UI", 11),
            width=35
        )
        self.keyword_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Buttons frame (initially hidden)
        self.buttons_frame = ttk.Frame(input_frame)
        self.buttons_frame.pack(side="right")
        
        # Execute button
        self.execute_button = ttk.Button(
            self.buttons_frame,
            text="Run",
            command=self.execute_command,
            width=6
        )
        self.execute_button.pack(side="left", padx=2)
        
        # Cancel button  
        self.cancel_button = ttk.Button(
            self.buttons_frame,
            text="Cancel",
            command=self.destroy,
            width=6
        )
        self.cancel_button.pack(side="left")
        
        # Suggestions frame (initially hidden)
        self.suggestions_frame = ttk.Frame(self.main_frame)
        
        # Suggestions listbox
        self.suggestions_listbox = tk.Listbox(
            self.suggestions_frame,
            height=6,
            font=("Segoe UI", 10),
            selectmode=tk.SINGLE,
            relief="flat",
            bd=0,
            highlightthickness=0
        )
        
        # Suggestions scrollbar
        suggestions_scrollbar = ttk.Scrollbar(
            self.suggestions_frame,
            orient="vertical",
            command=self.suggestions_listbox.yview
        )
        self.suggestions_listbox.configure(yscrollcommand=suggestions_scrollbar.set)
        
        self.suggestions_listbox.pack(side="left", fill="both", expand=True)
        suggestions_scrollbar.pack(side="right", fill="y")
        
        # Help text
        self.help_label = ttk.Label(
            self.main_frame,
            text="💡 Type a keyword or press ↓ for suggestions",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        self.help_label.pack(pady=(5, 0))

    def setup_events(self):
        """Setup event bindings"""
        # Entry events
        self.keyword_entry.bind("<KeyRelease>", self.on_key_release)
        self.keyword_entry.bind("<Return>", self.on_enter)
        self.keyword_entry.bind("<Tab>", self.on_tab)
        self.keyword_entry.bind("<Down>", self.on_arrow_down)
        self.keyword_entry.bind("<Up>", self.on_arrow_up)
        self.keyword_entry.bind("<Control-space>", self.show_all_suggestions)
        
        # Listbox events
        self.suggestions_listbox.bind("<Double-Button-1>", self.on_suggestion_double_click)
        self.suggestions_listbox.bind("<Return>", self.on_suggestion_select)
        self.suggestions_listbox.bind("<Escape>", lambda e: self.hide_suggestions())
        
        # Window events
        self.bind("<FocusOut>", self.on_focus_out)

    def focus_and_show(self):
        """Focus the dialog and entry widget"""
        self.lift()
        self.attributes('-topmost', True)
        self.update()
        self.attributes('-topmost', False)
        self.keyword_entry.focus_set()

    def on_key_release(self, event):
        """Handle key release in entry widget"""
        if event.keysym in ['Up', 'Down', 'Return', 'Tab', 'Escape']:
            return
        
        current_text = self.keyword_entry.get()
        
        if len(current_text) >= 1:  # Show suggestions after 1 character
            self.update_suggestions(current_text)
        else:
            self.hide_suggestions()

    def on_enter(self, event):
        """Handle Enter key"""
        if self.suggestions_visible and self.selected_suggestion_index >= 0:
            # Use selected suggestion
            self.use_suggestion(self.selected_suggestion_index)
        else:
            # Execute current command
            self.execute_command()

    def on_tab(self, event):
        """Handle Tab key for autocomplete"""
        if self.suggestions_visible and self.suggestions_list:
            # Auto-complete with first suggestion
            self.use_suggestion(0)
            return "break"  # Prevent default tab behavior

    def on_arrow_down(self, event):
        """Handle down arrow key"""
        if not self.suggestions_visible:
            self.show_all_suggestions()
        else:
            self.select_next_suggestion()
        return "break"

    def on_arrow_up(self, event):
        """Handle up arrow key"""
        if self.suggestions_visible:
            self.select_previous_suggestion()
        return "break"

    def show_all_suggestions(self, event=None):
        """Show all available suggestions"""
        current_text = self.keyword_entry.get()
        self.update_suggestions(current_text or "", show_all=True)

    def update_suggestions(self, partial_text: str, show_all: bool = False):
        """Update suggestions based on partial text"""
        try:
            suggestions = []
            
            if show_all or not partial_text:
                # Show recent history and all keywords
                recent_commands = self.command_history.get_suggestions("", limit=5)
                all_keywords = list(self.mappings.keys())
                
                # Combine and deduplicate
                seen = set()
                for cmd in recent_commands + all_keywords:
                    if cmd not in seen:
                        suggestions.append(cmd)
                        seen.add(cmd)
                        if len(suggestions) >= 10:  # Limit suggestions
                            break
            else:
                # Get suggestions based on partial text
                history_suggestions = self.command_history.get_suggestions(partial_text, limit=5)
                
                # Get matching keywords
                keyword_matches = []
                partial_lower = partial_text.lower()
                
                for keyword in self.mappings.keys():
                    if keyword.lower().startswith(partial_lower):
                        keyword_matches.append(keyword)
                    elif partial_lower in keyword.lower():
                        keyword_matches.append(keyword)
                
                # Combine suggestions (history first, then keywords)
                seen = set()
                for cmd in history_suggestions + keyword_matches:
                    if cmd not in seen:
                        suggestions.append(cmd)
                        seen.add(cmd)
                        if len(suggestions) >= 8:
                            break
            
            self.show_suggestions(suggestions)
            
        except Exception as e:
            logger.error(f"Error updating suggestions: {e}")

    def show_suggestions(self, suggestions: List[str]):
        """Show suggestions in the listbox"""
        if not suggestions:
            self.hide_suggestions()
            return
        
        # Store suggestions
        self.suggestions_list = suggestions
        
        # Clear and populate listbox
        self.suggestions_listbox.delete(0, tk.END)
        
        for i, suggestion in enumerate(suggestions):
            # Add description if available
            display_text = suggestion
            if suggestion in self.mappings:
                mapping = self.mappings[suggestion]
                if isinstance(mapping, dict):
                    command = mapping.get('command', '')
                    if command and len(command) < 50:
                        display_text = f"{suggestion} → {command}"
                    else:
                        display_text = f"{suggestion} → {command[:47]}..."
                else:
                    if len(str(mapping)) < 50:
                        display_text = f"{suggestion} → {mapping}"
                    else:
                        display_text = f"{suggestion} → {str(mapping)[:47]}..."
            
            self.suggestions_listbox.insert(tk.END, display_text)
        
        # Show suggestions frame
        if not self.suggestions_visible:
            self.suggestions_frame.pack(fill="both", expand=True, pady=(5, 0))
            self.suggestions_visible = True
            
            # Resize dialog
            new_height = 60 + (len(suggestions) * 22) + 40
            current_geo = self.geometry()
            width = current_geo.split('x')[0]
            x_y = current_geo.split('+', 1)[1] if '+' in current_geo else "100+100"
            self.geometry(f"{width}x{new_height}+{x_y}")
        
        # Reset selection
        self.selected_suggestion_index = -1

    def hide_suggestions(self):
        """Hide suggestions"""
        if self.suggestions_visible:
            self.suggestions_frame.pack_forget()
            self.suggestions_visible = False
            self.selected_suggestion_index = -1
            
            # Resize dialog back to original size
            current_geo = self.geometry()
            width = current_geo.split('x')[0]
            x_y = current_geo.split('+', 1)[1] if '+' in current_geo else "100+100"
            self.geometry(f"{width}x60+{x_y}")

    def select_next_suggestion(self):
        """Select next suggestion in list"""
        if not self.suggestions_list:
            return
        
        # Clear previous selection
        self.suggestions_listbox.selection_clear(0, tk.END)
        
        # Select next
        self.selected_suggestion_index = (self.selected_suggestion_index + 1) % len(self.suggestions_list)
        self.suggestions_listbox.selection_set(self.selected_suggestion_index)
        self.suggestions_listbox.see(self.selected_suggestion_index)

    def select_previous_suggestion(self):
        """Select previous suggestion in list"""
        if not self.suggestions_list:
            return
        
        # Clear previous selection
        self.suggestions_listbox.selection_clear(0, tk.END)
        
        # Select previous
        if self.selected_suggestion_index <= 0:
            self.selected_suggestion_index = len(self.suggestions_list) - 1
        else:
            self.selected_suggestion_index -= 1
        
        self.suggestions_listbox.selection_set(self.selected_suggestion_index)
        self.suggestions_listbox.see(self.selected_suggestion_index)

    def use_suggestion(self, index: int):
        """Use suggestion at given index"""
        if 0 <= index < len(self.suggestions_list):
            suggestion = self.suggestions_list[index]
            self.keyword_entry.delete(0, tk.END)
            self.keyword_entry.insert(0, suggestion)
            self.hide_suggestions()
            
            # Execute immediately or wait for user
            # For now, let user press Enter to execute
            self.keyword_entry.focus_set()

    def on_suggestion_double_click(self, event):
        """Handle double-click on suggestion"""
        selection = self.suggestions_listbox.curselection()
        if selection:
            self.use_suggestion(selection[0])
            self.execute_command()  # Execute immediately on double-click

    def on_suggestion_select(self, event):
        """Handle Enter on suggestion"""
        selection = self.suggestions_listbox.curselection()
        if selection:
            self.use_suggestion(selection[0])
            self.execute_command()

    def on_focus_out(self, event):
        """Handle focus out (auto-hide after delay)"""
        # Only hide if focus went to another application
        if event.widget == self:
            self.after(500, self.check_focus_and_hide)

    def check_focus_and_hide(self):
        """Check focus and hide if appropriate"""
        try:
            if self.focus_get() is None:
                self.destroy()
        except:
            pass

    def execute_command(self):
        """Execute the entered command"""
        keyword = self.keyword_entry.get().strip()
        
        if not keyword:
            return
        
        try:
            # Add to history
            self.command_history.add_command(keyword)
            
            # Execute using parent app
            if hasattr(self.parent_app, 'execute_keyword'):
                success = self.parent_app.execute_keyword(keyword)
                if success:
                    self.destroy()
                    return
            
            # Fallback to mappings if parent app method not available
            if self.mappings and keyword in self.mappings:
                try:
                    from . import core
                except ImportError:
                    import core
                success = core.execute_command(keyword, self.mappings)
                if success:
                    self.destroy()
                    return
            
            # Command not found
            self.show_command_not_found_help(keyword)
            
        except Exception as e:
            logger.error(f"Error executing keyword '{keyword}': {e}")
            report_error(
                e,
                ErrorCategory.COMMAND_EXECUTION,
                "general",
                context={"keyword": keyword},
                user_message=f"Failed to execute '{keyword}'. Check the command configuration."
            )

    def show_command_not_found_help(self, keyword: str):
        """Show help when command is not found"""
        # Create help popup
        help_popup = tk.Toplevel(self)
        help_popup.title("Command Not Found")
        help_popup.geometry("350x200")
        help_popup.transient(self)
        help_popup.grab_set()
        
        # Apply theme
        if hasattr(self.parent_app, "apply_theme_to_toplevel"):
            self.parent_app.apply_theme_to_toplevel(help_popup)
        
        # Center popup
        help_popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (help_popup.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (help_popup.winfo_height() // 2)
        help_popup.geometry(f"+{x}+{y}")
        
        # Content
        main_frame = ttk.Frame(help_popup, padding="15")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(
            main_frame,
            text="❌ Command Not Found",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        ttk.Label(
            main_frame,
            text=f"The keyword '{keyword}' is not configured.",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(0, 10))
        
        ttk.Label(
            main_frame,
            text="Would you like to:",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(0, 5))
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill="x", pady=10)
        
        def add_keyword():
            help_popup.destroy()
            self.destroy()
            if hasattr(self.parent_app, 'show_mapping_dialog'):
                self.parent_app.show_mapping_dialog()
        
        def open_settings():
            help_popup.destroy()
            self.destroy()
            if hasattr(self.parent_app, 'show_settings'):
                self.parent_app.show_settings()
        
        ttk.Button(action_frame, text="Add This Keyword", command=add_keyword).pack(fill="x", pady=2)
        ttk.Button(action_frame, text="Open Settings", command=open_settings).pack(fill="x", pady=2)
        ttk.Button(action_frame, text="Cancel", command=help_popup.destroy).pack(fill="x", pady=2)
