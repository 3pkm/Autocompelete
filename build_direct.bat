@echo off
REM Build script for Keyword Automator using direct launch approach
REM This script builds the application without process chains

echo Building Keyword Automator with Direct Launch approach...
echo.

REM Activate virtual environment if it exists
if exist "env\Scripts\activate.bat" (
    echo Activating virtual environment...
    call env\Scripts\activate.bat
) else (
    echo Virtual environment not found, using system Python...
)

REM Clean previous build
if exist "build" (
    echo Cleaning previous build directory...
    rmdir /s /q build
)

if exist "dist" (
    echo Cleaning previous dist directory...
    rmdir /s /q dist
)

REM Build with PyInstaller using the updated spec
echo.
echo Building executable...
pyinstaller KeywordAutomator.spec --clean

REM Check if build was successful
if exist "dist\KeywordAutomator\KeywordAutomator.exe" (
    echo.
    echo ✓ Build completed successfully!
    echo ✓ Executable location: dist\KeywordAutomator\KeywordAutomator.exe
    echo.
    echo The new build uses direct launch approach to avoid multiple processes.
    echo You can now run the executable directly without process chains.
) else (
    echo.
    echo ✗ Build failed! Check the output above for errors.
    echo.
    exit /b 1
)

echo.
echo Build process completed.
pause
