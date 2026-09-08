import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "default_voice": "vi-VN-NamMinhNeural",
    "speech_rate": "+0%",
    "speech_pitch": "+0Hz",
    "output_dir": str(BASE_DIR / "output"),
    "theme": "dark",
    "font_name": "Montserrat-Black.ttf",
    "fps": 30,
    "video_width": 1080,
    "video_height": 1920,
    "pexels_api_key": ""
}

def load_config() -> dict:
    """Load configuration from config.json with fallback to defaults."""
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with default keys if missing
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception as e:
        print(f"[Config] Error loading config: {e}. Using defaults.")
        return DEFAULT_CONFIG.copy()

def save_config(config_data: dict) -> bool:
    """Save configuration dictionary to config.json."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Config] Error saving config: {e}")
        return False

def get_config_value(key: str, default=None):
    """Get a single configuration value by key."""
    config = load_config()
    return config.get(key, default)

def set_config_value(key: str, value) -> bool:
    """Update a single configuration key and save."""
    config = load_config()
    config[key] = value
    return save_config(config)
