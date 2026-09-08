import os
import math
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    from moviepy import (
        VideoClip,
        AudioFileClip,
        CompositeAudioClip,
        concatenate_audioclips
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        from moviepy.editor import (
            VideoClip,
            AudioFileClip,
            CompositeAudioClip,
            concatenate_audioclips
        )
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
BG_DIR = ASSETS_DIR / "backgrounds"
MASCOT_DIR = ASSETS_DIR / "mascot"
SFX_DIR = ASSETS_DIR / "sfx"
BGM_DIR = ASSETS_DIR / "bgm"
FONTS_DIR = ASSETS_DIR / "fonts"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

WIDTH = 1080
HEIGHT = 1920
FPS = 25

def set_clip_start(clip, t: float):
    return clip.with_start(t) if hasattr(clip, 'with_start') else clip.set_start(t)

def set_clip_duration(clip, d: float):
    return clip.with_duration(d) if hasattr(clip, 'with_duration') else clip.set_duration(d)

def set_clip_volume(clip, factor: float):
    if hasattr(clip, 'with_volume_scaled'):
        return clip.with_volume_scaled(factor)
    elif hasattr(clip, 'volumex'):
        return clip.volumex(factor)
    return clip

def subclip_audio(clip, start: float, end: float):
    if hasattr(clip, 'subclipped'):
        return clip.subclipped(start, end)
    elif hasattr(clip, 'subclip'):
        return clip.subclip(start, end)
    return clip

def set_video_audio(video_clip, audio_clip):
    return video_clip.with_audio(audio_clip) if hasattr(video_clip, 'with_audio') else video_clip.set_audio(audio_clip)

def get_best_font(size: int) -> ImageFont.FreeTypeFont:
    """Load BeVietnamPro-ExtraBold or Montserrat-Black for perfect Vietnamese support."""
    font_paths = [
        FONTS_DIR / "BeVietnamPro-ExtraBold.ttf",
        FONTS_DIR / "Montserrat-Black.ttf",
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "segoeuib.ttf",
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "arialbd.ttf",
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "calibrib.ttf",
    ]
    for fp in font_paths:
        if fp.exists():
            try:
                return ImageFont.truetype(str(fp), size)
            except Exception:
                continue
    return ImageFont.load_default()

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> List[str]:
    """Wrap text with proper word boundary support."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_w = bbox[2] - bbox[0]
        if line_w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(" ".join(current_line))
        
    return lines if lines else [text]

CATEGORY_BG_MAP = {
    "🧪 Lầm Tưởng Đời Sống & Sự Thật Khoa Học": "bg_ai.png",
    "🥑 Tranh Luận Dinh Dưỡng & Ăn Uống Lành Mạnh": "bg_food.png",
    "🍜 Ẩm thực & Món ăn Đặc sản": "bg_food.png",
    "🏢 Tranh Cãi Công Sở & Tư Duy Đi Làm": "bg_finance.png",
    "💳 Thói Quen Tiêu Dùng & Quản Lý Tiền Bạc": "bg_finance.png",
    "💰 Quyết Định Tài Chính & Đầu Tư Lớn": "bg_finance.png",
    "🎭 Tâm Lý Học Hành Vi & Bẫy Cảm Xúc": "bg_finance.png",
    "📱 Công nghệ & Thiết bị Điện tử": "bg_tech.png",
    "🤖 Phần Mềm, Ứng Dụng & Công Cụ AI": "bg_ai.png",
    "💻 Tương Lai Việc Làm: AI vs Kỹ Năng Con Người": "bg_ai.png",
    "🚗 Xe cộ & Phương tiện Di chuyển": "bg_vehicles.png",
    "🎮 Game & Thiết Bị Giải Trí": "bg_gaming.png",
    "👨‍👩‍👧 Tranh Luận Nuôi Dạy Con & Gia Đình": "bg_pets.png",
    "🐾 Thú Cưng: Nuôi Dạy & So Sánh Giống Loài": "bg_pets.png",
    "🐕 Giải Mã Hành Vi Thú Cưng & Bí Ẩn Động Vật": "bg_pets.png",
    "🌍 Nghịch Lý Địa Lý & Văn Hóa Thế Giới": "bg_vehicles.png",
    "📜 Bí Ẩn Lịch Sử & Lầm Tưởng Cổ Nhân": "bg_finance.png"
}

CATEGORY_MASCOT_MAP = {
    "🧪 Lầm Tưởng Đời Sống & Sự Thật Khoa Học": "ai",
    "🥑 Tranh Luận Dinh Dưỡng & Ăn Uống Lành Mạnh": "food",
    "🍜 Ẩm thực & Món ăn Đặc sản": "food",
    "🏢 Tranh Cãi Công Sở & Tư Duy Đi Làm": "finance",
    "💳 Thói Quen Tiêu Dùng & Quản Lý Tiền Bạc": "finance",
    "💰 Quyết Định Tài Chính & Đầu Tư Lớn": "finance",
    "🎭 Tâm Lý Học Hành Vi & Bẫy Cảm Xúc": "finance",
    "📱 Công nghệ & Thiết bị Điện tử": "tech",
    "🤖 Phần Mềm, Ứng Dụng & Công Cụ AI": "ai",
    "💻 Tương Lai Việc Làm: AI vs Kỹ Năng Con Người": "ai",
    "🚗 Xe cộ & Phương tiện Di chuyển": "vehicles",
    "🎮 Game & Thiết Bị Giải Trí": "gaming",
    "👨‍👩‍👧 Tranh Luận Nuôi Dạy Con & Gia Đình": "pets",
    "🐾 Thú Cưng: Nuôi Dạy & So Sánh Giống Loài": "pets",
    "🐕 Giải Mã Hành Vi Thú Cưng & Bí Ẩn Động Vật": "pets",
    "🌍 Nghịch Lý Địa Lý & Văn Hóa Thế Giới": "vehicles",
    "📜 Bí Ẩn Lịch Sử & Lầm Tưởng Cổ Nhân": "finance"
}

class VideoComposer:
    def __init__(
        self,
        script_data: Dict[str, Any],
        item_a_img_path: str,
        item_b_img_path: str,
        segment_audios: List[Dict[str, Any]],
        output_video_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ):
        self.script_data = script_data
        self.item_a_img_path = item_a_img_path
        self.item_b_img_path = item_b_img_path
        self.segment_audios = segment_audios
        self.output_video_path = output_video_path
        self.progress_callback = progress_callback or (lambda p, m: None)
        
        self._load_resources()
        self._calculate_timeline()
        self._pre_render_segment_bases()

    def _load_resources(self):
        category = self.script_data.get("category", "")
        bg_filename = CATEGORY_BG_MAP.get(category, "bg_default.png")
        bg_path = BG_DIR / bg_filename
        if not bg_path.exists():
            bg_path = BG_DIR / "paper_bg.png"
            
        if bg_path.exists():
            self.bg_img = Image.open(bg_path).convert("RGBA").resize((WIDTH, HEIGHT))
        else:
            self.bg_img = Image.new("RGBA", (WIDTH, HEIGHT), (18, 21, 30, 255))
            
        card_size = (440, 440)
        if os.path.exists(self.item_a_img_path):
            self.img_a = Image.open(self.item_a_img_path).convert("RGBA").resize(card_size, Image.Resampling.LANCZOS)
        else:
            self.img_a = Image.new("RGBA", card_size, (30, 58, 138, 255))
            
        if os.path.exists(self.item_b_img_path):
            self.img_b = Image.open(self.item_b_img_path).convert("RGBA").resize(card_size, Image.Resampling.LANCZOS)
        else:
            self.img_b = Image.new("RGBA", card_size, (136, 19, 55, 255))
            
        mascot_key = CATEGORY_MASCOT_MAP.get(category, "default")
        mascot_cat_dir = ASSETS_DIR / "mascots" / mascot_key
        
        self.mascot_imgs = {}
        for pose in ["pointing", "thinking", "chill", "cta"]:
            p_path = mascot_cat_dir / f"{pose}.png"
            if not p_path.exists():
                p_path = MASCOT_DIR / f"{pose}.png" # legacy fallback
                
            if p_path.exists():
                self.mascot_imgs[pose] = Image.open(p_path).convert("RGBA").resize((580, 680), Image.Resampling.LANCZOS)
            else:
                self.mascot_imgs[pose] = Image.new("RGBA", (580, 680), (0, 0, 0, 0))

        # Typography with BeVietnamPro
        self.font_title = get_best_font(48)
        self.font_tag = get_best_font(28)
        self.font_subtitle = get_best_font(42)
        self.font_vs = get_best_font(44)

        # Pre-render high-impact VS badge for smooth dynamic pulsing
        vs_sz = 220
        vs_base = Image.new("RGBA", (vs_sz, vs_sz), (0, 0, 0, 0))
        vs_draw = ImageDraw.Draw(vs_base)
        vs_draw.ellipse([15, 15, 205, 205], fill=(245, 158, 11, 80), outline=(254, 240, 138, 180), width=4)
        vs_draw.ellipse([26, 26, 194, 194], fill=(220, 38, 38, 255), outline=(254, 240, 138, 255), width=5)
        vs_draw.text((110, 108), "VS", fill="#FEF08A", font=self.font_vs, anchor="mm", stroke_width=3, stroke_fill="#450A0A")
        self.vs_badge_img = vs_base

    def _calculate_timeline(self):
        self.timeline_segments = []
        current_time = 0.0
        
        segments = self.script_data.get("segments", [])
        for i, seg in enumerate(segments):
            audio_info = self.segment_audios[i] if i < len(self.segment_audios) else None
            duration = audio_info["duration"] if audio_info else 4.0
            
            self.timeline_segments.append({
                "index": i,
                "segment_id": seg.get("segment_id", i + 1),
                "pose": seg.get("pose", "pointing"),
                "voiceover_text": seg.get("voiceover_text", ""),
                "highlight_item": seg.get("highlight_item", "none"),
                "sfx": seg.get("sfx", "pop"),
                "start_time": current_time,
                "end_time": current_time + duration,
                "duration": duration,
                "words": audio_info.get("words", []) if audio_info else []
            })
            current_time += duration
            
        self.total_duration = max(1.0, current_time)

    def _pre_render_segment_bases(self):
        self.segment_base_frames = []
        
        for seg in self.timeline_segments:
            frame = self.bg_img.copy()
            draw = ImageDraw.Draw(frame)
            highlight = seg.get("highlight_item", "none")
            
            # 1. Header Banner
            badge_y = 65
            badge_text = "⚖️ ĐỐI ĐẦU TRỰC TIẾP ⚖️"
            draw.rounded_rectangle([WIDTH // 2 - 210, badge_y, WIDTH // 2 + 210, badge_y + 55], radius=16, fill="#1E293B", outline="#475569", width=2)
            draw.text((WIDTH // 2, badge_y + 27), badge_text, fill="#F59E0B", font=self.font_tag, anchor="mm")
            
            title_text = self.script_data.get("title", "SO SÁNH ĐỐI ĐẦU").upper()
            lines = wrap_text(title_text, self.font_title, WIDTH - 140, draw)
            title_y = 155
            for line in lines[:2]:
                # Draw thick stroke for high contrast
                draw.text(
                    (WIDTH // 2, title_y),
                    line,
                    fill="#FFFFFF",
                    font=self.font_title,
                    anchor="mm",
                    stroke_width=4,
                    stroke_fill="#000000"
                )
                title_y += 65
                
            # 2. Product Name Tags (Cards & VS badge are rendered dynamically with motion in render_frame)
            card_y = 310
            card_a_x = 70
            card_b_x = 570
            
            name_a = self.script_data.get("item_a", {}).get("name", "Bên A")
            name_b = self.script_data.get("item_b", {}).get("name", "Bên B")
            
            tag_a_w = 400
            draw.rounded_rectangle([card_a_x + 20, card_y + 455, card_a_x + tag_a_w + 20, card_y + 510], radius=14, fill="#0F172A", outline="#38BDF8", width=3)
            draw.text((card_a_x + 220, card_y + 482), name_a[:18], fill="#38BDF8", font=self.font_tag, anchor="mm")
            
            tag_b_w = 400
            draw.rounded_rectangle([card_b_x + 20, card_y + 455, card_b_x + tag_b_w + 20, card_y + 510], radius=14, fill="#0F172A", outline="#FB7185", width=3)
            draw.text((card_b_x + 220, card_y + 482), name_b[:18], fill="#FB7185", font=self.font_tag, anchor="mm")

            # 3. Subtitles with Stroke and Background Box
            sub_y_center = 965
            voice_text = seg.get("voiceover_text", "")
            if voice_text:
                sub_lines = wrap_text(voice_text, self.font_subtitle, WIDTH - 160, draw)
                box_h = len(sub_lines) * 65 + 44
                box_top = sub_y_center - box_h // 2
                
                # Dark container with yellow accent border
                draw.rounded_rectangle(
                    [55, box_top, WIDTH - 55, box_top + box_h],
                    radius=22,
                    fill=(15, 23, 42, 235),
                    outline=(245, 158, 11, 220),
                    width=3
                )
                
                cur_line_y = box_top + 34
                for s_line in sub_lines:
                    draw.text(
                        (WIDTH // 2, cur_line_y),
                        s_line,
                        fill="#FEF08A",
                        font=self.font_subtitle,
                        anchor="mm",
                        stroke_width=4,
                        stroke_fill="#000000"
                    )
                    cur_line_y += 64

            self.segment_base_frames.append(frame)

    def render_frame(self, t: float) -> np.ndarray:
        seg_idx = 0
        active_seg = self.timeline_segments[0]
        for idx, seg in enumerate(self.timeline_segments):
            if seg["start_time"] <= t < seg["end_time"]:
                seg_idx = idx
                active_seg = seg
                break
        else:
            seg_idx = len(self.timeline_segments) - 1
            active_seg = self.timeline_segments[-1]
            
        frame = self.segment_base_frames[seg_idx].copy()
        
        # Segment local time & highlight
        seg_t = max(0.0, t - active_seg.get("start_time", 0.0))
        highlight = active_seg.get("highlight_item", "none")
        
        # 1. Dynamic Product Cards with Ken Burns breathing zoom
        card_y = 310
        card_a_x = 70
        card_b_x = 570
        card_cx_a = card_a_x + 220
        card_cx_b = card_b_x + 220
        card_cy = card_y + 220
        
        # Scale breathing oscillation for highlighted item
        scale_a = (1.05 + 0.025 * math.sin(seg_t * 3.5)) if highlight in ["A", "both"] else 1.0
        scale_b = (1.05 + 0.025 * math.sin(seg_t * 3.5)) if highlight in ["B", "both"] else 1.0
        
        # Draw Card A
        if scale_a != 1.0:
            sa = int(440 * scale_a)
            img_a_draw = self.img_a.resize((sa, sa), Image.Resampling.BILINEAR)
            pos_a = (card_cx_a - sa // 2, card_cy - sa // 2)
            frame.paste(img_a_draw, pos_a, img_a_draw)
        else:
            frame.paste(self.img_a, (card_a_x, card_y), self.img_a)
            
        # Draw Card B
        if scale_b != 1.0:
            sb = int(440 * scale_b)
            img_b_draw = self.img_b.resize((sb, sb), Image.Resampling.BILINEAR)
            pos_b = (card_cx_b - sb // 2, card_cy - sb // 2)
            frame.paste(img_b_draw, pos_b, img_b_draw)
        else:
            frame.paste(self.img_b, (card_b_x, card_y), self.img_b)
            
        # 2. Dynamic Pulsing Central VS Badge
        vs_pulse = 1.0 + 0.07 * math.sin(t * 4.5)
        vs_sz = int(140 * vs_pulse)
        vs_draw = self.vs_badge_img.resize((vs_sz, vs_sz), Image.Resampling.BILINEAR)
        frame.paste(vs_draw, (WIDTH // 2 - vs_sz // 2, card_cy - vs_sz // 2), vs_draw)
        
        # 3. Mascot pop-in & idle float
        pose = active_seg.get("pose", "pointing")
        mascot_img = self.mascot_imgs.get(pose, self.mascot_imgs.get("pointing"))
        
        pop_scale = min(1.0, 0.75 + 1.25 * seg_t) if seg_t < 0.2 else 1.0
        idle_offset_y = int(6 * math.sin(t * 4.0))
        
        mw, mh = 580, 680
        if pop_scale < 1.0:
            cur_w = int(mw * pop_scale)
            cur_h = int(mh * pop_scale)
            mascot_to_paste = mascot_img.resize((cur_w, cur_h), Image.Resampling.BILINEAR)
            pos_x = (WIDTH - cur_w) // 2
            pos_y = 1170 + (mh - cur_h) + idle_offset_y
        else:
            mascot_to_paste = mascot_img
            pos_x = (WIDTH - mw) // 2
            pos_y = 1170 + idle_offset_y
            
        frame.paste(mascot_to_paste, (pos_x, pos_y), mascot_to_paste)

        # 4. Modern Bottom Progress bar
        draw = ImageDraw.Draw(frame)
        progress = min(1.0, max(0.0, t / self.total_duration))
        prog_w = int(WIDTH * progress)
        draw.rectangle([0, HEIGHT - 12, WIDTH, HEIGHT], fill="#1E293B")
        draw.rectangle([0, HEIGHT - 12, prog_w, HEIGHT], fill="#F59E0B")
        
        return np.array(frame.convert("RGB"))

    def build_audio_track(self) -> CompositeAudioClip:
        audio_clips = []
        
        # 1. Background Music (BGM) - soft Lo-Fi ambient music at 9% volume
        bgm_candidates = list(BGM_DIR.glob("*.wav")) + list(BGM_DIR.glob("*.mp3"))
        if not bgm_candidates:
            try:
                from asset_manager import generate_lofi_bgm
                auto_bgm = generate_lofi_bgm()
                if auto_bgm and os.path.exists(auto_bgm):
                    bgm_candidates = [Path(auto_bgm)]
            except Exception as e:
                print(f"[VideoComposer] Warning: Could not auto-generate BGM: {e}")

        if bgm_candidates:
            try:
                bgm_path = bgm_candidates[0]
                bgm_raw = AudioFileClip(str(bgm_path))
                if bgm_raw.duration < self.total_duration:
                    repeats = math.ceil(self.total_duration / max(0.1, bgm_raw.duration))
                    bgm_looped = concatenate_audioclips([bgm_raw] * repeats)
                else:
                    bgm_looped = bgm_raw
                    
                bgm_sub = subclip_audio(bgm_looped, 0, self.total_duration)
                bgm_sub = set_clip_volume(bgm_sub, 0.09)
                bgm_sub = set_clip_start(bgm_sub, 0.0)
                audio_clips.append(bgm_sub)
                print(f"[VideoComposer] Mixed BGM from {bgm_path.name} at 9% volume.")
            except Exception as e:
                print(f"[VideoComposer] Warning: Failed to mix BGM: {e}")

        # 2. Voiceover & SFX clips
        for seg in self.timeline_segments:
            start_t = seg["start_time"]
            
            matching_audio = next((a for a in self.segment_audios if a["segment_id"] == seg["segment_id"]), None)
            if matching_audio and os.path.exists(matching_audio["audio_path"]):
                try:
                    vo_clip = AudioFileClip(matching_audio["audio_path"])
                    vo_clip = set_clip_start(vo_clip, start_t)
                    audio_clips.append(vo_clip)
                except Exception as e:
                    print(f"[VideoComposer] Error loading VO audio: {e}")
                    
            sfx_type = seg.get("sfx", "pop")
            sfx_files = [
                SFX_DIR / f"{sfx_type}.wav",
                SFX_DIR / f"{sfx_type}.mp3"
            ]
            for sf in sfx_files:
                if sf.exists():
                    try:
                        s_clip = AudioFileClip(str(sf))
                        s_clip = set_clip_start(s_clip, start_t)
                        s_clip = set_clip_volume(s_clip, 0.4)
                        audio_clips.append(s_clip)
                        break
                    except Exception:
                        pass
                        
        if audio_clips:
            composite = CompositeAudioClip(audio_clips)
            return set_clip_duration(composite, self.total_duration)
        else:
            from moviepy import AudioClip
            return AudioClip(lambda t: 0, duration=self.total_duration)

    def render(self) -> str:
        self.progress_callback(0.05, "Đang chuẩn bị các layer hình ảnh...")
        video = VideoClip(self.render_frame, duration=self.total_duration)
        
        self.progress_callback(0.15, "Đang hòa trộn âm thanh và hiệu ứng SFX...")
        audio = self.build_audio_track()
        video = set_video_audio(video, audio)
        
        self.progress_callback(0.25, "Đang mã hóa và xuất video 1080x1920 25FPS...")
        
        video.write_videofile(
            self.output_video_path,
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )
        
        video.close()
        self.progress_callback(1.0, "Xuất video thành công!")
        print(f"[VideoComposer] Video rendered successfully: {self.output_video_path}")
        return self.output_video_path

def build_comparison_video(
    script_data: Dict[str, Any],
    item_a_img: str,
    item_b_img: str,
    segment_audios: List[Dict[str, Any]],
    output_path: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> str:
    composer = VideoComposer(
        script_data=script_data,
        item_a_img_path=item_a_img,
        item_b_img_path=item_b_img,
        segment_audios=segment_audios,
        output_video_path=output_path,
        progress_callback=progress_callback
    )
    return composer.render()