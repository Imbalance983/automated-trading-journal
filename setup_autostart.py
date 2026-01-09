import os
import sys
import getpass
from pathlib import Path

def setup_autostart():
    """Setup Trading Journal to auto-start on Windows login"""
    print("\n" + "="*60)
    print("Trading Journal Auto-Start Setup")
    print("="*60 + "\n")

    # Get current app directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    username = getpass.getuser()

    print(f"App Directory: {app_dir}")
    print(f"Current User: {username}\n")

    # 1. Create batch file to start the app
    batch_content = f'''@echo off
cd /d "{app_dir}"
python app.py
pause
'''

    batch_path = os.path.join(app_dir, "start_trading_journal.bat")
    try:
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        print(f"[OK] Created batch file: {batch_path}")
    except Exception as e:
        print(f"[ERROR] Failed to create batch file: {e}")
        return False

    # 2. Create shortcut in Startup folder
    startup_folder = f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"

    # Verify startup folder exists
    if not os.path.exists(startup_folder):
        print(f"[ERROR] Startup folder not found: {startup_folder}")
        return False

    print(f"Startup Folder: {startup_folder}")

    # Create VBS script to create shortcut (works without admin rights)
    shortcut_content = f'''Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{startup_folder}\\Trading Journal.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{batch_path}"
oLink.WorkingDirectory = "{app_dir}"
oLink.Description = "Automated Trading Journal - Auto Start"
oLink.Save
'''

    vbs_path = os.path.join(app_dir, "create_shortcut.vbs")
    try:
        with open(vbs_path, 'w') as f:
            f.write(shortcut_content)

        # Run the VBS script to create shortcut
        result = os.system(f'cscript //nologo "{vbs_path}"')

        if result == 0:
            print(f"[OK] Shortcut created in Startup folder")
        else:
            print(f"[WARNING] VBS script ran but returned code: {result}")

        # Clean up VBS file
        if os.path.exists(vbs_path):
            os.remove(vbs_path)
            print(f"[OK] Cleaned up temporary VBS file")

    except Exception as e:
        print(f"[ERROR] Failed to create shortcut: {e}")
        return False

    # 3. Success message
    print("\n" + "="*60)
    print("[SUCCESS] AUTO-START SETUP COMPLETE!")
    print("="*60 + "\n")

    print("What happens now:")
    print("   1. App will auto-start when you login to Windows")
    print("   2. A command window will open automatically")
    print("   3. Access the app at: http://localhost:5000")
    print("   4. Close command window to stop the app\n")

    print("Files created:")
    print(f"   - {batch_path}")
    print(f"   - {startup_folder}\\Trading Journal.lnk\n")

    print("To disable auto-start:")
    print(f"   - Delete: {startup_folder}\\Trading Journal.lnk\n")

    print("To test now:")
    print(f"   - Double-click: {batch_path}")
    print("   - Or run: python app.py\n")

    return True

if __name__ == "__main__":
    try:
        success = setup_autostart()
        if not success:
            print("\n[ERROR] Setup failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
