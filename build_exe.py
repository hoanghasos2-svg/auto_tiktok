import os
import sys
import subprocess
from pathlib import Path
import customtkinter

BASE_DIR = Path(__file__).resolve().parent
ctk_path = os.path.dirname(customtkinter.__file__)

def build_standalone_exe():
    print("=======================================================")
    print("   DANG DONG GOI UNG DUNG BANG PYINSTALLER...")
    print("=======================================================")
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "AutoShortsMaker_Standalone",
        "--icon", str(BASE_DIR / "assets" / "icon.ico"),
        "--add-data", f"{ctk_path};customtkinter/",
        "--add-data", f"{str(BASE_DIR / 'assets')};assets/",
        "--add-data", f"{str(BASE_DIR / 'config.json')};.",
        "main.py"
    ]
    
    print("Lenh thuc thi:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("\n[THANH CONG] Ung dung standalone da duoc tao trong thu muc: dist/AutoShortsMaker_Standalone/")

if __name__ == "__main__":
    build_standalone_exe()