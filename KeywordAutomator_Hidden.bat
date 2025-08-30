@echo off
REM Hidden startup batch file for Keyword Automator
REM Starts the application minimized to system tray without console window

REM Use pythonw.exe to avoid console window
if exist "%~dp0launch_direct.py" (
    REM Use direct launcher if available
    pythonw.exe "%~dp0launch_direct.py" --minimized %*
) else (
    REM Fallback to run.py
    pythonw.exe "%~dp0run.py" --minimized %*
)
