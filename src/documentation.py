"""
Enhanced documentation and help system for KeywordAutomator.
Provides interactive tutorials and user-friendly help content.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import webbrowser
from typing import Dict, List, Optional
import json
import os

class HelpTopic:
    """Represents a help topic with content and metadata"""
    
    def __init__(self, title: str, content: str, category: str = "General", 
                 keywords: List[str] = None, examples: List[str] = None):
        self.title = title
        self.content = content
        self.category = category
        self.keywords = keywords or []
        self.examples = examples or []

class DocumentationSystem:
    """Interactive documentation and help system"""
    
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.help_topics = {}
        self.search_index = {}
        self._initialize_help_content()
        self._build_search_index()
    
    def _initialize_help_content(self):
        """Initialize all help topics"""
        
        # Getting Started
        self.help_topics["getting_started"] = HelpTopic(
            title="Getting Started",
            content="""
# Welcome to KeywordAutomator!

KeywordAutomator helps you boost productivity by creating custom keywords that trigger commands, scripts, or applications.

## Quick Start:
1. **Add Your First Keyword**: Click 'Add New Keyword' or go to Settings
2. **Set Up the Command**: Enter what you want the keyword to do
3. **Use It**: Press Ctrl+Alt+K and type your keyword

## Example:
- Keyword: `note`
- Command: `notepad`
- Usage: Press Ctrl+Alt+K, type 'note', press Enter → Notepad opens!

## Next Steps:
- Explore the Settings to add more keywords
- Try assigning hotkeys to your favorite commands
- Set up categories to organize your keywords
            """,
            category="Getting Started",
            keywords=["start", "begin", "first", "tutorial", "intro"],
            examples=["note → notepad", "calc → calculator"]
        )
        
        # Keywords and Commands
        self.help_topics["keywords"] = HelpTopic(
            title="Working with Keywords",
            content="""
# Keywords and Commands

Keywords are shortcuts that trigger commands or applications.

## Adding Keywords:
1. Go to Settings → Keywords tab
2. Click "Add" button
3. Fill in the form:
   - **Keyword**: Short, memorable name
   - **Command**: What to execute
   - **Category**: Optional organization
   - **Hotkey**: Optional direct hotkey

## Command Types:

### Simple Commands:
- `notepad` - Opens Notepad
- `calc` - Opens Calculator
- `explorer` - Opens File Explorer

### Applications with Paths:
- `"C:\\Program Files\\MyApp\\app.exe"`
- Always use quotes for paths with spaces

### Web URLs:
- `https://google.com`
- `https://github.com`

### Scripts:
- Enable "Script" option for complex operations
- Supports Python, PowerShell, Batch files

## Tips:
- Keep keywords short and memorable
- Use categories to organize related commands
- Test commands before saving
            """,
            category="Basic Usage",
            keywords=["keyword", "command", "add", "create", "execute"],
            examples=[
                "chrome → Google Chrome",
                "goog → https://google.com",
                "docs → https://docs.google.com"
            ]
        )
        
        # Hotkeys
        self.help_topics["hotkeys"] = HelpTopic(
            title="Hotkeys and Shortcuts",
            content="""
# Hotkeys and Shortcuts

## Global Hotkey:
- **Default**: Ctrl+Alt+K
- **Purpose**: Opens the keyword input dialog
- **Customizable**: Change in Settings → Hotkeys

## Individual Keyword Hotkeys:
You can assign direct hotkeys to any keyword:

### Format:
- `<ctrl>+<alt>+k` - Control + Alt + K
- `<shift>+<ctrl>+f1` - Shift + Control + F1
- `<win>+<alt>+m` - Windows + Alt + M

### Valid Modifiers:
- `<ctrl>` - Control key
- `<alt>` - Alt key  
- `<shift>` - Shift key
- `<win>` - Windows key

### Valid Keys:
- Letters: a-z
- Numbers: 0-9
- Function keys: f1-f12
- Special keys: space, enter, tab, esc

## Conflict Detection:
The system automatically detects and warns about hotkey conflicts.

## Tips:
- Use Ctrl+Alt combinations for global actions
- Use Ctrl+Shift for application-specific actions
- Avoid system hotkeys (like Alt+Tab)
            """,
            category="Advanced Features",
            keywords=["hotkey", "shortcut", "ctrl", "alt", "shift", "key"],
            examples=[
                "<ctrl>+<alt>+n → Opens Notepad",
                "<shift>+<ctrl>+c → Opens Calculator"
            ]
        )
        
        # Categories
        self.help_topics["categories"] = HelpTopic(
            title="Organizing with Categories",
            content="""
# Command Categories

Categories help organize your keywords by type or purpose.

## Auto-Detection:
KeywordAutomator automatically detects categories based on your commands:

- **Web & Browsers**: URLs, browser commands
- **System & Utilities**: System tools, utilities
- **Development**: Code editors, development tools
- **Media & Entertainment**: Music, video, games
- **Office & Productivity**: Documents, office apps
- **Scripts & Automation**: Custom scripts

## Custom Categories:
- Create your own categories
- Simply type a new category name when adding keywords
- Categories appear automatically in the interface

## Category Features:
- **Visual Organization**: See commands grouped by type
- **Color Coding**: Each category has its own color
- **Icons**: Visual indicators for quick recognition
- **Filtering**: Easily find commands by category

## Tips:
- Use descriptive category names
- Group related commands together
- Let auto-detection handle common apps
- Create custom categories for specific workflows
            """,
            category="Organization",
            keywords=["category", "organize", "group", "filter", "sort"],
            examples=[
                "Work Tools → Excel, Word, Teams",
                "Quick Access → Calculator, Notepad",
                "Development → VS Code, Git, Python"
            ]
        )
        
        # Scripts
        self.help_topics["scripts"] = HelpTopic(
            title="Using Scripts",
            content="""
# Advanced Scripting

Run complex scripts and automation with KeywordAutomator.

## Script Types:

### Python Scripts:
```python
import webbrowser
webbrowser.open('https://github.com')
print("Opened GitHub!")
```

### PowerShell Scripts:
```powershell
Get-Date
Write-Host "Current time displayed!"
```

### Batch Scripts:
```batch
@echo off
echo Hello from batch!
pause
```

## Script Options:

### Run as Administrator:
- Enable for system-level operations
- Required for some Windows commands
- Use carefully for security

### Show Window:
- **Enabled**: See script output
- **Disabled**: Run silently in background

## Script Features:
- **Auto-detection**: System detects script type
- **Temporary files**: Scripts run from temp files
- **Error handling**: Detailed error reporting
- **Security**: Validation before execution

## Best Practices:
- Test scripts before saving
- Use descriptive keywords for scripts
- Enable "Run as Admin" only when needed
- Add comments in complex scripts

## Examples:
- System info script
- File cleanup automation
- Quick calculations
- API calls and data fetching
            """,
            category="Advanced Features",
            keywords=["script", "python", "powershell", "batch", "automation"],
            examples=[
                "sysinfo → System information script",
                "cleanup → File cleanup automation",
                "weather → Weather API script"
            ]
        )
        
        # Troubleshooting
        self.help_topics["troubleshooting"] = HelpTopic(
            title="Troubleshooting",
            content="""
# Troubleshooting Common Issues

## Hotkeys Not Working:
1. **Check conflicts**: Other apps might use the same hotkey
2. **Restart application**: Sometimes resolves hotkey issues
3. **Run as administrator**: Required for some hotkey functionality
4. **Antivirus software**: May block hotkey functionality

## Commands Not Executing:
1. **Check paths**: Ensure application paths are correct
2. **Use quotes**: For paths with spaces: `"C:\\My App\\app.exe"`
3. **Test manually**: Try running the command in Command Prompt
4. **Permissions**: Some commands need administrator privileges

## Application Won't Start:
1. **Check dependencies**: Ensure Python and required modules are installed
2. **Run from terminal**: See detailed error messages
3. **Check log files**: Located in application directory
4. **Reinstall**: Download fresh copy if corrupted

## System Tray Issues:
1. **Windows settings**: Check if tray icons are enabled
2. **Restart application**: Usually resolves tray problems
3. **Fallback mode**: App continues working without tray

## Performance Issues:
1. **Too many keywords**: Consider organizing with categories
2. **Large scripts**: Break down into smaller pieces
3. **Background processes**: Check for running scripts

## Getting Help:
- Check error log files in application directory
- Use the error reporting system
- Visit the GitHub repository for updates
- Community forums for user discussions

## Error Logs:
Error details are saved to: `keyword_automator_errors.log`
            """,
            category="Support",
            keywords=["problem", "issue", "error", "fix", "help", "troubleshoot"],
            examples=[
                "Hotkey conflicts with other software",
                "Command not found errors",
                "Permission denied issues"
            ]
        )
    
    def _build_search_index(self):
        """Build search index for quick topic lookup"""
        self.search_index = {}
        
        for topic_id, topic in self.help_topics.items():
            # Index by title words
            title_words = topic.title.lower().split()
            for word in title_words:
                if word not in self.search_index:
                    self.search_index[word] = []
                self.search_index[word].append(topic_id)
            
            # Index by keywords
            for keyword in topic.keywords:
                if keyword.lower() not in self.search_index:
                    self.search_index[keyword.lower()] = []
                self.search_index[keyword.lower()].append(topic_id)
            
            # Index by category
            category_words = topic.category.lower().split()
            for word in category_words:
                if word not in self.search_index:
                    self.search_index[word] = []
                self.search_index[word].append(topic_id)
    
    def search_topics(self, query: str) -> List[str]:
        """Search for help topics by query"""
        if not query.strip():
            return list(self.help_topics.keys())
        
        query_words = query.lower().split()
        matching_topics = set()
        
        for word in query_words:
            # Exact matches
            if word in self.search_index:
                matching_topics.update(self.search_index[word])
            
            # Partial matches
            for index_word in self.search_index:
                if word in index_word:
                    matching_topics.update(self.search_index[index_word])
        
        return list(matching_topics)
    
    def get_topic(self, topic_id: str) -> Optional[HelpTopic]:
        """Get a specific help topic"""
        return self.help_topics.get(topic_id)
    
    def get_categories(self) -> List[str]:
        """Get all help categories"""
        categories = set()
        for topic in self.help_topics.values():
            categories.add(topic.category)
        return sorted(list(categories))
    
    def show_help_window(self, initial_topic: str = "getting_started"):
        """Show the main help window"""
        HelpWindow(self.parent_app, self, initial_topic)
    
    def show_quick_help(self, topic_id: str):
        """Show quick help popup for specific topic"""
        topic = self.get_topic(topic_id)
        if topic:
            QuickHelpDialog(self.parent_app, topic)


class HelpWindow(tk.Toplevel):
    """Main help window with navigation and search"""
    
    def __init__(self, parent_app, doc_system: DocumentationSystem, initial_topic: str = "getting_started"):
        super().__init__(parent_app.tk_root)
        self.parent_app = parent_app
        self.doc_system = doc_system
        self.current_topic = initial_topic
        
        self.setup_window()
        self.create_widgets()
        self.load_topic(initial_topic)
        
        # Apply theme
        if hasattr(parent_app, "apply_theme_to_toplevel"):
            parent_app.apply_theme_to_toplevel(self)
    
    def setup_window(self):
        """Setup window properties"""
        self.title("KeywordAutomator - Help & Documentation")
        self.geometry("900x700")
        self.minsize(800, 600)
        self.transient(self.parent_app.tk_root)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Create the help window interface"""
        # Main container
        main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Left panel - Navigation
        left_frame = ttk.Frame(main_container, width=250)
        main_container.add(left_frame, weight=0)
        
        # Search frame
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search Help:").pack(anchor="w")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(fill="x", pady=(5, 0))
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        # Topics tree
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ttk.Label(tree_frame, text="Help Topics:").pack(anchor="w")
        
        self.topics_tree = ttk.Treeview(tree_frame, show="tree")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.topics_tree.yview)
        self.topics_tree.configure(yscrollcommand=scrollbar.set)
        
        self.topics_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.topics_tree.bind("<Double-1>", self.on_topic_select)
        self.topics_tree.bind("<<TreeviewSelect>>", self.on_topic_select)
        
        # Right panel - Content
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=1)
        
        # Content header
        header_frame = ttk.Frame(right_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        self.topic_title = ttk.Label(header_frame, text="", font=("Segoe UI", 14, "bold"))
        self.topic_title.pack(anchor="w")
        
        # Content area
        content_frame = ttk.Frame(right_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.content_text = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            padx=10,
            pady=10
        )
        self.content_text.pack(fill="both", expand=True)
        
        # Bottom buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(button_frame, text="Close", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Print", command=self.print_topic).pack(side="right", padx=5)
        
        # Populate topics tree
        self.populate_topics_tree()
    
    def populate_topics_tree(self):
        """Populate the topics tree with categories and topics"""
        # Clear existing items
        for item in self.topics_tree.get_children():
            self.topics_tree.delete(item)
        
        # Group topics by category
        categories = {}
        for topic_id, topic in self.doc_system.help_topics.items():
            if topic.category not in categories:
                categories[topic.category] = []
            categories[topic.category].append((topic_id, topic.title))
        
        # Add categories and topics to tree
        for category, topics in sorted(categories.items()):
            category_item = self.topics_tree.insert("", "end", text=category, values=[category], open=True)
            
            for topic_id, topic_title in sorted(topics, key=lambda x: x[1]):
                self.topics_tree.insert(category_item, "end", text=topic_title, values=[topic_id])
    
    def on_search(self, event=None):
        """Handle search input"""
        query = self.search_var.get()
        matching_topics = self.doc_system.search_topics(query)
        
        # Update tree to show only matching topics
        self.populate_topics_tree()  # Reset first
        
        if query.strip():
            # Highlight matching topics
            for item in self.topics_tree.get_children():
                for child in self.topics_tree.get_children(item):
                    topic_id = self.topics_tree.item(child)["values"][0]
                    if topic_id not in matching_topics:
                        self.topics_tree.delete(child)
    
    def on_topic_select(self, event=None):
        """Handle topic selection"""
        selection = self.topics_tree.selection()
        if selection:
            item = selection[0]
            values = self.topics_tree.item(item)["values"]
            if values and len(values) > 0:
                topic_id = values[0]
                if topic_id in self.doc_system.help_topics:
                    self.load_topic(topic_id)
    
    def load_topic(self, topic_id: str):
        """Load and display a help topic"""
        topic = self.doc_system.get_topic(topic_id)
        if not topic:
            return
        
        self.current_topic = topic_id
        self.topic_title.config(text=topic.title)
        
        # Clear and populate content
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert(tk.END, topic.content)
        
        # Add examples if available
        if topic.examples:
            self.content_text.insert(tk.END, "\n\n## Examples:\n")
            for example in topic.examples:
                self.content_text.insert(tk.END, f"• {example}\n")
        
        # Make read-only
        self.content_text.configure(state="disabled")
    
    def print_topic(self):
        """Print or save current topic"""
        topic = self.doc_system.get_topic(self.current_topic)
        if topic:
            # For now, just copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(topic.content)
            
            # Show confirmation
            from tkinter import messagebox
            messagebox.showinfo("Copied", "Help content copied to clipboard!")


class QuickHelpDialog(tk.Toplevel):
    """Quick help popup for specific topics"""
    
    def __init__(self, parent_app, topic: HelpTopic):
        super().__init__(parent_app.tk_root)
        self.parent_app = parent_app
        self.topic = topic
        
        self.setup_dialog()
        self.create_content()
        
        # Apply theme
        if hasattr(parent_app, "apply_theme_to_toplevel"):
            parent_app.apply_theme_to_toplevel(self)
    
    def setup_dialog(self):
        """Setup dialog properties"""
        self.title(f"Quick Help - {self.topic.title}")
        self.geometry("500x400")
        self.resizable(True, True)
        self.transient(self.parent_app.tk_root)
        self.grab_set()
        
        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_content(self):
        """Create dialog content"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text=self.topic.title, font=("Segoe UI", 12, "bold"))
        title_label.pack(anchor="w", pady=(0, 10))
        
        # Content
        content_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            height=15
        )
        content_text.pack(fill="both", expand=True, pady=(0, 10))
        content_text.insert(tk.END, self.topic.content)
        
        # Add examples
        if self.topic.examples:
            content_text.insert(tk.END, "\n\nExamples:\n")
            for example in self.topic.examples:
                content_text.insert(tk.END, f"• {example}\n")
        
        content_text.configure(state="disabled")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="More Help", command=self.show_full_help).pack(side="left")
        ttk.Button(button_frame, text="Close", command=self.destroy).pack(side="right")
    
    def show_full_help(self):
        """Show the full help window"""
        self.destroy()
        self.parent_app.documentation_system.show_help_window()


def add_context_help(widget, help_text: str, parent_app):
    """Add context-sensitive help to any widget"""
    def show_help(event=None):
        help_topic = HelpTopic("Context Help", help_text, "Context")
        QuickHelpDialog(parent_app, help_topic)
    
    # Bind right-click or F1 for help
    widget.bind("<Button-3>", show_help)  # Right-click
    widget.bind("<F1>", show_help)  # F1 key
    
    # Add tooltip-style help
    def show_tooltip(event):
        # Create a simple tooltip (optional enhancement)
        pass
    
    widget.bind("<Enter>", show_tooltip)
