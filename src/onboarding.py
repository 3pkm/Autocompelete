"""
User onboarding and setup wizard for KeywordAutomator.
Provides guided setup with application detection and sample configurations.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import logging
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)

try:
    from .utils import detect_common_applications, CommandCategoryManager
    from .error_handler import report_error, ErrorCategory
except ImportError:
    # Fallback for standalone execution
    from utils import detect_common_applications, CommandCategoryManager
    from error_handler import report_error, ErrorCategory

class OnboardingWizard(tk.Toplevel):
    """Comprehensive setup wizard for new users"""
    
    def __init__(self, parent_app):
        super().__init__(parent_app.tk_root)
        self.parent_app = parent_app
        self.current_step = 0
        self.total_steps = 5
        self.wizard_data = {}
        
        try:
            self.setup_window()
            self.create_widgets()
            self.show_step(0)
            
            # Apply theme
            if hasattr(parent_app, "apply_theme_to_toplevel"):
                parent_app.apply_theme_to_toplevel(self)
                
            logger.info("Onboarding wizard initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing onboarding wizard: {e}")
            # Show a simple error message and close
            try:
                from tkinter import messagebox
                messagebox.showerror("Wizard Error", 
                                   f"Failed to initialize setup wizard: {e}\n\n"
                                   "You can configure the application manually through the Settings menu.")
            except:
                pass
            self.destroy()
    
    def setup_window(self):
        """Setup wizard window"""
        self.title("KeywordAutomator Setup Wizard")
        self.geometry("700x550")
        self.resizable(False, False)
        self.transient(self.parent_app.tk_root)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Prevent closing during setup
        self.protocol("WM_DELETE_WINDOW", self.on_close_attempt)
    
    def create_widgets(self):
        """Create wizard interface"""
        # Header frame
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=20, pady=10)
        
        self.title_label = ttk.Label(
            header_frame, 
            text="Welcome to KeywordAutomator!",
            font=("Segoe UI", 16, "bold")
        )
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = ttk.Label(
            header_frame,
            text="Let's set up your productivity shortcuts",
            font=("Segoe UI", 10)
        )
        self.subtitle_label.pack(anchor="w", pady=(0, 10))
        
        # Progress bar
        progress_frame = ttk.Frame(header_frame)
        progress_frame.pack(fill="x", pady=(0, 15))
        
        # Progress bar with better visibility
        self.progress = ttk.Progressbar(
            progress_frame,
            length=500,
            mode='determinate',
            style="TProgressbar"
        )
        self.progress.pack(anchor="w", pady=(0, 5))
        
        # Progress label with step information
        self.progress_label = ttk.Label(
            progress_frame, 
            text="Step 1 of 5", 
            font=("Segoe UI", 10, "bold")
        )
        self.progress_label.pack(anchor="w")
        
        # Step description label
        self.step_desc_label = ttk.Label(
            progress_frame,
            text="Welcome and Introduction",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        self.step_desc_label.pack(anchor="w")
        
        # Content frame (will be replaced for each step)
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Navigation frame
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill="x", padx=20, pady=15)
        
        # Left side buttons
        left_nav = ttk.Frame(nav_frame)
        left_nav.pack(side="left")
        
        self.prev_button = ttk.Button(
            left_nav, 
            text="← Previous", 
            command=self.previous_step,
            width=12
        )
        self.prev_button.pack(side="left")
        
        # Right side buttons  
        right_nav = ttk.Frame(nav_frame)
        right_nav.pack(side="right")
        
        self.skip_button = ttk.Button(
            right_nav, 
            text="Skip Setup", 
            command=self.skip_setup,
            width=12
        )
        self.skip_button.pack(side="right", padx=(0, 10))
        
        self.next_button = ttk.Button(
            right_nav, 
            text="Next →", 
            command=self.next_step,
            width=12,
            style="Accent.TButton"  # Make it more prominent
        )
        self.next_button.pack(side="right")
    
    def show_step(self, step: int):
        """Show specific wizard step"""
        self.current_step = step
        
        # Step descriptions
        step_descriptions = [
            "Welcome and Introduction",
            "Detecting Applications",
            "Organizing Categories", 
            "Configuring Hotkeys",
            "Setup Complete"
        ]
        
        # Update progress bar with animation
        progress_value = (step / (self.total_steps - 1)) * 100
        self.progress.config(value=progress_value)
        
        # Update labels
        self.progress_label.config(text=f"Step {step + 1} of {self.total_steps}")
        if hasattr(self, 'step_desc_label'):
            self.step_desc_label.config(text=step_descriptions[step])
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Show appropriate step
        if step == 0:
            self.show_welcome_step()
        elif step == 1:
            self.show_detection_step()
        elif step == 2:
            self.show_categories_step()
        elif step == 3:
            self.show_hotkeys_step()
        elif step == 4:
            self.show_completion_step()
        
        # Update navigation buttons
        self.prev_button.config(state="disabled" if step == 0 else "normal")
        
        # Update next button text and enable state
        if step == self.total_steps - 1:
            self.next_button.config(text="Finish Setup")
        else:
            self.next_button.config(text="Next →")
        
        # Always enable next button - validation happens on click
        self.next_button.config(state="normal")
    
    def show_welcome_step(self):
        """Step 0: Welcome and introduction"""
        self.title_label.config(text="Welcome to KeywordAutomator!")
        self.subtitle_label.config(text="Let's set up your productivity shortcuts")
        
        content = ttk.Frame(self.content_frame)
        content.pack(fill="both", expand=True)
        
        # Welcome text
        welcome_text = """
KeywordAutomator helps you work faster by creating custom shortcuts for:

• Opening applications quickly
• Running scripts and commands  
• Launching websites and tools
• Automating repetitive tasks

This wizard will help you:
1. Detect installed applications
2. Set up useful keywords
3. Configure hotkeys and categories
4. Create your first shortcuts

The whole process takes just a few minutes!
        """
        
        text_widget = tk.Text(
            content,
            wrap=tk.WORD,
            height=15,
            font=("Segoe UI", 10),
            relief="flat",
            bg=self.cget("bg")
        )
        text_widget.pack(fill="both", expand=True, pady=10)
        text_widget.insert(tk.END, welcome_text.strip())
        text_widget.config(state="disabled")
        
        # Feature highlights
        features_frame = ttk.LabelFrame(content, text="Key Features")
        features_frame.pack(fill="x", pady=10)
        
        features = [
            ("🚀", "Quick Access", "Press Ctrl+Alt+K anytime to run commands"),
            ("⌨️", "Custom Hotkeys", "Assign direct hotkeys to your favorites"),
            ("📁", "Smart Categories", "Automatic organization by app type"),
            ("🔧", "Script Support", "Run Python, PowerShell, and batch scripts")
        ]
        
        for i, (icon, title, desc) in enumerate(features):
            feature_frame = ttk.Frame(features_frame)
            feature_frame.pack(fill="x", padx=10, pady=5)
            
            ttk.Label(feature_frame, text=icon, font=("Segoe UI", 12)).pack(side="left")
            ttk.Label(feature_frame, text=title, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(10, 5))
            ttk.Label(feature_frame, text=desc, font=("Segoe UI", 9)).pack(side="left")
    
    def show_detection_step(self):
        """Step 1: Application detection"""
        self.title_label.config(text="Detecting Your Applications")
        self.subtitle_label.config(text="We'll find common applications and suggest keywords")
        
        content = ttk.Frame(self.content_frame)
        content.pack(fill="both", expand=True)
        
        # Detection status
        status_frame = ttk.Frame(content)
        status_frame.pack(fill="x", pady=10)
        
        ttk.Label(status_frame, text="Scanning for installed applications...", 
                 font=("Segoe UI", 10)).pack(anchor="w")
        
        # Progress for detection
        detect_progress = ttk.Progressbar(status_frame, mode='indeterminate')
        detect_progress.pack(fill="x", pady=5)
        detect_progress.start()
        
        # Results frame
        results_frame = ttk.LabelFrame(content, text="Found Applications")
        results_frame.pack(fill="both", expand=True, pady=10)
        
        # Applications tree
        columns = ("app", "keyword", "category", "include")
        self.apps_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=12)
        
        self.apps_tree.heading("app", text="Application")
        self.apps_tree.heading("keyword", text="Suggested Keyword")
        self.apps_tree.heading("category", text="Category")
        self.apps_tree.heading("include", text="Include")
        
        self.apps_tree.column("app", width=200)
        self.apps_tree.column("keyword", width=120)
        self.apps_tree.column("category", width=120)
        self.apps_tree.column("include", width=60)
        
        # Scrollbar
        apps_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.apps_tree.yview)
        self.apps_tree.configure(yscrollcommand=apps_scrollbar.set)
        
        self.apps_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        apps_scrollbar.pack(side="right", fill="y", pady=5)
        
        # Detect applications
        self.after(1000, lambda: self.detect_applications(detect_progress))
        
        # Instructions
        ttk.Label(content, text="💡 Tip: Uncheck applications you don't want to add as keywords",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=5)
    
    def detect_applications(self, progress_bar):
        """Detect and populate applications"""
        try:
            progress_bar.stop()
            progress_bar.destroy()
            
            # Get detected applications
            detected_apps = detect_common_applications()
            category_manager = CommandCategoryManager()
            
            # Populate tree
            for keyword, app_info in detected_apps.items():
                # Determine category
                category = category_manager.detect_category(keyword, app_info['command'])
                
                self.apps_tree.insert("", "end", values=(
                    app_info.get('description', keyword.title()),
                    keyword,
                    category,
                    "✓"  # Include by default
                ))
            
            # Store detected apps for later use
            self.wizard_data['detected_apps'] = detected_apps
            
            # Enable interaction
            self.apps_tree.bind("<Button-1>", self.toggle_app_selection)
            
        except Exception as e:
            report_error(e, ErrorCategory.SYSTEM, "app_detection",
                        user_message="Failed to detect applications. You can add them manually later.")
    
    def toggle_app_selection(self, event):
        """Toggle application selection in tree"""
        item = self.apps_tree.identify('item', event.x, event.y)
        if item:
            values = list(self.apps_tree.item(item, "values"))
            if len(values) >= 4:
                # Toggle include status
                values[3] = "✗" if values[3] == "✓" else "✓"
                self.apps_tree.item(item, values=values)
    
    def show_categories_step(self):
        """Step 2: Category organization"""
        self.title_label.config(text="Organize with Categories")
        self.subtitle_label.config(text="Categories help organize your keywords by purpose")
        
        content = ttk.Frame(self.content_frame)
        content.pack(fill="both", expand=True)
        
        # Categories explanation
        explanation_frame = ttk.Frame(content)
        explanation_frame.pack(fill="x", pady=10)
        
        explanation_text = """
Categories automatically group your keywords by type:

• Web & Browsers: Chrome, Firefox, websites
• System & Utilities: Calculator, Notepad, File Explorer  
• Development: VS Code, Git, programming tools
• Office & Productivity: Word, Excel, Teams
• Media & Entertainment: Spotify, VLC, games
• Scripts & Automation: Custom scripts and tools
        """
        
        ttk.Label(explanation_frame, text=explanation_text.strip(), 
                 font=("Segoe UI", 10)).pack(anchor="w")
        
        # Category preview
        preview_frame = ttk.LabelFrame(content, text="Category Preview")
        preview_frame.pack(fill="both", expand=True, pady=10)
        
        # Create category tree
        self.category_tree = ttk.Treeview(preview_frame, show="tree", height=10)
        cat_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=cat_scrollbar.set)
        
        self.category_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        cat_scrollbar.pack(side="right", fill="y", pady=5)
        
        # Populate with detected apps organized by category
        self.populate_category_preview()
        
        # Options frame
        options_frame = ttk.Frame(content)
        options_frame.pack(fill="x", pady=10)
        
        self.auto_categorize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Enable automatic categorization",
            variable=self.auto_categorize_var
        ).pack(anchor="w")
        
        self.show_icons_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Show category icons and colors",
            variable=self.show_icons_var
        ).pack(anchor="w")
    
    def populate_category_preview(self):
        """Populate category preview tree"""
        if 'detected_apps' not in self.wizard_data:
            return
        
        category_manager = CommandCategoryManager()
        categories = {}
        
        # Group apps by category
        for item in self.apps_tree.get_children():
            values = self.apps_tree.item(item, "values")
            if len(values) >= 4 and values[3] == "✓":  # Only included apps
                app_name, keyword, category, _ = values
                if category not in categories:
                    categories[category] = []
                categories[category].append((keyword, app_name))
        
        # Add to tree
        for category_name, apps in sorted(categories.items()):
            cat_item = self.category_tree.insert("", "end", text=f"📁 {category_name} ({len(apps)})")
            
            for keyword, app_name in sorted(apps):
                self.category_tree.insert(cat_item, "end", text=f"  → {keyword}: {app_name}")
    
    def show_hotkeys_step(self):
        """Step 3: Hotkey configuration"""
        self.title_label.config(text="Configure Hotkeys")
        self.subtitle_label.config(text="Set up global and individual hotkeys")
        
        content = ttk.Frame(self.content_frame)
        content.pack(fill="both", expand=True)
        
        # Global hotkey section
        global_frame = ttk.LabelFrame(content, text="Global Activation Hotkey")
        global_frame.pack(fill="x", pady=10)
        
        ttk.Label(global_frame, text="This hotkey opens the keyword input dialog from anywhere:",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=5)
        
        hotkey_frame = ttk.Frame(global_frame)
        hotkey_frame.pack(fill="x", padx=10, pady=5)
        
        self.global_hotkey_var = tk.StringVar(value="<ctrl>+<alt>+k")
        hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.global_hotkey_var, width=20)
        hotkey_entry.pack(side="left", padx=(0, 10))
        
        ttk.Button(hotkey_frame, text="Test", command=self.test_global_hotkey).pack(side="left")
        
        ttk.Label(global_frame, text="Format: <modifier>+<key> (e.g., <ctrl>+<alt>+k)",
                 font=("Segoe UI", 9), foreground="gray").pack(anchor="w", padx=10, pady=5)
        
        # Individual hotkeys section
        individual_frame = ttk.LabelFrame(content, text="Individual Command Hotkeys")
        individual_frame.pack(fill="both", expand=True, pady=10)
        
        ttk.Label(individual_frame, text="Assign direct hotkeys to your most-used commands:",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=5)
        
        # Hotkey assignment tree
        hotkey_columns = ("keyword", "app", "hotkey")
        self.hotkey_tree = ttk.Treeview(individual_frame, columns=hotkey_columns, show="headings", height=8)
        
        self.hotkey_tree.heading("keyword", text="Keyword")
        self.hotkey_tree.heading("app", text="Application")
        self.hotkey_tree.heading("hotkey", text="Hotkey")
        
        self.hotkey_tree.column("keyword", width=100)
        self.hotkey_tree.column("app", width=200)
        self.hotkey_tree.column("hotkey", width=150)
        
        hotkey_scrollbar = ttk.Scrollbar(individual_frame, orient="vertical", command=self.hotkey_tree.yview)
        self.hotkey_tree.configure(yscrollcommand=hotkey_scrollbar.set)
        
        self.hotkey_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        hotkey_scrollbar.pack(side="right", fill="y", pady=5)
        
        # Populate with selected apps
        self.populate_hotkey_assignments()
        
        # Hotkey assignment controls
        hotkey_controls = ttk.Frame(individual_frame)
        hotkey_controls.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(hotkey_controls, text="Assign Hotkey", command=self.assign_hotkey).pack(side="left", padx=5)
        ttk.Button(hotkey_controls, text="Remove Hotkey", command=self.remove_hotkey).pack(side="left", padx=5)
        
        ttk.Label(individual_frame, text="💡 Tip: You can always change hotkeys later in Settings",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=5)
    
    def populate_hotkey_assignments(self):
        """Populate hotkey assignment tree"""
        if not hasattr(self, 'apps_tree'):
            return
        
        for item in self.apps_tree.get_children():
            values = self.apps_tree.item(item, "values")
            if len(values) >= 4 and values[3] == "✓":  # Only included apps
                app_name, keyword, category, _ = values
                self.hotkey_tree.insert("", "end", values=(keyword, app_name, ""))
    
    def test_global_hotkey(self):
        """Test the global hotkey configuration"""
        hotkey = self.global_hotkey_var.get()
        # Simple validation
        if "+" in hotkey and hotkey.startswith("<") and hotkey.endswith(">"):
            messagebox.showinfo("Test Result", f"Hotkey '{hotkey}' format looks valid!")
        else:
            messagebox.showwarning("Test Result", "Invalid hotkey format. Use format like <ctrl>+<alt>+k")
    
    def assign_hotkey(self):
        """Assign hotkey to selected command"""
        selection = self.hotkey_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a command to assign a hotkey to.")
            return
        
        # Show hotkey input dialog
        HotkeyAssignmentDialog(self, selection[0])
    
    def remove_hotkey(self):
        """Remove hotkey from selected command"""
        selection = self.hotkey_tree.selection()
        if selection:
            values = list(self.hotkey_tree.item(selection[0], "values"))
            values[2] = ""  # Clear hotkey
            self.hotkey_tree.item(selection[0], values=values)
    
    def show_completion_step(self):
        """Step 4: Completion and summary"""
        self.title_label.config(text="Setup Complete!")
        self.subtitle_label.config(text="Your KeywordAutomator is ready to use")
        
        content = ttk.Frame(self.content_frame)
        content.pack(fill="both", expand=True)
        
        # Success message
        success_frame = ttk.Frame(content)
        success_frame.pack(fill="x", pady=10)
        
        success_text = """
🎉 Congratulations! KeywordAutomator is now set up and ready to boost your productivity.

Here's what we've configured for you:
        """
        
        ttk.Label(success_frame, text=success_text.strip(), 
                 font=("Segoe UI", 10)).pack(anchor="w")
        
        # Summary frame
        summary_frame = ttk.LabelFrame(content, text="Setup Summary")
        summary_frame.pack(fill="both", expand=True, pady=10)
        
        # Create summary content
        self.create_setup_summary(summary_frame)
        
        # Next steps
        next_steps_frame = ttk.LabelFrame(content, text="Next Steps")
        next_steps_frame.pack(fill="x", pady=10)
        
        next_steps_text = """
• Press Ctrl+Alt+K to open the keyword dialog
• Type any keyword and press Enter to run it
• Right-click the system tray icon for quick access
• Visit Settings to add more keywords or modify existing ones
• Check out Help & Documentation for advanced features
        """
        
        ttk.Label(next_steps_frame, text=next_steps_text.strip(),
                 font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=5)
        
        # Options
        options_frame = ttk.Frame(content)
        options_frame.pack(fill="x", pady=10)
        
        self.show_help_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Show help documentation after setup",
            variable=self.show_help_var
        ).pack(anchor="w")
        
        self.minimize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Minimize to system tray after setup",
            variable=self.minimize_var
        ).pack(anchor="w")
    
    def create_setup_summary(self, parent):
        """Create setup summary content"""
        summary_text = tk.Text(parent, height=8, wrap=tk.WORD, font=("Segoe UI", 9))
        summary_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Count selected applications
        app_count = 0
        hotkey_count = 0
        
        if hasattr(self, 'apps_tree'):
            for item in self.apps_tree.get_children():
                values = self.apps_tree.item(item, "values")
                if len(values) >= 4 and values[3] == "✓":
                    app_count += 1
        
        if hasattr(self, 'hotkey_tree'):
            for item in self.hotkey_tree.get_children():
                values = self.hotkey_tree.item(item, "values")
                if len(values) >= 3 and values[2]:  # Has hotkey
                    hotkey_count += 1
        
        summary_content = f"""
✓ {app_count} applications configured with keywords
✓ {hotkey_count} individual hotkeys assigned
✓ Global hotkey set to: {self.global_hotkey_var.get()}
✓ Automatic categorization enabled: {self.auto_categorize_var.get()}
✓ Categories organized and ready

Your keywords are ready to use! Press {self.global_hotkey_var.get()} anytime to access them.
        """
        
        summary_text.insert(tk.END, summary_content.strip())
        summary_text.config(state="disabled")
    
    def previous_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
    
    def next_step(self):
        """Go to next step or finish setup"""
        if self.current_step < self.total_steps - 1:
            # Validate current step before proceeding
            if self.validate_current_step():
                self.show_step(self.current_step + 1)
        else:
            # Finish setup
            self.finish_setup()
    
    def validate_current_step(self) -> bool:
        """Validate current step before proceeding"""
        if self.current_step == 1:  # Detection step
            # Just ensure detection completed - no strict validation needed
            pass
        elif self.current_step == 2:  # Categories step  
            # Categories are optional - no strict validation needed
            pass
        elif self.current_step == 3:  # Hotkeys step
            # Validate global hotkey format
            hotkey = self.global_hotkey_var.get().strip()
            if not hotkey:
                messagebox.showwarning("Missing Hotkey", 
                                     "Please enter a global hotkey or use the default.")
                return False
            if "+" not in hotkey or not hotkey.startswith("<") or not hotkey.endswith(">"):
                messagebox.showwarning("Invalid Hotkey", 
                                     "Please enter a valid global hotkey format like <ctrl>+<alt>+k")
                return False
        
        return True
    
    def skip_setup(self):
        """Skip the setup wizard"""
        if messagebox.askyesno("Skip Setup", 
                             "Are you sure you want to skip the setup wizard?\n\n"
                             "You can always run it again from the Help menu."):
            self.finish_setup(skipped=True)
    
    def finish_setup(self, skipped: bool = False):
        """Complete the setup process"""
        try:
            if not skipped:
                self.apply_wizard_settings()
            
            # Mark wizard as completed
            self.parent_app.app_config["wizard_completed"] = True
            self.parent_app.app_config["has_seen_welcome"] = True
            
            # Save configuration with explicit verification
            try:
                from . import config as config_module
            except ImportError:
                import config as config_module
            
            save_success = config_module.save_config(self.parent_app.app_config)
            if save_success:
                logger.info("Wizard completion status saved successfully")
            else:
                logger.error("Failed to save wizard completion status")
            
            # Show help if requested
            if not skipped and hasattr(self, 'show_help_var') and self.show_help_var.get():
                self.after(500, lambda: self.parent_app.documentation_system.show_help_window())
            
            # Minimize if requested
            if not skipped and hasattr(self, 'minimize_var') and self.minimize_var.get():
                self.after(1000, self.parent_app.minimize_to_tray)
            
            # Close wizard
            self.destroy()
            
            # Show completion message
            if not skipped:
                messagebox.showinfo("Setup Complete", 
                                  "KeywordAutomator setup is complete!\n\n"
                                  f"Press {self.global_hotkey_var.get()} to start using your keywords.")
            
        except Exception as e:
            report_error(e, ErrorCategory.CONFIG, "wizard_completion",
                        user_message="Setup completed with some errors. You can configure manually in Settings.")
    
    def apply_wizard_settings(self):
        """Apply all wizard settings to the application"""
        try:
            # Apply global hotkey
            if hasattr(self, 'global_hotkey_var'):
                self.parent_app.app_config["global_hotkey"] = self.global_hotkey_var.get()
            
            # Apply detected applications
            if hasattr(self, 'apps_tree'):
                detected_apps = self.wizard_data.get('detected_apps', {})
                
                for item in self.apps_tree.get_children():
                    values = self.apps_tree.item(item, "values")
                    if len(values) >= 4 and values[3] == "✓":  # Include selected
                        app_name, keyword, category, _ = values
                        
                        if keyword in detected_apps:
                            app_info = detected_apps[keyword]
                            
                            # Get hotkey if assigned
                            hotkey = None
                            if hasattr(self, 'hotkey_tree'):
                                for hk_item in self.hotkey_tree.get_children():
                                    hk_values = self.hotkey_tree.item(hk_item, "values")
                                    if len(hk_values) >= 3 and hk_values[0] == keyword and hk_values[2]:
                                        hotkey = hk_values[2]
                                        break
                            
                            # Create mapping
                            mapping = {
                                'command': app_info['command'],
                                'category': category,
                                'hotkey': hotkey if hotkey else 'None',
                                'is_script': False,
                                'run_as_admin': False,
                                'show_window': True,
                                'description': app_info.get('description', '')
                            }
                            
                            # Add to config
                            if 'mappings' not in self.parent_app.app_config:
                                self.parent_app.app_config['mappings'] = {}
                            
                            self.parent_app.app_config['mappings'][keyword] = mapping
            
            # Apply other settings
            if hasattr(self, 'auto_categorize_var'):
                self.parent_app.app_config["auto_categorize"] = self.auto_categorize_var.get()
            
            if hasattr(self, 'show_icons_var'):
                self.parent_app.app_config["show_category_icons"] = self.show_icons_var.get()
            
        except Exception as e:
            raise Exception(f"Failed to apply wizard settings: {e}")
    
    def on_close_attempt(self):
        """Handle window close attempt"""
        if messagebox.askyesno("Exit Setup", 
                             "Are you sure you want to exit the setup wizard?\n\n"
                             "Your current progress will be lost."):
            self.destroy()


class HotkeyAssignmentDialog(tk.Toplevel):
    """Dialog for assigning hotkeys to commands"""
    
    def __init__(self, parent_wizard, tree_item):
        super().__init__(parent_wizard)
        self.parent_wizard = parent_wizard
        self.tree_item = tree_item
        self.result = None
        
        self.setup_dialog()
        self.create_widgets()
        
        # Apply theme
        if hasattr(parent_wizard.parent_app, "apply_theme_to_toplevel"):
            parent_wizard.parent_app.apply_theme_to_toplevel(self)
    
    def setup_dialog(self):
        """Setup dialog window"""
        self.title("Assign Hotkey")
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(self.parent_wizard)
        self.grab_set()
        
        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Get command info
        values = self.parent_wizard.hotkey_tree.item(self.tree_item, "values")
        keyword, app_name, current_hotkey = values
        
        # Title
        ttk.Label(main_frame, text=f"Assign Hotkey to '{keyword}'", 
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        ttk.Label(main_frame, text=f"Application: {app_name}",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 15))
        
        # Hotkey input
        ttk.Label(main_frame, text="Hotkey:").pack(anchor="w")
        
        self.hotkey_var = tk.StringVar(value=current_hotkey)
        hotkey_entry = ttk.Entry(main_frame, textvariable=self.hotkey_var, width=30)
        hotkey_entry.pack(fill="x", pady=5)
        hotkey_entry.focus_set()
        
        # Format help
        ttk.Label(main_frame, text="Format: <modifier>+<key> (e.g., <ctrl>+<shift>+n)",
                 font=("Segoe UI", 9), foreground="gray").pack(anchor="w", pady=(0, 10))
        
        # Quick suggestions
        suggestions_frame = ttk.LabelFrame(main_frame, text="Quick Suggestions")
        suggestions_frame.pack(fill="x", pady=10)
        
        suggestions = [
            f"<ctrl>+<alt>+{keyword[0].lower()}",
            f"<ctrl>+<shift>+{keyword[0].lower()}",
            f"<win>+<alt>+{keyword[0].lower()}"
        ]
        
        for suggestion in suggestions:
            ttk.Button(suggestions_frame, text=suggestion,
                      command=lambda s=suggestion: self.hotkey_var.set(s)).pack(side="left", padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(15, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Assign", command=self.assign_hotkey).pack(side="right")
        ttk.Button(button_frame, text="Clear", command=lambda: self.hotkey_var.set("")).pack(side="left")
    
    def assign_hotkey(self):
        """Assign the hotkey"""
        hotkey = self.hotkey_var.get().strip()
        
        # Validate hotkey format if not empty
        if hotkey:
            try:
                from .utils import HotkeyValidator
            except ImportError:
                from utils import HotkeyValidator
            is_valid, error_msg = HotkeyValidator.validate_hotkey_format(hotkey)
            if not is_valid:
                messagebox.showerror("Invalid Hotkey", f"Invalid hotkey format:\n{error_msg}")
                return
            
            # Check for conflicts (simplified check)
            for item in self.parent_wizard.hotkey_tree.get_children():
                if item != self.tree_item:
                    values = self.parent_wizard.hotkey_tree.item(item, "values")
                    if len(values) >= 3 and values[2] == hotkey:
                        if not messagebox.askyesno("Hotkey Conflict", 
                                                  f"The hotkey '{hotkey}' is already assigned to '{values[0]}'.\n\n"
                                                  "Do you want to use it anyway?"):
                            return
        
        # Update tree
        values = list(self.parent_wizard.hotkey_tree.item(self.tree_item, "values"))
        values[2] = hotkey
        self.parent_wizard.hotkey_tree.item(self.tree_item, values=values)
        
        self.result = hotkey
        self.destroy()
