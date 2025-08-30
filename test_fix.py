#!/usr/bin/env python3
"""
Test the fixed executable to verify the onboarding wizard and config fixes
"""
import os
import sys
import subprocess
import time
import json
import logging

def test_executable_fix():
    """Test the built executable with our fixes"""
    print("Testing KeywordAutomator executable fixes...")
    print("=" * 50)
    
    exe_path = "dist/KeywordAutomator.exe"
    
    if not os.path.exists(exe_path):
        print("❌ Executable not found at dist/KeywordAutomator.exe")
        return False
    
    print(f"✅ Executable found: {exe_path}")
    
    # Test 1: Check if config will be created in the right location
    print("\n🧪 Test 1: Checking config file handling...")
    
    # Find where the config will be stored
    import tempfile
    temp_dir = tempfile.gettempdir()
    print(f"   Temporary directory: {temp_dir}")
    
    # Test 2: Start the executable and check if wizard shows
    print("\n🧪 Test 2: Testing first-time startup (should show wizard)...")
    try:
        proc = subprocess.Popen([exe_path, "--debug"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        print("   Started executable with new console window")
        print("   ⚠️  Check the new console window for:")
        print("      - Onboarding wizard should appear")
        print("      - Next button should be visible and clickable")
        print("      - Complete the wizard to test config saving")
        
        # Wait for user to test
        input("\n   Press Enter after testing the wizard (or Ctrl+C to stop)...")
        
        # Kill the process
        proc.terminate()
        time.sleep(1)
        if proc.poll() is None:
            proc.kill()
            
    except KeyboardInterrupt:
        print("\n   Test interrupted by user")
        if 'proc' in locals():
            proc.terminate()
        return False
    except Exception as e:
        print(f"   ❌ Failed to start executable: {e}")
        return False
    
    # Test 3: Start again to see if wizard is skipped
    print("\n🧪 Test 3: Testing second startup (should skip wizard)...")
    try:
        proc = subprocess.Popen([exe_path, "--debug"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        print("   Started executable again with new console window")
        print("   ⚠️  Check the new console window for:")
        print("      - Wizard should NOT appear this time")
        print("      - Main window should open directly")
        
        # Wait for user to verify
        input("\n   Press Enter after verifying (or Ctrl+C to stop)...")
        
        # Kill the process
        proc.terminate()
        time.sleep(1)
        if proc.poll() is None:
            proc.kill()
            
    except KeyboardInterrupt:
        print("\n   Test interrupted by user")
        if 'proc' in locals():
            proc.terminate()
        return False
    except Exception as e:
        print(f"   ❌ Failed to start executable: {e}")
        return False
    
    print("\n✅ Testing completed!")
    print("\nExpected Results:")
    print("1. First run: Onboarding wizard appears with working Next button")
    print("2. Wizard completion: Config gets saved properly")
    print("3. Second run: No wizard, goes directly to main app")
    
    return True

def find_config_files():
    """Find any config files that might exist"""
    print("\n🔍 Searching for config files...")
    
    # Check common locations
    locations = [
        "assets/config.json",
        "config.json",
    ]
    
    # Check user config directory
    try:
        import appdirs
        user_config = appdirs.user_config_dir("KeywordAutomator", "Prakhar Jaiswal")
        locations.append(os.path.join(user_config, "config.json"))
    except:
        pass
    
    found_configs = []
    for location in locations:
        if os.path.exists(location):
            found_configs.append(location)
            print(f"   ✅ Found: {location}")
            try:
                with open(location, 'r') as f:
                    config = json.load(f)
                    print(f"      has_seen_welcome: {config.get('has_seen_welcome', 'Not set')}")
                    print(f"      wizard_completed: {config.get('wizard_completed', 'Not set')}")
            except Exception as e:
                print(f"      ❌ Error reading: {e}")
        else:
            print(f"   ❌ Not found: {location}")
    
    return found_configs

if __name__ == "__main__":
    print("KeywordAutomator Fix Test")
    print("=" * 40)
    
    # Search for existing configs
    configs = find_config_files()
    
    if configs:
        print(f"\n⚠️  Found {len(configs)} existing config file(s)")
        choice = input("Delete them to test fresh install? (y/N): ").lower().strip()
        if choice == 'y':
            for config_file in configs:
                try:
                    os.remove(config_file)
                    print(f"   🗑️  Deleted: {config_file}")
                except Exception as e:
                    print(f"   ❌ Failed to delete {config_file}: {e}")
    
    # Run the test
    if test_executable_fix():
        print("\n🎉 Test completed! Check the results above.")
        sys.exit(0)
    else:
        print("\n❌ Test failed")
        sys.exit(1)
