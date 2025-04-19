import subprocess

def execute_command(keyword, mappings):
    if keyword in mappings:
        command = mappings[keyword]
        try:
            subprocess.Popen(command, shell=True)
            return True
        except Exception as e:
            print(f"Error executing command: {e}")
            return False
    return False