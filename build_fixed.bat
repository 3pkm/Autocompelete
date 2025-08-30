@echo off
echo Building Keyword Automator executable with PyInstaller fixes...

REM Activate virtual environment if it exists
if exist env\Scripts\activate.bat (
    call env\Scripts\activate.bat
    echo Using virtual environment for build
) else (
    echo No virtual environment found, using system Python
)

REM Install required packages for PyInstaller
echo Installing required packages...
pip install pyinstaller pillow pystray

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM Create the executable with proper settings for system tray
echo Building executable with PyInstaller...
pyinstaller --name "KeywordAutomator" ^
            --windowed ^
            --icon=assets/icon.ico ^
            --add-data "assets;assets" ^
            --hidden-import=pystray._win32 ^
            --hidden-import=PIL._tkinter_finder ^
            --hidden-import=PIL ^
            --hidden-import=PIL.Image ^
            --hidden-import=PIL.ImageDraw ^
            --hidden-import=pystray ^
            --hidden-import=threading ^
            --collect-all=pystray ^
            main.py

echo Build complete! 
echo Executable is in the dist folder: dist\KeywordAutomator\KeywordAutomator.exe
echo.
echo Testing the executable...
if exist dist\KeywordAutomator\KeywordAutomator.exe (
    echo ✓ Executable created successfully
    echo.
    echo You can now run: dist\KeywordAutomator\KeywordAutomator.exe
    echo Or run minimized: dist\KeywordAutomator\KeywordAutomator.exe --minimized
) else (
    echo ✗ Build failed - executable not found
    echo Check the output above for errors
)

pause
