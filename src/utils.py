"""
Utility functions and classes for KeywordAutomator.
This module contains common utilities used across the application.
"""

import os
import sys
import re
import json
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class CommandHistory:
    """Manages command history with persistence across sessions"""
    
    def __init__(self, max_size: int = 50, history_file: Optional[str] = None):
        self.max_size = max_size
        self.history = []
        self.favorites = set()
        self.usage_count = {}
        
        # Set default history file path
        if history_file is None:
            try:
                from . import config
            except ImportError:
                # Fallback for standalone execution
                import config
            self.history_file = os.path.join(config.CONFIG_DIR, 'command_history.json')
        else:
            self.history_file = history_file
            
        self.load_history()
    
    def add_command(self, keyword: str):
        """Add a command to history"""
        if not keyword or not keyword.strip():
            return
            
        keyword = keyword.strip()
        
        # Remove if already exists to avoid duplicates
        if keyword in self.history:
            self.history.remove(keyword)
        
        # Add to beginning
        self.history.insert(0, keyword)
        
        # Trim to max size
        if len(self.history) > self.max_size:
            self.history = self.history[:self.max_size]
        
        # Update usage count
        self.usage_count[keyword] = self.usage_count.get(keyword, 0) + 1
        
        # Save to file
        self.save_history()
        
        logger.debug(f"Added command '{keyword}' to history")
    
    def get_suggestions(self, partial_keyword: str, limit: int = 5) -> List[str]:
        """Get command suggestions based on history and partial input"""
        if not partial_keyword:
            # Return most recent commands if no input
            return self.history[:limit]
        
        partial_lower = partial_keyword.lower()
        suggestions = []
        
        # First, exact prefix matches from history
        for cmd in self.history:
            if cmd.lower().startswith(partial_lower):
                suggestions.append(cmd)
                if len(suggestions) >= limit:
                    break
        
        # If we need more suggestions, add fuzzy matches
        if len(suggestions) < limit:
            for cmd in self.history:
                if (cmd not in suggestions and 
                    partial_lower in cmd.lower()):
                    suggestions.append(cmd)
                    if len(suggestions) >= limit:
                        break
        
        return suggestions
    
    def add_to_favorites(self, keyword: str):
        """Add a command to favorites"""
        self.favorites.add(keyword)
        self.save_history()
    
    def remove_from_favorites(self, keyword: str):
        """Remove a command from favorites"""
        self.favorites.discard(keyword)
        self.save_history()
    
    def is_favorite(self, keyword: str) -> bool:
        """Check if a command is in favorites"""
        return keyword in self.favorites
    
    def get_favorites(self) -> List[str]:
        """Get list of favorite commands"""
        return list(self.favorites)
    
    def get_most_used(self, limit: int = 10) -> List[str]:
        """Get most frequently used commands"""
        sorted_commands = sorted(
            self.usage_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return [cmd for cmd, count in sorted_commands[:limit]]
    
    def clear_history(self):
        """Clear all history"""
        self.history = []
        self.usage_count = {}
        self.save_history()
    
    def load_history(self):
        """Load history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get('history', [])
                    self.favorites = set(data.get('favorites', []))
                    self.usage_count = data.get('usage_count', {})
                    logger.info("Command history loaded successfully")
        except Exception as e:
            logger.error(f"Error loading command history: {e}")
            self.history = []
            self.favorites = set()
            self.usage_count = {}
    
    def save_history(self):
        """Save history to file"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            data = {
                'history': self.history,
                'favorites': list(self.favorites),
                'usage_count': self.usage_count,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving command history: {e}")


class HotkeyValidator:
    """Validates and normalizes hotkey strings"""
    
    # Valid modifier keys
    VALID_MODIFIERS = {'ctrl', 'alt', 'shift', 'win', 'cmd', 'super'}
    
    # Valid key patterns
    KEY_PATTERN = re.compile(r'^[a-zA-Z0-9]$|^f[1-9]|f1[0-2]$|^(space|enter|tab|esc|escape|backspace|delete|home|end|pageup|pagedown|insert|up|down|left|right)$')
    
    @classmethod
    def validate_hotkey_format(cls, hotkey_string: str) -> tuple[bool, str]:
        """
        Validate hotkey format and return (is_valid, error_message)
        
        Expected format: <modifier>+<modifier>+<key>
        Example: <ctrl>+<alt>+k
        """
        if not hotkey_string or not hotkey_string.strip():
            return False, "Hotkey cannot be empty"
        
        hotkey_string = hotkey_string.strip()
        
        # Split by + and process parts
        parts = hotkey_string.split('+')
        if len(parts) < 2:
            return False, "Hotkey must have at least one modifier and one key"
        
        modifiers = []
        key = None
        
        for i, part in enumerate(parts):
            part = part.strip()
            
            if i == len(parts) - 1:  # Last part is the key
                # Key can be with or without brackets
                if part.startswith('<') and part.endswith('>'):
                    key = part.strip('<>').lower()
                else:
                    key = part.lower()
            else:  # Modifier
                # Check if part is enclosed in brackets
                if not (part.startswith('<') and part.endswith('>')):
                    return False, f"Modifier must be enclosed in angle brackets: {part}"
                
                # Remove brackets
                clean_part = part.strip('<>').lower()
                
                if clean_part not in cls.VALID_MODIFIERS:
                    return False, f"Invalid modifier '{clean_part}'. Valid modifiers: {', '.join(cls.VALID_MODIFIERS)}"
                modifiers.append(clean_part)
        
        # Validate key
        if not key:
            return False, "No key specified"
        
        if not cls.KEY_PATTERN.match(key):
            return False, f"Invalid key '{key}'. Use single letters, numbers, or function keys (f1-f12)"
        
        # Check for duplicate modifiers
        if len(modifiers) != len(set(modifiers)):
            return False, "Duplicate modifiers not allowed"
        
        return True, ""
    
    @classmethod
    def normalize_hotkey(cls, hotkey_string: str) -> str:
        """Normalize hotkey string to standard format"""
        is_valid, error = cls.validate_hotkey_format(hotkey_string)
        if not is_valid:
            raise ValueError(f"Invalid hotkey: {error}")
        
        parts = hotkey_string.strip().lower().split('+')
        modifiers = [part.strip('<>') for part in parts[:-1]]
        key = parts[-1].strip('<>')
        
        # Sort modifiers for consistency
        modifiers.sort()
        
        # Build normalized string
        normalized_parts = [f'<{mod}>' for mod in modifiers] + [f'<{key}>']
        return '+'.join(normalized_parts)
    
    @classmethod
    def detect_hotkey_conflicts(cls, new_hotkey: str, existing_mappings: Dict[str, Dict]) -> List[str]:
        """Detect conflicts with existing hotkey assignments"""
        conflicts = []
        
        try:
            normalized_new = cls.normalize_hotkey(new_hotkey)
        except ValueError:
            return conflicts  # Invalid hotkey, let validation handle it
        
        for keyword, mapping in existing_mappings.items():
            if isinstance(mapping, dict):
                existing_hotkey = mapping.get('hotkey')
                if existing_hotkey and existing_hotkey.lower() != 'none':
                    try:
                        normalized_existing = cls.normalize_hotkey(existing_hotkey)
                        if normalized_new == normalized_existing:
                            conflicts.append(keyword)
                    except ValueError:
                        # Ignore invalid existing hotkeys
                        continue
        
        return conflicts


class CommandCategory:
    """Represents a command category with metadata"""
    
    def __init__(self, name: str, icon: Optional[str] = None, color: Optional[str] = None):
        self.name = name
        self.icon = icon or "📁"
        self.color = color or "#0078d7"
        self.commands = []
    
    def add_command(self, keyword: str, mapping: Dict):
        """Add a command to this category"""
        self.commands.append((keyword, mapping))
    
    def remove_command(self, keyword: str):
        """Remove a command from this category"""
        self.commands = [(k, m) for k, m in self.commands if k != keyword]
    
    def get_command_count(self) -> int:
        """Get number of commands in this category"""
        return len(self.commands)


class CommandCategoryManager:
    """Manages command categories and auto-categorization"""
    
    # Predefined categories with detection patterns
    DEFAULT_CATEGORIES = {
        'Web & Browsers': {
            'icon': '🌐',
            'color': '#4285f4',
            'patterns': [
                r'chrome|firefox|edge|safari|browser',
                r'https?://',
                r'www\.',
                r'\.com|\.org|\.net'
            ]
        },
        'System & Utilities': {
            'icon': '⚙️',
            'color': '#ff9800',
            'patterns': [
                r'notepad|calc|calculator|control|cmd|powershell|terminal',
                r'taskmgr|regedit|msconfig|services',
                r'explorer|folder'
            ]
        },
        'Development': {
            'icon': '💻',
            'color': '#9c27b0',
            'patterns': [
                r'vscode|code|visual studio|sublime|atom|notepad\+\+',
                r'git|github|python|node|npm|pip',
                r'\.py|\.js|\.html|\.css|\.json'
            ]
        },
        'Media & Entertainment': {
            'icon': '🎵',
            'color': '#e91e63',
            'patterns': [
                r'spotify|youtube|vlc|media player|music',
                r'netflix|video|movie|photo',
                r'\.mp3|\.mp4|\.avi|\.jpg|\.png'
            ]
        },
        'Office & Productivity': {
            'icon': '📄',
            'color': '#2196f3',
            'patterns': [
                r'word|excel|powerpoint|outlook|onenote',
                r'office|teams|slack|zoom|skype',
                r'\.doc|\.xls|\.ppt|\.pdf'
            ]
        },
        'Scripts & Automation': {
            'icon': '🔧',
            'color': '#4caf50',
            'patterns': [
                r'\.bat|\.ps1|\.sh|\.py',
                r'script|automation|batch',
                r'python|powershell|bash'
            ]
        }
    }
    
    def __init__(self):
        self.categories = {}
        self.custom_categories = {}
        self._initialize_default_categories()
    
    def _initialize_default_categories(self):
        """Initialize default categories"""
        for name, data in self.DEFAULT_CATEGORIES.items():
            self.categories[name] = CommandCategory(
                name=name,
                icon=data['icon'],
                color=data['color']
            )
    
    def detect_category(self, keyword: str, command: str) -> str:
        """Auto-detect category based on keyword and command content"""
        text_to_analyze = f"{keyword} {command}".lower()
        
        for category_name, category_data in self.DEFAULT_CATEGORIES.items():
            for pattern in category_data['patterns']:
                if re.search(pattern, text_to_analyze, re.IGNORECASE):
                    return category_name
        
        return 'Other'
    
    def add_custom_category(self, name: str, icon: str = None, color: str = None):
        """Add a custom category"""
        if name not in self.categories:
            self.categories[name] = CommandCategory(name, icon, color)
            self.custom_categories[name] = True
    
    def get_category(self, name: str) -> Optional[CommandCategory]:
        """Get category by name"""
        return self.categories.get(name)
    
    def get_all_categories(self) -> Dict[str, CommandCategory]:
        """Get all categories"""
        return self.categories.copy()
    
    def categorize_command(self, keyword: str, mapping: Dict[str, any], user_category: Optional[str] = None) -> str:
        """Categorize a command, using user category if provided, otherwise auto-detect"""
        if user_category and user_category.strip():
            # User provided custom category
            category_name = user_category.strip()
            if category_name not in self.categories:
                self.add_custom_category(category_name)
            return category_name
        else:
            # Auto-detect category
            command = mapping.get('command', '') if isinstance(mapping, dict) else str(mapping)
            return self.detect_category(keyword, command)


def detect_common_applications():
    """Detect common applications installed on the system"""
    applications = {}
    
    if sys.platform == 'win32':
        # Windows application detection
        common_apps = {
            'notepad': {
                'command': 'notepad',
                'category': 'System & Utilities',
                'description': 'Open Notepad text editor'
            },
            'calc': {
                'command': 'calc',
                'category': 'System & Utilities', 
                'description': 'Open Calculator'
            },
            'cmd': {
                'command': 'cmd',
                'category': 'System & Utilities',
                'description': 'Open Command Prompt'
            },
            'powershell': {
                'command': 'powershell',
                'category': 'System & Utilities',
                'description': 'Open PowerShell'
            },
            'explorer': {
                'command': 'explorer',
                'category': 'System & Utilities',
                'description': 'Open File Explorer'
            },
            'taskmgr': {
                'command': 'taskmgr',
                'category': 'System & Utilities',
                'description': 'Open Task Manager'
            },
            'control': {
                'command': 'control',
                'category': 'System & Utilities',
                'description': 'Open Control Panel'
            },
            'msconfig': {
                'command': 'msconfig',
                'category': 'System & Utilities',
                'description': 'Open System Configuration'
            }
        }
        
        # Check for browser executables
        browser_paths = [
            ('chrome', r'C:\Program Files\Google\Chrome\Application\chrome.exe'),
            ('chrome', r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'),
            ('firefox', r'C:\Program Files\Mozilla Firefox\firefox.exe'),
            ('firefox', r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe'),
            ('edge', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
        ]
        
        for name, path in browser_paths:
            if os.path.exists(path) and name not in applications:
                applications[name] = {
                    'command': f'"{path}"',
                    'category': 'Web & Browsers',
                    'description': f'Open {name.title()} browser'
                }
        
        # Add common apps
        applications.update(common_apps)
        
        # Check for Office applications
        office_apps = {
            'word': (r'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE', 'Microsoft Word'),
            'excel': (r'C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE', 'Microsoft Excel'),
            'powerpoint': (r'C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE', 'Microsoft PowerPoint')
        }
        
        for app_name, (path, description) in office_apps.items():
            if os.path.exists(path):
                applications[app_name] = {
                    'command': f'"{path}"',
                    'category': 'Office & Productivity',
                    'description': f'Open {description}'
                }
        
        # Check for development tools
        dev_tools = {
            'vscode': (r'C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe'.format(os.getenv('USERNAME', '')), 'Visual Studio Code'),
            'code': (r'C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe'.format(os.getenv('USERNAME', '')), 'Visual Studio Code')
        }
        
        for app_name, (path, description) in dev_tools.items():
            if os.path.exists(path):
                applications[app_name] = {
                    'command': f'"{path}"',
                    'category': 'Development',
                    'description': f'Open {description}'
                }
    
    return applications


class ResourceManager:
    """Manages application resources and cleanup tasks"""
    
    def __init__(self):
        self.cleanup_tasks = []
        self.temp_files = []
        self.threads = []
        self.tray_icons = []
    
    def register_cleanup(self, task_func, description: str = ""):
        """Register a cleanup task"""
        self.cleanup_tasks.append((task_func, description))
        logger.debug(f"Registered cleanup task: {description}")
    
    def register_temp_file(self, file_path: str):
        """Register a temporary file for cleanup"""
        self.temp_files.append(file_path)
    
    def register_thread(self, thread):
        """Register a thread for proper shutdown"""
        self.threads.append(thread)
    
    def register_tray_icon(self, tray_icon):
        """Register a tray icon for cleanup"""
        self.tray_icons.append(tray_icon)
    
    def cleanup_all(self):
        """Execute all cleanup tasks"""
        logger.info("Starting resource cleanup...")
        
        # Stop tray icons
        for tray_icon in self.tray_icons:
            try:
                if hasattr(tray_icon, 'stop'):
                    tray_icon.stop()
                logger.debug("Stopped tray icon")
            except Exception as e:
                logger.error(f"Error stopping tray icon: {e}")
        
        # Execute custom cleanup tasks
        for task_func, description in self.cleanup_tasks:
            try:
                task_func()
                logger.debug(f"Completed cleanup task: {description}")
            except Exception as e:
                logger.error(f"Error in cleanup task '{description}': {e}")
        
        # Clean up temporary files
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Removed temp file: {file_path}")
            except Exception as e:
                logger.error(f"Error removing temp file {file_path}: {e}")
        
        # Wait for threads to finish (with timeout)
        for thread in self.threads:
            try:
                if hasattr(thread, 'join'):
                    thread.join(timeout=2.0)
                logger.debug("Thread joined")
            except Exception as e:
                logger.error(f"Error joining thread: {e}")
        
        logger.info("Resource cleanup completed")
    
    def __del__(self):
        """Ensure cleanup happens on object destruction"""
        try:
            self.cleanup_all()
        except:
            pass  # Ignore errors during destruction
