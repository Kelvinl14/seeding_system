import sys
from pathlib import Path

def resource_path(relative_path: str) -> Path:
    """
    Resolve paths tanto em dev quanto em executável PyInstaller
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parents[2] / relative_path
