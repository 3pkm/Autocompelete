@echo off
REM Direct launch batch file for Keyword Automator (starts minimized)
REM This runs the application directly without process chains

REM Run main.py directly with minimized flag
python.exe "%~dp0main.py" --minimized %*
