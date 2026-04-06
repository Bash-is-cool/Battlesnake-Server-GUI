import os
import sys


def get_resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

        if not os.path.exists(os.path.join(base_path, relative_path)):
            parent_dir = os.path.dirname(base_path)
            if os.path.exists(os.path.join(parent_dir, relative_path)):
                base_path = parent_dir

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