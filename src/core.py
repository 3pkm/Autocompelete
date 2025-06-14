import subprocess
import tempfile
import os
import sys
import logging
import re
import time
import threading

logger = logging.getLogger(__name__)

def show_error_dialog(title, message):
    """Show an error dialog to the user"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        # Create a root window (it will be hidden)
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        
        # Show the error message box
        messagebox.showerror(title, message)
        
        # Destroy the root window
        root.destroy()
    except ImportError:
        # If tkinter is not available, print to console as fallback
        print(f"ERROR - {title}: {message}")

def detect_script_type(command):
    """Detect what type of script is being executed"""
    command = command.lower().strip()
    
    if command.startswith('#!'):
        first_line = command.split('\n')[0]
        if 'python' in first_line:
            return "python"
        elif 'powershell' in first_line or 'pwsh' in first_line:
            return "powershell"
        elif 'bash' in first_line or 'sh' in first_line:
            return "shell"
        elif 'cmd' in first_line or 'bat' in first_line:
            return "batch"
    
    if os.path.exists(command):
        if command.endswith('.py'):
            return "python"
        elif command.endswith('.ps1'):
            return "powershell"
        elif command.endswith('.sh'):
            return "shell"
        elif command.endswith('.bat') or command.endswith('.cmd'):
            return "batch"
    
    if re.search(r'import\s+|from\s+\w+\s+import', command):
        return "python"
    elif re.search(r'function\s+\w+\s*{|\$\w+|Write-Host', command):
        return "powershell"
    elif re.search(r'echo\s+|set\s+\w+=|if\s+errorlevel', command):
        return "batch"
    elif re.search(r'echo\s+|export\s+\w+=|#!/bin/bash', command):
        return "shell"
    
    return "command"

def run_as_admin(command_to_run):
    """
    Runs a command with administrative privileges using PowerShell.
    """
    try:
        # Escape single quotes in command_to_run for PowerShell single-quoted string
        escaped_command = command_to_run.replace("'", "''")

        # Construct the PowerShell command to use Start-Process with an explicit ArgumentList array
        # This tells Start-Process to run cmd.exe with two arguments: "/c" and "escaped_command"
        ps_command = f"Start-Process -FilePath cmd.exe -ArgumentList @('/c', '{escaped_command}') -Verb RunAs -WindowStyle Hidden"
        
        logging.info(f"Constructed PowerShell command for admin execution: {ps_command}")
        
        # Execute the PowerShell command
        # CREATE_NO_WINDOW flag is used to prevent the PowerShell window from flashing
        process = subprocess.run(
            ["powershell.exe", "-Command", ps_command],
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception for non-zero exit codes, we'll check manually
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if process.returncode == 0:
            logging.info(f"Admin command executed successfully. Output: {process.stdout.strip()}")
            return True, process.stdout.strip()
        else:
            error_message = f"Admin command failed. Return code: {process.returncode}\\nStderr: {process.stderr.strip()}\\nStdout: {process.stdout.strip()}"
            logging.error(error_message)
            # In packaged mode, show GUI error. Otherwise, print to console.
            if getattr(sys, 'frozen', False):
                show_error_dialog("Admin Command Execution Failed", 
                                  f"Command: {command_to_run}\\nError: {process.stderr.strip() or process.stdout.strip() or 'Unknown error'}")
            return False, error_message
    except FileNotFoundError:
        error_msg = "Error: powershell.exe not found. Please ensure PowerShell is installed and in your system's PATH."
        logging.error(error_msg)
        if getattr(sys, 'frozen', False):
            show_error_dialog("PowerShell Not Found", error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred while trying to run command as admin: {e}"
        logging.exception(error_msg)
        if getattr(sys, 'frozen', False):
            show_error_dialog("Admin Execution Error", 
                              f"Command: {command_to_run}\\nError: {str(e)}")
        return False, str(e)

def run_python_script(command, show_window=True):
    """Run a Python script"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w') as temp:
            temp.write(command)
            temp_path = temp.name
        
        if show_window and sys.platform == 'win32':
            creationflags = subprocess.CREATE_NEW_CONSOLE
        else:
            creationflags = 0

        python_path = sys.executable
        subprocess.Popen([python_path, temp_path], creationflags=creationflags)

        threading.Timer(10.0, lambda: os.remove(temp_path)).start()
        return True
    except Exception as e:
        logger.error(f"Error running Python script: {e}")
        return False

def run_powershell_script(command, use_admin=False, show_window=True):
    """Run a PowerShell script"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ps1', mode='w') as temp:
            temp.write(command)
            temp_path = temp.name

        ps_command = f'powershell.exe -ExecutionPolicy Bypass -File "{temp_path}"'
        
        if use_admin:
            return run_as_admin(ps_command)
        else:
            startupinfo = None
            if not show_window and sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
            
            subprocess.Popen(ps_command, shell=True, startupinfo=startupinfo)

        threading.Timer(10.0, lambda: os.remove(temp_path)).start()
        return True
    except Exception as e:
        logger.error(f"Error running PowerShell script: {e}")
        return False

def run_batch_script(command, use_admin=False, show_window=True):
    """Run a batch script"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bat', mode='w') as temp:
            temp.write(command)
            temp_path = temp.name
        
        if use_admin:
            return run_as_admin(temp_path)
        else:
            startupinfo = None
            if not show_window and sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
            
            subprocess.Popen(temp_path, shell=True, startupinfo=startupinfo)
        
        threading.Timer(10.0, lambda: os.remove(temp_path)).start()
        return True
    except Exception as e:
        logger.error(f"Error running batch script: {e}")
        return False

def run_shell_script(command, use_admin=False, show_window=True):
    """Run a shell script (for Unix-like systems)"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sh', mode='w') as temp:
            temp.write(command)
            temp_path = temp.name

        os.chmod(temp_path, 0o755)
        
        if use_admin:
            return run_as_admin(temp_path)
        else:
            if show_window:
                if sys.platform == 'darwin':
                    subprocess.Popen(['open', '-a', 'Terminal.app', temp_path])
                else:
                    for terminal in ['gnome-terminal', 'xterm', 'konsole']:
                        try:
                            subprocess.Popen([terminal, '-e', temp_path])
                            break
                        except FileNotFoundError:
                            continue
            else:
                subprocess.Popen(['/bin/sh', temp_path])

        threading.Timer(10.0, lambda: os.remove(temp_path)).start()
        return True
    except Exception as e:
        logger.error(f"Error running shell script: {e}")
        return False

def execute_command(keyword, mappings):
    """Execute a command or script associated with a keyword"""
    if not mappings or keyword not in mappings:
        logger.error(f"Keyword '{keyword}' not found in mappings")
        return False

    try:
        value = mappings[keyword]

        if isinstance(value, str):
            command = value
            is_script = False
            show_window = True
        elif isinstance(value, dict):
            command = value.get('command', '')
            is_script = value.get('is_script', False)
            run_as_admin_flag = value.get('run_as_admin', False)  # Renamed to avoid shadowing function
            show_window = value.get('show_window', True)
        else:
            logger.error(f"Invalid mapping value type for keyword '{keyword}': {type(value)}")
            return False
        
        if not command:
            logger.error(f"Empty command for keyword '{keyword}'")
            return False
            
        logger.info(f"Executing command for keyword '{keyword}': {command}")
        
        if is_script:
            if run_as_admin_flag:
                # Pass only the actual command, not 'cmd /c ...'
                # Remove any accidental 'cmd /c' prefix from command
                if command.strip().lower().startswith('cmd /c '):
                    command = command.strip()[7:].strip('"')
                return run_as_admin(command)
            else:
                script_type = detect_script_type(command)
                logger.info(f"Detected script type: {script_type}")
                
                if script_type == "python":
                    return run_python_script(command, show_window)
                elif script_type == "powershell":
                    return run_powershell_script(command, run_as_admin_flag, show_window)
                elif script_type == "batch":
                    return run_batch_script(command, run_as_admin_flag, show_window)
                elif script_type == "shell":
                    return run_shell_script(command, run_as_admin_flag, show_window)
                else:
                    if sys.platform == 'win32':
                        return run_batch_script(command, run_as_admin_flag, show_window)
        else:
            if sys.platform == 'win32':
                if run_as_admin_flag:
                    # Pass command to run_as_admin
                    return run_as_admin(f'cmd /c "{command}"')
                else:
                    import subprocess
                    try:
                        if show_window:
                            subprocess.Popen(f'cmd /c "{command}"', creationflags=0x10)
                        else:
                            subprocess.Popen(
                                f'cmd /c "{command}"', 
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                        return True
                    except Exception as e:
                        logger.error(f"Error executing command: {e}")
                        return False
    except Exception as e:
        logger.error(f"Error in execute_command for keyword '{keyword}': {e}", exc_info=True)
        return False