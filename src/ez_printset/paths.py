import os
import platform
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
DEFAULT_PRESETS_PATH = BUNDLE_ROOT / "profiles" / "presets.json"
APP_ICON_PATH = BUNDLE_ROOT / "assets" / "app.ico"

if platform.system() == "Windows":
    appdata = Path(os.environ.get("APPDATA", Path.home()))
    PRESETS_PATH = appdata / "EZ-PrintSet" / "presets.json"
else:
    PRESETS_PATH = PROJECT_ROOT / "profiles" / "presets.json"
