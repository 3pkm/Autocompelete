@echo off
echo Testing KeywordAutomator Duplicate Process Fix
echo =============================================

REM Clean up any existing config files
if exist "dist\KeywordAutomator\config.json" (
    echo Removing existing config file...
    del "dist\KeywordAutomator\config.json"
)

echo.
echo Step 1: Testing Singleton Behavior
echo Starting KeywordAutomator...
echo.

start "" "dist\KeywordAutomator\KeywordAutomator.exe" --debug

echo First instance started. Now trying to start a second instance...
echo This should show a message that the app is already running.
echo.
pause

start "" "dist\KeywordAutomator\KeywordAutomator.exe" --debug

echo.
echo Check if:
echo - A message appeared saying "Already Running"
echo - Only ONE process is visible in Task Manager
echo - System tray shows only ONE icon
echo.
echo Press any key after checking...
pause

echo.
echo Step 2: Testing Process Termination
echo Close the application and check if both instances close properly.
echo.
pause

echo.
echo Test completed! Results:
echo ✅ SUCCESS: Only one instance runs, second shows "already running" message
echo ❌ FAILED: Two instances still running simultaneously
echo.
pause
