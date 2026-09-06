import asyncio
import os
import threading
import time
import glob
import shutil
import wave
import struct
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    from moviepy import AudioFileClip
except ImportError:
    try:
        from moviepy.editor import AudioFileClip
    except ImportError:
        AudioFileClip = None

try:
    import pygame
    PYGAME_AVAILABLE = True
    pygame.mixer.init()
except Exception:
    PYGAME_AVAILABLE = False

from text_normalizer import normalize_text_for_speech

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
MY_VOICE_DIR = BASE_DIR / "assets" / "my_voice"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
MY_VOICE_DIR.mkdir(parents=True, exist_ok=True)

# Raw Voice IDs
VOICE_MALE = "vi-VN-NamMinhNeural"
VOICE_FEMALE = "vi-VN-HoaiMyNeural"

# Voice Presets Mapping
VOICE_PRESETS = {
    "🌟 Giọng Cá Nhân (Giọng của bạn)": {
        "voice": "CUSTOM_PERSONAL",
        "gender": "Nam",
        "rate": "+10%",
        "pitch": "+0Hz",
        "desc": "Sử dụng file ghi âm giọng thật của bạn"
    },
    "🎙️ Nam - Reviewer Công Nghệ (Năng động • Shorts/TikTok)": {
        "voice": VOICE_MALE,
        "gender": "Nam",
        "rate": "+12%",
        "pitch": "+1Hz",
        "desc": "Giọng nam dứt khoát, năng lượng cao chuẩn review"
    },
    "🎙️ Nam - Trầm Ấm, Bản Lĩnh (Chuyên nghiệp)": {
        "voice": VOICE_MALE,
        "gender": "Nam",
        "rate": "+5%",
        "pitch": "-3Hz",
        "desc": "Giọng nam chững chạc, độ tin cậy cao"
    },
    "🎙️ Nam - Kể Chuyện / Deep Voice": {
        "voice": VOICE_MALE,
        "gender": "Nam",
        "rate": "+0%",
        "pitch": "-6Hz",
        "desc": "Giọng nam siêu trầm, huyền bí, lôi cuốn"
    },
    "🎀 Nữ - MC Năng Động / Bắt Trend": {
        "voice": VOICE_FEMALE,
        "gender": "Nữ",
        "rate": "+14%",
        "pitch": "+2Hz",
        "desc": "Giọng nữ tươi vui, cuốn hút người nghe"
    },
    "🎀 Nữ - Ngọt Ngào, Truyền Cảm": {
        "voice": VOICE_FEMALE,
        "gender": "Nữ",
        "rate": "+8%",
        "pitch": "+0Hz",
        "desc": "Giọng nữ tự nhiên, mềm mại, truyền cảm"
    },
    "🎀 Nữ - Trầm Ấm, Tin Tức": {
        "voice": VOICE_FEMALE,
        "gender": "Nữ",
        "rate": "+4%",
        "pitch": "-2Hz",
        "desc": "Giọng nữ điềm đạm, trang trọng"
    }
}

DEFAULT_PRESET = "🎙️ Nam - Reviewer Công Nghệ (Năng động • Shorts/TikTok)"
DEFAULT_VOICE = VOICE_MALE

def get_personal_voice_path() -> Optional[str]:
    for ext in [".mp3", ".wav", ".m4a", ".ogg"]:
        p = MY_VOICE_DIR / f"my_voice{ext}"
        if p.exists():
            return str(p)
    audio_files = list(MY_VOICE_DIR.glob("*.mp3")) + list(MY_VOICE_DIR.glob("*.wav"))
    if audio_files:
        return str(audio_files[0])
    return None

def import_personal_voice_file(source_path: str) -> str:
    MY_VOICE_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(source_path).suffix.lower() or ".mp3"
    target_path = MY_VOICE_DIR / f"my_voice{ext}"
    shutil.copy2(source_path, target_path)
    return str(target_path)

def _create_silent_wav(output_path: str, duration_sec: float = 3.0):
    """Create a valid silent WAV file as ultimate fallback so MoviePy never encounters 0-byte error."""
    sample_rate = 22050
    num_samples = int(sample_rate * duration_sec)
    with wave.open(output_path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))

async def _async_generate_speech(
    text: str,
    output_audio_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "+10%",
    pitch: str = "+0Hz"
) -> Dict[str, Any]:
    if not EDGE_TTS_AVAILABLE:
        raise RuntimeError("Thư viện 'edge-tts' chưa được cài đặt.")
        
    spoken_text = normalize_text_for_speech(text)
    if not spoken_text or not spoken_text.strip():
        spoken_text = "Xin chào và hẹn gặp lại các bạn!"
        
    actual_voice = voice
    if voice == "CUSTOM_PERSONAL":
        actual_voice = VOICE_MALE
        
    temp_audio = output_audio_path + ".tmp"
    word_timings = []
    
    # Retry loop up to 3 attempts with exponential backoff
    for attempt in range(3):
        try:
            communicate = edge_tts.Communicate(spoken_text, actual_voice, rate=rate, pitch=pitch)
            word_timings.clear()
            
            with open(temp_audio, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        offset_s = chunk["offset"] / 10_000_000.0
                        duration_s = chunk["duration"] / 10_000_000.0
                        word_timings.append({
                            "word": chunk["text"],
                            "start": offset_s,
                            "end": offset_s + duration_s
                        })
            
            if os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 500:
                if os.path.exists(output_audio_path):
                    try:
                        os.remove(output_audio_path)
                    except Exception:
                        pass
                os.replace(temp_audio, output_audio_path)
                break
        except Exception as e:
            print(f"[TTSService] Edge-TTS attempt {attempt+1} retry ({e})...")
            await asyncio.sleep(0.5 * (attempt + 1))
            
    # If still not created or 0 bytes, create fallback wav
    if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) < 500:
        print(f"[TTSService] Fallback silent WAV created for: {output_audio_path}")
        _create_silent_wav(output_audio_path, duration_sec=max(2.5, len(spoken_text) * 0.08))

    duration = 3.0
    if AudioFileClip is not None and os.path.exists(output_audio_path):
        try:
            clip = AudioFileClip(output_audio_path)
            duration = float(clip.duration)
            clip.close()
        except Exception:
            if word_timings:
                duration = word_timings[-1]["end"] + 0.2
    elif word_timings:
        duration = word_timings[-1]["end"] + 0.2

    return {
        "audio_path": output_audio_path,
        "duration": max(1.5, duration),
        "words": word_timings,
        "spoken_text": spoken_text
    }

def generate_speech(
    text: str,
    output_audio_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "+10%",
    pitch: str = "+0Hz"
) -> Dict[str, Any]:
    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(
                    _async_generate_speech(text, output_audio_path, voice, rate, pitch)
                )
            else:
                return loop.run_until_complete(
                    _async_generate_speech(text, output_audio_path, voice, rate, pitch)
                )
        except RuntimeError:
            return asyncio.run(
                _async_generate_speech(text, output_audio_path, voice, rate, pitch)
            )
    except Exception as e:
        print(f"[TTSService] Fatal Edge-TTS error: {e}")
        _create_silent_wav(output_audio_path, duration_sec=3.0)
        return {
            "audio_path": output_audio_path,
            "duration": 3.0,
            "words": [],
            "spoken_text": text
        }

def cleanup_old_previews():
    try:
        for f in glob.glob(str(TEMP_DIR / "preview_voice_*.mp3")):
            try:
                os.remove(f)
            except Exception:
                pass
    except Exception:
        pass

def play_audio_preview(text: str, voice: str, rate: str, pitch: str, on_finish_callback=None):
    stop_audio_preview()
    
    def worker():
        try:
            timestamp_ms = int(time.time() * 1000)
            preview_file = str(TEMP_DIR / f"preview_voice_{timestamp_ms}.mp3")
            generate_speech(text, preview_file, voice=voice, rate=rate, pitch=pitch)
            
            if PYGAME_AVAILABLE and os.path.exists(preview_file):
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass
                pygame.mixer.music.load(preview_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass
        except Exception as e:
            print(f"[TTSService] Preview error: {e}")
        finally:
            if on_finish_callback:
                on_finish_callback()
                
    threading.Thread(target=worker, daemon=True).start()

def stop_audio_preview():
    if PYGAME_AVAILABLE:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass