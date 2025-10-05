# Autocompelete (Keyword Automator)

A Windows-focused desktop utility to create custom keywords and hotkeys that launch apps, run scripts (PowerShell, Python, Batch), or open websites. Includes a global hotkey, system tray integration, onboarding wizard, and an in-app help system.

## Features
- Global hotkey to open a quick command palette (default: Ctrl+Alt+K)
- Map keywords to commands or scripts; optional per-keyword hotkeys
- PowerShell/Python/Batch script support, with optional Run as Administrator
- System tray icon with quick actions (pystray)
- Theming (system, light, dark)
- Onboarding wizard and interactive help/documentation
- Robust error handling with logs and friendly dialogs

## Requirements
- Windows 10/11
- Python 3.11+ (for development)
- Packages: see `requirements.txt`

## Getting Started (Development)
1. Create and activate a virtual environment
2. Install dependencies
3. Run the app

```pwsh
# From project root
python -m venv env
./env/Scripts/Activate.ps1
pip install -r requirements.txt
python launch_direct.py --debug
```

Global hotkey opens the input dialog; type your keyword and press Enter.

## Packaging (PyInstaller)
Generate a standalone Windows executable:

```pwsh
./env/Scripts/Activate.ps1
pip install -r requirements.txt
pyinstaller --noconfirm --noconsole --name "KeywordAutomator" --icon assets/icon.ico run.py
```

Artifacts will be in `build/` and `dist/`. These are ignored by git.

## Project Structure
```
/Autocompelete
  |-- src/                # All application source code
  |-- assets/             # Icons and static assets
  |-- build/, dist/       # PyInstaller output (ignored)
  |-- env/                # Virtual environment (ignored)
  |-- run.py              # App entry (direct launcher)
  |-- main.py             # Main module (invoked by launcher)
  |-- requirements.txt
  |-- .gitignore
  |-- README.md
```

## Configuration
- Config file is stored next to the packaged EXE, or under the user config dir in dev.
- Use File > Import/Export Settings in the app UI.

## Security & Permissions
- Dangerous admin actions require confirmation.
- Admin actions and errors are logged to `keyword_automator_errors.log`.

## Troubleshooting
- View logs via Help > View Error Log.
- If the tray icon fails, the app stays usable and notifies you.
- See Help > Troubleshooting inside the app for common fixes.

## Contributing
At this stage, we're focusing on stability and UX improvements. PRs with small, focused enhancements are welcome.
