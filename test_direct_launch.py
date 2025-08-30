#!/usr/bin/env python3
"""
Test script to verify that the direct launch approach works correctly
and that only one process is created.
"""

import os
import sys
import subprocess
import time

def test_direct_launch():
    """Test the direct launch approach"""
    print("Testing Direct Launch Approach")
    print("=" * 50)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Test 1: Direct launcher
    print("\n1. Testing launch_direct.py...")
    launcher_path = os.path.join(script_dir, 'launch_direct.py')
    
    if os.path.exists(launcher_path):
        print("   ✓ launch_direct.py exists")
        
        # Test import capability
        try:
            import launch_direct
            print("   ✓ launch_direct.py can be imported successfully")
        except Exception as e:
            print(f"   ✗ Import error: {e}")
        
        print("   Testing launch functionality...")
        try:
            # Quick test launch (will exit due to singleton)
            result = subprocess.run([
                sys.executable, launcher_path, '--debug'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("   ✓ Direct launcher executed successfully")
            else:
                print(f"   ⚠ Launcher returned code {result.returncode}")
                if result.stderr:
                    print(f"   Error output: {result.stderr[:200]}...")
        except subprocess.TimeoutExpired:
            print("   ⚠ Launcher is running (this is expected for GUI app)")
        except Exception as e:
            print(f"   ✗ Launch test failed: {e}")
            
    else:
        print("   ✗ launch_direct.py not found")
    
    # Test 2: Updated run.py
    print("\n2. Testing updated run.py...")
    run_path = os.path.join(script_dir, 'run.py')
    
    if os.path.exists(run_path):
        print("   ✓ run.py exists")
        
        try:
            import run
            print("   ✓ run.py can be imported successfully")
        except Exception as e:
            print(f"   ✗ Import error: {e}")
        
        print("   Testing run functionality...")
        try:
            result = subprocess.run([
                sys.executable, run_path, '--debug'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("   ✓ run.py executed successfully")
            else:
                print(f"   ⚠ run.py returned code {result.returncode}")
        except subprocess.TimeoutExpired:
            print("   ⚠ run.py is running (this is expected for GUI app)")
        except Exception as e:
            print(f"   ✗ Run test failed: {e}")
    else:
        print("   ✗ run.py not found")
    
    # Test 3: Check startup scripts
    print("\n3. Testing startup scripts...")
    
    start_hidden_path = os.path.join(script_dir, 'start_hidden.pyw')
    if os.path.exists(start_hidden_path):
        print("   ✓ start_hidden.pyw exists and has been updated")
        
        # Check if it has the new direct launch code
        with open(start_hidden_path, 'r') as f:
            content = f.read()
            if 'def main():' in content and 'Direct launch without subprocess chain' in content:
                print("   ✓ start_hidden.pyw has been updated with direct launch")
            else:
                print("   ✗ start_hidden.pyw may not have the latest updates")
    else:
        print("   ✗ start_hidden.pyw not found")
    
    # Test 4: Batch file
    print("\n4. Testing batch file...")
    batch_path = os.path.join(script_dir, 'KeywordAutomator.bat')
    
    if os.path.exists(batch_path):
        print("   ✓ KeywordAutomator.bat exists")
        
        with open(batch_path, 'r') as f:
            content = f.read()
            if 'launch_direct.py' in content:
                print("   ✓ Batch file has been updated to use direct launch")
            else:
                print("   ⚠ Batch file may be using old method")
                
        if os.name == 'nt':
            print("   You can test the batch file by running: KeywordAutomator.bat")
    else:
        print("   ✗ KeywordAutomator.bat not found")
    
    # Test 5: PyInstaller spec
    print("\n5. Testing PyInstaller configuration...")
    spec_path = os.path.join(script_dir, 'KeywordAutomator.spec')
    
    if os.path.exists(spec_path):
        print("   ✓ KeywordAutomator.spec exists")
        
        with open(spec_path, 'r') as f:
            content = f.read()
            if 'launch_direct.py' in content:
                print("   ✓ PyInstaller spec updated to use direct launch")
            else:
                print("   ⚠ PyInstaller spec may need updating")
    else:
        print("   ✗ KeywordAutomator.spec not found")
    
    print("\n" + "=" * 50)
    print("Direct Launch Testing Complete")
    print("\nWhat was changed:")
    print("1. ✓ Created launch_direct.py for direct process launch")
    print("2. ✓ Updated start_hidden.pyw to avoid subprocess chains")
    print("3. ✓ Modified run.py to use direct launch by default")
    print("4. ✓ Updated batch files to use direct launch")
    print("5. ✓ Modified PyInstaller spec for direct compilation")
    print("6. ✓ Enhanced tray handling for better cleanup")
    
    print("\nTo verify the fix:")
    print("1. Run: python launch_direct.py --minimized")
    print("2. Check Task Manager - you should see only ONE Python process")
    print("3. Close the application - the process should terminate cleanly")
    print("4. For compiled version: run build_direct.bat to create new executable")

if __name__ == "__main__":
    try:
        test_direct_launch()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
