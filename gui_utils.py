import os
import sys

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.\\
    - Dev: script is in /Learning, resources in /resources
    - Bundled: Everything is in the root or _MEIPASS
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If running as script in /Directory, go up one level to find /resources
        # If the script calling this is in the ROOT, remove the second dirname
        caller_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        base_path = os.path.dirname(caller_dir)

    return os.path.normpath(os.path.join(base_path, relative_path))

def init_windows_appid(appid: str):
    """
    Sets the AppUserModelID so the taskbar icon shows up on Windows.
    Safe to call on any platform.
    """
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
        except Exception as e:
            print(f"Failed to set Windows AppID: {e}")