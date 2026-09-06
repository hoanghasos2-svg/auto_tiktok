import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import asset_manager
from gui import run_app

def main():
    print("=" * 60)
    print("   AUTO SHORTS / REELS MAKER 9:16 - AI COMPARISON (0 VND)")
    print("=" * 60)
    print("[Main] Đang khởi tạo tài nguyên hệ thống...")
    asset_manager.init_all_assets()
    print("[Main] Đang mở giao diện ứng dụng...")
    run_app()

if __name__ == "__main__":
    main()