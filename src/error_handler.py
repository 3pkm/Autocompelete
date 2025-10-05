"""
Enhanced error handling and reporting system for KeywordAutomator.
Provides user-friendly error messages and comprehensive logging.
"""

import os
import sys
import logging
from tkinter import messagebox
import traceback
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class ErrorLevel(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better organization"""
    HOTKEY = "hotkey"
    COMMAND_EXECUTION = "command_execution"
    CONFIG = "configuration"
    UI = "user_interface"
    SYSTEM = "system"
    IMPORT = "import"
    TRAY = "system_tray"
    CRITICAL = "critical"
    NETWORK = "network"
    ERROR = "error"
    WARNING = "warning"

class ErrorReporter:
    """Enhanced error reporting with user-friendly messages and solutions"""
    
    def __init__(self, log_file_path: Optional[str] = None):
        self.error_log = []
        self.setup_local_logger(log_file_path)
        # Lightweight audit/event logging separate from error reporting
        # Use self.logger with category='audit' via extra fields
        
        # Error solutions database
        self.error_solutions = {
            ErrorCategory.HOTKEY: {
                "invalid_format": {
                    "message": "The hotkey format is incorrect.",
                    "solution": "Use format like <ctrl>+<alt>+k. Each modifier and key should be in angle brackets.",
                    "example": "Examples: <ctrl>+<alt>+k, <shift>+<ctrl>+f1"
                },
                "conflict": {
                    "message": "This hotkey is already assigned to another command.",
                    "solution": "Choose a different hotkey combination or remove the existing assignment.",
                    "example": "Try using <ctrl>+<shift>+k instead"
                },
                "listener_failed": {
                    "message": "Failed to start hotkey listener.",
                    "solution": "Try restarting the application. If the problem persists, check if another application is blocking hotkeys.",
                    "example": "Some antivirus software can block hotkey functionality"
                }
            },
            ErrorCategory.COMMAND_EXECUTION: {
                "command_not_found": {
                    "message": "The command or application could not be found.",
                    "solution": "Check if the application is installed and the path is correct.",
                    "example": "For 'notepad', ensure Windows is properly installed. For custom apps, use full paths."
                },
                "permission_denied": {
                    "message": "Permission denied when trying to execute the command.",
                    "solution": "Try enabling 'Run as Administrator' for this command, or check file permissions.",
                    "example": "System commands often require administrator privileges"
                },
                "script_error": {
                    "message": "Error occurred while executing the script.",
                    "solution": "Check the script syntax and ensure all required dependencies are installed.",
                    "example": "For Python scripts, make sure Python is installed and accessible"
                }
            },
            ErrorCategory.CONFIG: {
                "load_failed": {
                    "message": "Failed to load configuration file.",
                    "solution": "The config file may be corrupted. A new default configuration will be created.",
                    "example": "Your settings will be reset to defaults"
                },
                "save_failed": {
                    "message": "Failed to save configuration.",
                    "solution": "Check if the application has write permissions to the config directory.",
                    "example": "Try running the application as administrator"
                }
            },
            ErrorCategory.UI: {
                "theme_error": {
                    "message": "Error applying theme.",
                    "solution": "Theme will be reset to default. Try selecting a different theme.",
                    "example": "Switch to Light or Dark theme manually"
                },
                "dialog_error": {
                    "message": "Error displaying dialog window.",
                    "solution": "Try restarting the application.",
                    "example": "This usually resolves UI-related issues"
                }
            },
            ErrorCategory.SYSTEM: {
                "tray_failed": {
                    "message": "Failed to create system tray icon.",
                    "solution": "The application will continue to work, but won't appear in the system tray.",
                    "example": "You can still access the application from the taskbar"
                },
                "startup_failed": {
                    "message": "Failed to set up startup configuration.",
                    "solution": "You'll need to manually add the application to your startup programs.",
                    "example": "Add the application to Windows startup folder"
                }
            },
            ErrorCategory.IMPORT: {
                "module_missing": {
                    "message": "Required module is missing.",
                    "solution": "Try reinstalling the application or installing missing dependencies.",
                    "example": "Run: pip install -r requirements.txt"
                }
            }
        }
    
    def setup_local_logger(self, log_file_path: Optional[str] = None):
        """Setup local logger in the application directory"""
        if log_file_path is None:
            # Create log file in the application directory
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_file_path = os.path.join(app_dir, 'keyword_automator_errors.log')
        
        self.log_file_path = log_file_path
        
        # Create logger
        self.logger = logging.getLogger('ErrorReporter')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler for detailed logging
        try:
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(category)s - %(message)s\n'
                'Details: %(details)s\n'
                'Traceback: %(traceback)s\n'
                '---'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def log_audit(self, action: str, details: Optional[Dict[str, Any]] = None):
        """Log an audit/event entry to the same log file used for errors.

        This is intended for informational events like admin executions.
        """
        try:
            payload = {
                "action": action,
                "details": details or {},
            }
            extra = {
                'category': 'audit',
                'details': json.dumps(payload, indent=2, default=str),
                'traceback': ''
            }
            self.logger.info(f"AUDIT: {action}", extra=extra)
        except Exception:
            # Do not raise from audit logging
            pass
    
    def report_error(self, 
                    error: Exception, 
                    category: ErrorCategory, 
                    error_type: str = "general",
                    context: Optional[Dict[str, Any]] = None,
                    user_message: Optional[str] = None,
                    show_dialog: bool = True) -> str:
        """
        Report an error with comprehensive logging and user-friendly feedback
        
        Returns: User-friendly error message
        """
        timestamp = datetime.now()
        
        # Get error details
        error_details = {
            'timestamp': timestamp.isoformat(),
            'error_type': str(type(error).__name__),
            'error_message': str(error),
            'category': category.value,
            'specific_type': error_type,
            'context': context or {},
            'traceback': traceback.format_exc()
        }
        
        # Add to error log
        self.error_log.append(error_details)
        
        # Get user-friendly message
        friendly_message = self._get_friendly_message(category, error_type, error, user_message)
        
        # Log to file with extra context
        extra = {
            'category': category.value,
            'details': json.dumps(error_details, indent=2),
            'traceback': error_details['traceback']
        }
        
        if category == ErrorCategory.CRITICAL:
            self.logger.critical(friendly_message, extra=extra)
        elif category == ErrorCategory.ERROR:
            self.logger.error(friendly_message, extra=extra)
        elif category == ErrorCategory.WARNING:
            self.logger.warning(friendly_message, extra=extra)
        else:
            self.logger.info(friendly_message, extra=extra)
        
        # Show user dialog if requested
        if show_dialog:
            self._show_user_dialog(friendly_message, category, error_type)
        
        return friendly_message
    
    def _get_friendly_message(self, 
                             category: ErrorCategory, 
                             error_type: str, 
                             error: Exception,
                             user_message: Optional[str] = None) -> str:
        """Generate user-friendly error message"""
        if user_message:
            return user_message
        
        # Try to get specific error info
        if category in self.error_solutions and error_type in self.error_solutions[category]:
            error_info = self.error_solutions[category][error_type]
            return f"{error_info['message']}\n\nSolution: {error_info['solution']}\n\nTip: {error_info['example']}"
        
        # Fallback to generic messages
        generic_messages = {
            ErrorCategory.HOTKEY: "There was an issue with hotkey functionality.",
            ErrorCategory.COMMAND_EXECUTION: "Failed to execute the command.",
            ErrorCategory.CONFIG: "Configuration error occurred.",
            ErrorCategory.UI: "User interface error occurred.",
            ErrorCategory.SYSTEM: "System-level error occurred.",
            ErrorCategory.IMPORT: "Module import error occurred.",
            ErrorCategory.TRAY: "System tray error occurred."
        }
        
        base_message = generic_messages.get(category, "An unexpected error occurred.")
        return f"{base_message}\n\nTechnical details: {str(error)[:100]}..."
    
    def _show_user_dialog(self, message: str, category: ErrorCategory, error_type: str):
        """Show user-friendly error dialog"""
        try:
            import tkinter as tk
            from tkinter import messagebox, scrolledtext
            
            # Determine dialog type based on category
            if category == ErrorCategory.CRITICAL:
                title = "Critical Error"
                icon = "error"
            elif category == ErrorCategory.ERROR:
                title = "Error"
                icon = "error"
            elif category == ErrorCategory.WARNING:
                title = "Warning"
                icon = "warning"
            else:
                title = "Information"
                icon = "info"
            
            # For long messages, show in a custom dialog
            if len(message) > 200:
                self._show_detailed_error_dialog(title, message)
            else:
                # Use standard messagebox for short messages
                if icon == "error":
                    messagebox.showerror(title, message)
                elif icon == "warning":
                    messagebox.showwarning(title, message)
                else:
                    messagebox.showinfo(title, message)
                    
        except Exception as e:
            # Fallback to console if GUI fails
            print(f"{category.value.upper()}: {message}")
    
    def _show_detailed_error_dialog(self, title: str, message: str):
        """Show detailed error dialog with scrollable text"""
        try:
            import tkinter as tk
            from tkinter import scrolledtext, ttk
            
            # Create dialog window
            dialog = tk.Toplevel()
            dialog.title(title)
            dialog.geometry("500x300")
            dialog.resizable(True, True)
            
            # Make it modal
            dialog.transient(dialog.master)
            dialog.grab_set()
            
            # Main frame
            main_frame = ttk.Frame(dialog, padding="10")
            main_frame.pack(fill="both", expand=True)
            
            # Message text area
            text_area = scrolledtext.ScrolledText(
                main_frame, 
                wrap=tk.WORD, 
                height=12,
                font=("Segoe UI", 9)
            )
            text_area.pack(fill="both", expand=True, pady=(0, 10))
            text_area.insert(tk.END, message)
            text_area.configure(state="disabled")
            
            # Buttons frame
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill="x")
            
            # Show log button
            def show_log():
                try:
                    if os.path.exists(self.log_file_path):
                        if sys.platform == 'win32':
                            os.startfile(self.log_file_path)
                        else:
                            import subprocess
                            subprocess.run(['open', self.log_file_path])
                except Exception as e:
                    messagebox.showerror("Error", f"Cannot open log file: {e}")
            
            ttk.Button(btn_frame, text="View Log File", command=show_log).pack(side="left")
            ttk.Button(btn_frame, text="OK", command=dialog.destroy).pack(side="right")
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
        except Exception as e:
            # Final fallback
            print(f"Error showing dialog: {e}")
            print(f"Original message: {message}")
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        stats = {}
        for error in self.error_log:
            category = error.get('category', 'unknown')
            stats[category] = stats.get(category, 0) + 1
        return stats
    
    def clear_error_log(self):
        """Clear the error log"""
        self.error_log = []
    
    def export_error_log(self, file_path: Optional[str] = None) -> str:
        """Export error log to JSON file"""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"error_log_{timestamp}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.error_log, f, indent=2, default=str)
            return file_path
        except Exception as e:
            raise Exception(f"Failed to export error log: {e}")


# Global error reporter instance
error_reporter = ErrorReporter()

def report_error(error: Exception, 
                category: ErrorCategory, 
                error_type: str = "general",
                context: Optional[Dict[str, Any]] = None,
                user_message: Optional[str] = None,
                show_dialog: bool = True) -> str:
    """Convenience function for reporting errors"""
    return error_reporter.report_error(
        error=error,
        category=category,
        error_type=error_type,
        context=context,
        user_message=user_message,
        show_dialog=show_dialog
    )

def log_audit(action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for audit logging without raising or dialogs."""
    error_reporter.log_audit(action, details)
