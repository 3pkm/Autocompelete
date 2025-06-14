import sys
import os
import subprocess

if __name__ == "__main__":
    script_dir = os.path.abspath(os.path.dirname(__file__))

    run_script = os.path.join(script_dir, "run.py")
    
    pythonw_exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")

    cmd = [pythonw_exe, run_script, "--minimized"]

    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    subprocess.Popen(cmd, close_fds=True, shell=False)
