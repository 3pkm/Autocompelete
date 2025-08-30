@echo off
REM Direct launch batch file for Keyword Automator
REM This runs the application directly without process chains

REM Run main.py directly to avoid subprocess chains
python.exe "%~dp0main.py" %*
