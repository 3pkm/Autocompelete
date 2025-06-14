@echo off
echo Building Keyword Automator executable...

REM Activate virtual environment if it exists
if exist env\Scripts\activate.bat (
    call env\Scripts\activate.bat
    echo Using virtual environment for build
) else (
    echo No virtual environment found, using system Python
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if %ERRORLEVEL% neq 0 (
    echo PyInstaller not found, installing...
    pip install pyinstaller
)

REM Make sure src directory has __init__.py
if not exist src\__init__.py (
    echo Creating __init__.py in src directory...
    echo """KeywordAutomator package.""" > src\__init__.py
)

REM Create the executable
echo Building executable with PyInstaller...
pyinstaller --name "KeywordAutomator" ^
            --icon=assets/icon.ico ^
            --windowed ^
            --add-data "assets;assets" ^
            --add-data "scripts;scripts" ^
            --paths "src" ^
            --hidden-import=pystray._win32 ^
            --hidden-import=PIL._tkinter_finder ^
            run.py

echo Build complete! Executable is in the dist/KeywordAutomator folder

pause
