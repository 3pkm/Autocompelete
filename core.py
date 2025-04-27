import subprocess
import tempfile
import os
import sys

def execute_command(keyword, mappings):
    if keyword in mappings:
        value = mappings[keyword]
        
        # Handle both old format (string command) and new format (dict with command and is_script)
        if isinstance(value, dict):
            command = value.get('command', '')
            is_script = value.get('is_script', False)
        else:
            # Legacy support for old format
            command = value
            is_script = False

        try:
            if is_script and sys.platform == 'win32':
                # For complex PowerShell scripts, create a temporary .ps1 file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.ps1', mode='w') as temp:
                    temp.write(command)
                    temp_path = temp.name
                
                # Execute the PowerShell script
                powershell_cmd = f'powershell.exe -ExecutionPolicy Bypass -File "{temp_path}"'
                subprocess.Popen(powershell_cmd, shell=True)
                
                # Schedule the temp file for deletion after execution
                # We don't delete immediately to ensure the script has time to run
                def delete_temp_file():
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                
                # Use a simple timer to delete the file after 10 seconds
                import threading
                threading.Timer(10.0, delete_temp_file).start()
            else:
                # For simple commands, execute directly
                subprocess.Popen(command, shell=True)
            
            return True
        except Exception as e:
            print(f"Error executing command: {e}")
            return False
    return False