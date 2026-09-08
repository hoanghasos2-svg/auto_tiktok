import os
import math
import struct
import wave
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
BG_DIR = ASSETS_DIR / "backgrounds"
MASCOT_DIR = ASSETS_DIR / "mascot"
SFX_DIR = ASSETS_DIR / "sfx"
BGM_DIR = ASSETS_DIR / "bgm"
FONTS_DIR = ASSETS_DIR / "fonts"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

def ensure_directories():
    """Ensure all required directories exist."""
    for d in [BG_DIR, MASCOT_DIR, SFX_DIR, BGM_DIR, FONTS_DIR, OUTPUT_DIR, TEMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def create_default_background(filepath: Path, width=1080, height=1920):
    """Create a high-aesthetic modern paper/gradient background."""
    img = Image.new("RGB", (width, height), color="#12151E")
    draw = ImageDraw.Draw(img)
    
    top_color = (20, 24, 38)
    bottom_color = (11, 13, 20)
    
    for y in range(height):
        factor = y / height
        r = int(top_color[0] * (1 - factor) + bottom_color[0] * factor)
        g = int(top_color[1] * (1 - factor) + bottom_color[1] * factor)
        b = int(top_color[2] * (1 - factor) + bottom_color[2] * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    grid_color = (255, 255, 255, 12)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    step = 80
    for x in range(0, width, step):
        overlay_draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, step):
        overlay_draw.line([(0, y), (width, y)], fill=grid_color, width=1)
        
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        [width * 0.1, height * 0.15, width * 0.9, height * 0.85],
        fill=(59, 130, 246, 22)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    img = Image.alpha_composite(img, glow)
    
    img.convert("RGB").save(filepath, "PNG", quality=95)
    print(f"[AssetManager] Created default background: {filepath.name}")

def draw_cute_mascot(pose: str, filepath: Path, width=600, height=700):
    """Draw an expressive high-res 2D mascot character in 4 distinct poses."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = width // 2, height // 2 + 50
    
    body_color = "#3B82F6"
    belly_color = "#93C5FD"
    face_color = "#FFFFFF"
    shadow_color = (0, 0, 0, 40)
    blush_color = "#F472B6"
    
    # 1. Base Shadow
    draw.ellipse([cx - 160, height - 80, cx + 160, height - 30], fill=shadow_color)
    
    # 2. Body
    body_bbox = [cx - 150, cy - 130, cx + 150, cy + 220]
    draw.rounded_rectangle(body_bbox, radius=110, fill=body_color, outline="#1E40AF", width=6)
    draw.ellipse([cx - 95, cy + 10, cx + 95, cy + 170], fill=belly_color)
    
    # 3. Head / Screen
    head_bbox = [cx - 170, cy - 250, cx + 170, cy - 40]
    draw.rounded_rectangle(head_bbox, radius=70, fill="#1E293B", outline="#0F172A", width=8)
    screen_bbox = [cx - 150, cy - 230, cx + 150, cy - 60]
    draw.rounded_rectangle(screen_bbox, radius=55, fill="#0F172A")
    
    draw.line([(cx, cy - 250), (cx, cy - 300)], fill="#1E40AF", width=8)
    draw.ellipse([cx - 20, cy - 330, cx + 20, cy - 290], fill="#F59E0B", outline="#D97706", width=4)
    
    draw.ellipse([cx - 125, cy - 115, cx - 85, cy - 90], fill=blush_color)
    draw.ellipse([cx + 85, cy - 115, cx + 125, cy - 90], fill=blush_color)
    
    # 4. Expressions & Poses
    if pose == "pointing":
        draw.ellipse([cx - 90, cy - 170, cx - 45, cy - 110], fill="#38BDF8")
        draw.ellipse([cx - 75, cy - 160, cx - 55, cy - 135], fill="#FFFFFF")
        draw.ellipse([cx + 45, cy - 170, cx + 90, cy - 110], fill="#38BDF8")
        draw.ellipse([cx + 60, cy - 160, cx + 80, cy - 135], fill="#FFFFFF")
        
        draw.arc([cx - 35, cy - 120, cx + 35, cy - 80], start=10, end=170, fill="#FFFFFF", width=6)
        
        draw.line([(cx + 120, cy + 30), (cx + 220, cy - 120)], fill=body_color, width=32)
        draw.ellipse([cx + 205, cy - 140, cx + 245, cy - 100], fill="#F59E0B")
        draw.line([(cx + 225, cy - 120), (cx + 270, cy - 270)], fill="#E2E8F0", width=8)
        draw.polygon([(cx + 270, cy - 290), (cx + 258, cy - 265), (cx + 282, cy - 265)], fill="#EF4444")
        
        draw.arc([cx - 200, cy - 10, cx - 100, cy + 90], start=90, end=270, fill=body_color, width=30)
        
    elif pose == "thinking":
        draw.ellipse([cx - 85, cy - 180, cx - 45, cy - 130], fill="#38BDF8")
        draw.ellipse([cx - 75, cy - 175, cx - 55, cy - 150], fill="#FFFFFF")
        draw.arc([cx + 45, cy - 160, cx + 90, cy - 130], start=190, end=350, fill="#38BDF8", width=6)
        
        draw.ellipse([cx - 15, cy - 105, cx + 15, cy - 85], fill="#FFFFFF")
        
        draw.arc([cx + 60, cy - 40, cx + 180, cy + 70], start=200, end=350, fill=body_color, width=30)
        draw.ellipse([cx + 40, cy - 80, cx + 90, cy - 35], fill=body_color, outline="#1E40AF", width=4)
        
        draw.arc([cx - 190, cy + 20, cx - 110, cy + 120], start=100, end=260, fill=body_color, width=28)
        
        draw.ellipse([cx + 170, cy - 240, cx + 185, cy - 225], fill="#F59E0B")
        draw.ellipse([cx + 195, cy - 280, cx + 215, cy - 260], fill="#F59E0B")
        draw.ellipse([cx + 225, cy - 330, cx + 255, cy - 295], fill="#F59E0B")
        
    elif pose == "chill":
        draw.arc([cx - 95, cy - 160, cx - 45, cy - 120], start=200, end=340, fill="#38BDF8", width=7)
        draw.arc([cx + 45, cy - 160, cx + 95, cy - 120], start=200, end=340, fill="#38BDF8", width=7)
        
        draw.chord([cx - 40, cy - 120, cx + 40, cy - 65], start=0, end=180, fill="#EF4444", outline="#FFFFFF", width=4)
        
        draw.arc([cx + 90, cy - 20, cx + 190, cy + 90], start=220, end=360, fill=body_color, width=30)
        draw.polygon([(cx + 145, cy + 20), (cx + 195, cy + 20), (cx + 185, cy + 85), (cx + 155, cy + 85)], fill="#F8FAFC", outline="#CBD5E1", width=3)
        draw.rectangle([cx + 165, cy - 5, cx + 175, cy + 20], fill="#10B981")
        
        draw.arc([cx - 200, cy - 50, cx - 110, cy + 50], start=120, end=270, fill=body_color, width=28)
        draw.ellipse([cx - 215, cy - 60, cx - 170, cy - 15], fill=body_color)
        
    elif pose == "cta":
        draw.ellipse([cx - 95, cy - 175, cx - 40, cy - 105], fill="#38BDF8")
        draw.ellipse([cx - 75, cy - 160, cx - 55, cy - 135], fill="#FFFFFF")
        draw.ellipse([cx + 40, cy - 175, cx + 95, cy - 105], fill="#38BDF8")
        draw.ellipse([cx + 60, cy - 160, cx + 80, cy - 135], fill="#FFFFFF")
        
        draw.chord([cx - 50, cy - 120, cx + 50, cy - 55], start=0, end=180, fill="#F59E0B", outline="#FFFFFF", width=5)
        
        draw.arc([cx - 210, cy - 60, cx - 110, cy + 40], start=90, end=270, fill=body_color, width=32)
        draw.ellipse([cx - 220, cy - 80, cx - 170, cy - 30], fill="#F59E0B", outline="#D97706", width=4)
        draw.arc([cx + 110, cy - 60, cx + 210, cy + 40], start=270, end=90, fill=body_color, width=32)
        draw.ellipse([cx + 170, cy - 80, cx + 220, cy - 30], fill="#F59E0B", outline="#D97706", width=4)

    img.save(filepath, "PNG")
    print(f"[AssetManager] Created mascot pose: {filepath.name}")

def generate_sfx_pop(filepath: Path):
    sample_rate = 44100
    duration = 0.12
    num_samples = int(sample_rate * duration)
    with wave.open(str(filepath), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for i in range(num_samples):
            t = i / sample_rate
            freq = 850 * math.exp(-35 * t) + 220
            envelope = math.exp(-28 * t)
            sample = math.sin(2 * math.pi * freq * t) * envelope
            int_sample = int(sample * 32767 * 0.9)
            wav.writeframes(struct.pack('<h', max(-32768, min(32767, int_sample))))

def generate_sfx_whoosh(filepath: Path):
    sample_rate = 44100
    duration = 0.35
    num_samples = int(sample_rate * duration)
    with wave.open(str(filepath), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for i in range(num_samples):
            t = i / sample_rate
            progress = t / duration
            freq = 200 + 700 * math.sin(math.pi * progress)
            envelope = math.sin(math.pi * progress) ** 2
            sample = (0.7 * math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(4 * math.pi * freq * t)) * envelope
            int_sample = int(sample * 32767 * 0.85)
            wav.writeframes(struct.pack('<h', max(-32768, min(32767, int_sample))))

def download_vietnamese_font():
    """Download Google Font BeVietnamPro designed specifically for Vietnamese diacritics."""
    vn_font_file = FONTS_DIR / "BeVietnamPro-ExtraBold.ttf"
    if vn_font_file.exists() and vn_font_file.stat().st_size > 10000:
        return vn_font_file
        
    try:
        import requests
        url = "https://raw.githubusercontent.com/google/fonts/main/ofl/bevietnampro/BeVietnamPro-ExtraBold.ttf"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(vn_font_file, "wb") as f:
                f.write(resp.content)
            print(f"[AssetManager] Downloaded Vietnamese font: {vn_font_file.name}")
            return vn_font_file
    except Exception as e:
        print(f"[AssetManager] BeVietnamPro download note: {e}")
        
    # Also check Montserrat
    mont_file = FONTS_DIR / "Montserrat-Black.ttf"
    if mont_file.exists():
        return mont_file
        
    return vn_font_file

def init_all_assets():
    ensure_directories()
    
    bg_file = BG_DIR / "paper_bg.png"
    if not bg_file.exists():
        create_default_background(bg_file)
        
    # Check category backgrounds
    from create_category_backgrounds import generate_all_backgrounds
    if not (BG_DIR / "bg_tech.png").exists() or not (BG_DIR / "bg_food.png").exists():
        generate_all_backgrounds()
        
    # Check category mascots
    from create_category_mascots import generate_all_category_mascots
    MASCOTS_DIR = ASSETS_DIR / "mascots"
    if not (MASCOTS_DIR / "food" / "pointing.png").exists() or not (MASCOTS_DIR / "tech" / "pointing.png").exists():
        generate_all_category_mascots()
        
    poses = ["pointing", "thinking", "chill", "cta"]
    for pose in poses:
        pfile = MASCOT_DIR / f"{pose}.png"
        if not pfile.exists():
            draw_cute_mascot(pose, pfile)
            
    bgm_file = BGM_DIR / "bgm_chill.wav"
    if not bgm_file.exists():
        generate_lofi_bgm(bgm_file, duration=60.0)

def generate_lofi_bgm(filepath: Optional[Path] = None, duration: float = 60.0, sample_rate: int = 44100) -> Path:
    """Tạo nhạc nền Lofi Chill Acoustic êm dịu, bản quyền miễn phí 100% (Numpy siêu tốc)."""
    if filepath is None:
        ensure_directories()
        filepath = BGM_DIR / "bgm_chill.wav"
    else:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
    import numpy as np
    chords = [
        [261.63, 329.63, 392.00, 493.88],  # Cmaj7
        [220.00, 261.63, 329.63, 392.00],  # Am7
        [293.66, 349.23, 440.00, 523.25],  # Dm7
        [196.00, 246.94, 293.66, 349.23],  # G7
    ]
    chord_len = 3.2
    total_samples = int(sample_rate * duration)
    full_audio = np.zeros(total_samples, dtype=np.float32)

    samples_per_chord = int(sample_rate * chord_len)
    chord_t = np.linspace(0, chord_len, samples_per_chord, endpoint=False)
    env = np.exp(-0.75 * chord_t) * np.minimum(1.0, chord_t * 15.0)

    current_idx = 0
    num_cycles = int(duration / (chord_len * len(chords))) + 1
    for _ in range(num_cycles):
        for chord in chords:
            if current_idx >= total_samples:
                break
            chunk_len = min(samples_per_chord, total_samples - current_idx)
            ct = chord_t[:chunk_len]
            c_env = env[:chunk_len]
            chunk = np.zeros(chunk_len, dtype=np.float32)
            for freq in chord:
                chunk += 0.45 * np.sin(2 * np.pi * freq * ct)
                chunk += 0.15 * np.sin(2 * np.pi * (freq * 2) * ct)
                chunk += 0.05 * np.sin(2 * np.pi * (freq * 3) * ct)
            chunk = (chunk / len(chord)) * c_env
            bass = 0.35 * np.sin(2 * np.pi * (chord[0] / 2) * ct) * c_env
            full_audio[current_idx:current_idx + chunk_len] = (chunk + bass) * 0.45
            current_idx += chunk_len

    int_audio = (full_audio * 32767 * 0.8).clip(-32768, 32767).astype(np.int16)
    with wave.open(str(filepath), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(int_audio.tobytes())
    print(f"[AssetManager] Created Lofi BGM: {filepath.name}")
    return filepath

def download_vietnamese_font():
    """Download Google Font BeVietnamPro designed specifically for Vietnamese diacritics."""
    vn_font_file = FONTS_DIR / "BeVietnamPro-ExtraBold.ttf"
    if vn_font_file.exists() and vn_font_file.stat().st_size > 10000:
        return vn_font_file
        
    try:
        import requests
        url = "https://raw.githubusercontent.com/google/fonts/main/ofl/bevietnampro/BeVietnamPro-ExtraBold.ttf"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(vn_font_file, "wb") as f:
                f.write(resp.content)
            print(f"[AssetManager] Downloaded Vietnamese font: {vn_font_file.name}")
            return vn_font_file
    except Exception as e:
        print(f"[AssetManager] BeVietnamPro download note: {e}")
        
    # Also check Montserrat
    mont_file = FONTS_DIR / "Montserrat-Black.ttf"
    if mont_file.exists():
        return mont_file
        
    return vn_font_file

def init_all_assets():
    ensure_directories()
    
    bg_file = BG_DIR / "paper_bg.png"
    if not bg_file.exists():
        create_default_background(bg_file)
        
    # Check category backgrounds
    from create_category_backgrounds import generate_all_backgrounds
    if not (BG_DIR / "bg_tech.png").exists() or not (BG_DIR / "bg_food.png").exists():
        generate_all_backgrounds()
        
    # Check category mascots
    from create_category_mascots import generate_all_category_mascots
    MASCOTS_DIR = ASSETS_DIR / "mascots"
    if not (MASCOTS_DIR / "food" / "pointing.png").exists() or not (MASCOTS_DIR / "tech" / "pointing.png").exists():
        generate_all_category_mascots()
        
    poses = ["pointing", "thinking", "chill", "cta"]
    for pose in poses:
        pfile = MASCOT_DIR / f"{pose}.png"
        if not pfile.exists():
            draw_cute_mascot(pose, pfile)
            
    pop_wav = SFX_DIR / "pop.wav"
    pop_mp3 = SFX_DIR / "pop.mp3"
    if not pop_wav.exists() and not pop_mp3.exists():
        generate_sfx_pop(pop_wav)
        
    whoosh_wav = SFX_DIR / "whoosh.wav"
    whoosh_mp3 = SFX_DIR / "whoosh.mp3"
    if not whoosh_wav.exists() and not whoosh_mp3.exists():
        generate_sfx_whoosh(whoosh_wav)
        
    # Check BGM
    bgm_file = BGM_DIR / "bgm_chill.wav"
    if not bgm_file.exists():
        generate_lofi_bgm(bgm_file, duration=60.0)

    download_vietnamese_font()
    print("[AssetManager] All assets and category backgrounds verified and ready!")

if __name__ == "__main__":
    init_all_assets()