import os
import sys
import re
import threading
import queue
import time
import json
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import customtkinter as ctk
from PIL import Image
from tkinter import messagebox, filedialog

import config_manager
import gemini_service
import tts_service
import image_service
import video_engine
import script_manager
import asset_manager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
MY_VOICE_DIR = ASSETS_DIR / "my_voice"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MY_VOICE_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_video_filename(title: str, output_dir: Path) -> Path:
    """Format video filename strictly based on comparison title (Option A: Full Vietnamese with spaces)."""
    clean = title.replace(":", " - ").replace("/", " - ").replace("\\", " - ")
    clean = re.sub(r'[\\/*?:"<>|]', '', clean).strip()
    clean = re.sub(r'\s+', ' ', clean)
    if not clean:
        clean = f"Video_So_Sanh_{int(time.time())}"
        
    base_path = output_dir / f"{clean}.mp4"
    if not base_path.exists():
        return base_path
        
    idx = 1
    while True:
        cand = output_dir / f"{clean} ({idx}).mp4"
        if not cand.exists():
            return cand
        idx += 1

class AutoShortsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Auto Shorts SS V2 - AI Comparison Video Factory (0 VNĐ)")
        self.geometry("1100x740")
        self.minsize(1000, 700)
        
        icon_path = ASSETS_DIR / "icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass
                
        self.config = config_manager.load_config()
        self.log_queue = queue.Queue()
        self.is_processing = False
        self.cancel_requested = False
        self.last_rendered_video = None
        self.is_previewing_audio = False
        self.video_count_val = 1
        
        self._build_ui()
        self._check_assets_async()
        self._update_stats_ui()
        self.after(100, self._process_log_queue)

    def _check_assets_async(self):
        def worker():
            asset_manager.init_all_assets()
            self.log_queue.put(("[Hệ thống] Đã sẵn sàng tài nguyên: Font BeVietnamPro, 8 Mascot, 8 Nền đồ họa.", "info"))
        threading.Thread(target=worker, daemon=True).start()

    def _update_stats_ui(self):
        used_cnt = script_manager.get_used_count()
        if hasattr(self, "lbl_stats"):
            self.lbl_stats.configure(
                text=f"🗄️ Đã sản xuất: {used_cnt} video thành phẩm (Chống trùng lặp 100%)",
                text_color="#10B981" if used_cnt > 0 else "#94A3B8"
            )

    def _build_ui(self):
        # ---------------- HEADER ----------------
        self.header_frame = ctk.CTkFrame(self, height=65, corner_radius=0, fg_color="#0F172A")
        self.header_frame.pack(fill="x", side="top")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🎬 AUTO SHORTS SS (V2)",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#38BDF8"
        )
        self.title_label.pack(side="left", padx=20, pady=12)
        
        self.badge_label = ctk.CTkLabel(
            self.header_frame,
            text="KÊNH PHỤ (V2) • 9:16 SO SÁNH (35s - 55s)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1E293B",
            text_color="#10B981",
            corner_radius=8,
            padx=10,
            pady=4
        )
        self.badge_label.pack(side="left", padx=5)

        # Header Right Controls
        btn_api_settings = ctk.CTkButton(
            self.header_frame,
            text="⚙️ Cài Đặt API Key",
            width=130,
            fg_color="#334155",
            hover_color="#475569",
            command=self._open_api_settings_modal
        )
        btn_api_settings.pack(side="right", padx=(6, 15), pady=12)
        
        self.btn_open_out = ctk.CTkButton(
            self.header_frame,
            text="📁 Thư Mục Video",
            width=130,
            fg_color="#1E293B",
            hover_color="#334155",
            command=self._open_output_folder
        )
        self.btn_open_out.pack(side="right", padx=6, pady=12)

        # ---------------- MAIN CONTENT ----------------
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)

        self.left_panel = ctk.CTkFrame(self.main_container, width=470, corner_radius=12, fg_color="#1E293B")
        self.left_panel.pack(side="left", fill="both", padx=(0, 10))
        self.left_panel.pack_propagate(False)

        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=12, fg_color="#1E293B")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        # ---------------- 1. TOPIC CATEGORY CARD ----------------
        topic_box = ctk.CTkFrame(self.left_panel, fg_color="#0F172A", corner_radius=10, border_width=1, border_color="#334155")
        topic_box.pack(fill="x", padx=14, pady=(12, 8))

        lbl_topic = ctk.CTkLabel(
            topic_box,
            text="1. Chọn Thể Loại / Chủ Đề Video:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38BDF8"
        )
        lbl_topic.pack(anchor="w", padx=14, pady=(10, 2))

        self.category_names = list(gemini_service.TOPIC_CATEGORIES.keys())
        self.combo_category = ctk.CTkComboBox(
            topic_box,
            values=self.category_names,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.combo_category.pack(fill="x", padx=14, pady=(0, 10))
        self.combo_category.set(self.category_names[0])

        # ---------------- 2. VOICE & AUDIO CARD ----------------
        voice_box = ctk.CTkFrame(self.left_panel, fg_color="#0F172A", corner_radius=10, border_width=1, border_color="#334155")
        voice_box.pack(fill="x", padx=14, pady=(0, 8))

        lbl_voice = ctk.CTkLabel(
            voice_box,
            text="2. Giọng Đọc AI & Tốc Độ:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38BDF8"
        )
        lbl_voice.pack(anchor="w", padx=14, pady=(10, 2))

        self.voice_presets = list(tts_service.VOICE_PRESETS.keys())
        self.combo_voice = ctk.CTkComboBox(
            voice_box,
            values=self.voice_presets,
            height=34,
            font=ctk.CTkFont(size=12)
        )
        self.combo_voice.pack(fill="x", padx=14, pady=(0, 6))
        self.combo_voice.set(self.config.get("selected_preset", tts_service.DEFAULT_PRESET))

        voice_btn_row = ctk.CTkFrame(voice_box, fg_color="transparent")
        voice_btn_row.pack(fill="x", padx=14, pady=(0, 10))

        self.btn_preview_voice = ctk.CTkButton(
            voice_btn_row,
            text="🔊 Nghe Thử Giọng",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self._preview_voice_sample
        )
        self.btn_preview_voice.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_my_voice = ctk.CTkButton(
            voice_btn_row,
            text="🎙️ Tải Giọng Cá Nhân",
            font=ctk.CTkFont(size=11),
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self._upload_personal_voice
        )
        self.btn_my_voice.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # ---------------- 3. PRODUCTION & BATCH CARD ----------------
        action_card = ctk.CTkFrame(self.left_panel, fg_color="#0F172A", corner_radius=10, border_width=1, border_color="#334155")
        action_card.pack(fill="x", padx=14, pady=(0, 10))

        lbl_act_title = ctk.CTkLabel(
            action_card,
            text="3. Sản Xuất Video Tự Động:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38BDF8"
        )
        lbl_act_title.pack(anchor="w", padx=14, pady=(10, 4))

        # Video Quantity Stepper
        count_row = ctk.CTkFrame(action_card, fg_color="transparent")
        count_row.pack(fill="x", padx=14, pady=(0, 8))

        lbl_cnt_title = ctk.CTkLabel(
            count_row,
            text="Số lượng video tạo 1 lúc:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_cnt_title.pack(side="left", padx=(0, 8))

        btn_dec = ctk.CTkButton(
            count_row,
            text="➖",
            width=32,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=self._decrease_video_count
        )
        btn_dec.pack(side="left", padx=(0, 4))

        self.entry_count = ctk.CTkEntry(
            count_row,
            width=50,
            height=30,
            font=ctk.CTkFont(size=13, weight="bold"),
            justify="center"
        )
        self.entry_count.pack(side="left", padx=(0, 4))
        self.entry_count.insert(0, "1")
        self.entry_count.bind("<KeyRelease>", self._on_count_entry_change)

        btn_inc = ctk.CTkButton(
            count_row,
            text="➕",
            width=32,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=self._increase_video_count
        )
        btn_inc.pack(side="left", padx=(0, 8))

        # Quick preset buttons
        for val in [1, 3, 5, 10]:
            btn_quick = ctk.CTkButton(
                count_row,
                text=str(val),
                width=28,
                height=26,
                font=ctk.CTkFont(size=11),
                fg_color="#1E293B",
                hover_color="#334155",
                command=lambda v=val: self._set_video_count(v)
            )
            btn_quick.pack(side="left", padx=2)

        # Big Action Button
        self.btn_generate = ctk.CTkButton(
            action_card,
            text="🚀 BẮT ĐẦU SẢN XUẤT 1 VIDEO (35s - 55s)",
            height=46,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            command=self._start_generation
        )
        self.btn_generate.pack(fill="x", padx=14, pady=(4, 6))

        self.prog_bar = ctk.CTkProgressBar(action_card, height=10)
        self.prog_bar.pack(fill="x", padx=14, pady=(2, 6))
        self.prog_bar.set(0)

        self.lbl_status = ctk.CTkLabel(
            action_card,
            text="Sẵn sàng sản xuất video...",
            font=ctk.CTkFont(size=12),
            text_color="#38BDF8"
        )
        self.lbl_status.pack(anchor="w", padx=16, pady=(0, 6))

        btn_row = ctk.CTkFrame(action_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 8))

        self.btn_play = ctk.CTkButton(
            btn_row,
            text="▶️ Xem Video Vừa Tạo",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            fg_color="#6366F1",
            hover_color="#4F46E5",
            state="disabled",
            command=self._play_last_video
        )
        self.btn_play.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_cancel = ctk.CTkButton(
            btn_row,
            text="⏹️ Dừng",
            font=ctk.CTkFont(size=12),
            height=34,
            width=65,
            fg_color="#EF4444",
            hover_color="#DC2626",
            state="disabled",
            command=self._cancel_generation
        )
        self.btn_cancel.pack(side="right")

        self.lbl_stats = ctk.CTkLabel(
            action_card,
            text="🗄️ Đang tải lịch sử...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#10B981"
        )
        self.lbl_stats.pack(anchor="w", padx=16, pady=(0, 8))

    def _build_right_panel(self):
        lbl_preview = ctk.CTkLabel(
            self.right_panel,
            text="Hình Ảnh Sản Phẩm (Tự động tải & Crop 1:1):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_preview.pack(anchor="w", padx=16, pady=(12, 4))

        self.img_frame = ctk.CTkFrame(self.right_panel, fg_color="#0F172A", height=125, corner_radius=8)
        self.img_frame.pack(fill="x", padx=16, pady=(0, 10))
        self.img_frame.pack_propagate(False)

        box_a = ctk.CTkFrame(self.img_frame, fg_color="transparent")
        box_a.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        self.lbl_name_a = ctk.CTkLabel(box_a, text="Sản phẩm A", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38BDF8")
        self.lbl_name_a.pack()
        self.lbl_img_a = ctk.CTkLabel(box_a, text="[Chưa có ảnh]", width=90, height=80, fg_color="#1E293B", corner_radius=6)
        self.lbl_img_a.pack(pady=2)

        lbl_vs = ctk.CTkLabel(self.img_frame, text="VS", font=ctk.CTkFont(size=16, weight="bold"), text_color="#EF4444")
        lbl_vs.pack(side="left", padx=5)

        box_b = ctk.CTkFrame(self.img_frame, fg_color="transparent")
        box_b.pack(side="right", fill="both", expand=True, padx=8, pady=8)
        self.lbl_name_b = ctk.CTkLabel(box_b, text="Sản phẩm B", font=ctk.CTkFont(size=11, weight="bold"), text_color="#F43F5E")
        self.lbl_name_b.pack()
        self.lbl_img_b = ctk.CTkLabel(box_b, text="[Chưa có ảnh]", width=90, height=80, fg_color="#1E293B", corner_radius=6)
        self.lbl_img_b.pack(pady=2)

        lbl_log = ctk.CTkLabel(
            self.right_panel,
            text="Nhật Ký Sản Xuất Thời Gian Thực:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_log.pack(anchor="w", padx=16, pady=(0, 4))

        self.txt_logs = ctk.CTkTextbox(
            self.right_panel,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#0F172A",
            text_color="#E2E8F0",
            corner_radius=8
        )
        self.txt_logs.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    # Stepper Control
    def _set_video_count(self, count: int):
        val = max(1, min(count, 50))
        self.video_count_val = val
        self.entry_count.delete(0, "end")
        self.entry_count.insert(0, str(val))
        self._update_generate_btn_text()

    def _increase_video_count(self):
        self._set_video_count(self._get_target_count() + 1)

    def _decrease_video_count(self):
        self._set_video_count(self._get_target_count() - 1)

    def _on_count_entry_change(self, event=None):
        raw = self.entry_count.get().strip()
        if raw.isdigit():
            self._set_video_count(int(raw))

    def _get_target_count(self) -> int:
        raw = self.entry_count.get().strip()
        if raw.isdigit() and int(raw) > 0:
            return min(int(raw), 50)
        return 1

    def _update_generate_btn_text(self):
        cnt = self._get_target_count()
        if cnt == 1:
            self.btn_generate.configure(text="🚀 BẮT ĐẦU SẢN XUẤT 1 VIDEO (35s - 55s)")
        else:
            self.btn_generate.configure(text=f"🚀 BẮT ĐẦU SẢN XUẤT BATCH {cnt} VIDEO")

    def _preview_voice_sample(self):
        if self.is_previewing_audio:
            tts_service.stop_audio_preview()
            self.is_previewing_audio = False
            self.btn_preview_voice.configure(text="🔊 Nghe Thử Giọng")
            return

        sample_text = "Chào mừng bạn đến với kênh so sánh thông minh! Hôm nay chúng ta sẽ cùng phân tích chi tiết."
        voice_id, rate, pitch = self._get_current_voice_config()
        
        self.is_previewing_audio = True
        self.btn_preview_voice.configure(text="⏹️ Dừng Nghe Thử")
        
        def on_done():
            self.is_previewing_audio = False
            self.btn_preview_voice.configure(text="🔊 Nghe Thử Giọng")
            
        tts_service.play_audio_preview(sample_text, voice_id, rate, pitch, on_finish_callback=on_done)

    def _upload_personal_voice(self):
        fpath = filedialog.askopenfilename(
            title="Chọn file ghi âm giọng nói của bạn",
            filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.ogg")]
        )
        if fpath:
            imported = tts_service.import_personal_voice_file(fpath)
            self.combo_voice.set("🌟 Giọng Cá Nhân (Giọng của bạn)")
            self._log(f"Đã nạp file giọng cá nhân thành công: {Path(imported).name}", "success")
            messagebox.showinfo("Thành công", "Đã tích hợp file giọng cá nhân thành công!")

    def _open_output_folder(self):
        category = self.combo_category.get()
        clean_cat = category.replace(":", " - ").replace("/", " - ").replace("\\", " - ")
        clean_cat = re.sub(r'[\\/*?:"<>|]', '', clean_cat).strip()
        cat_dir = OUTPUT_DIR / clean_cat
        target_dir = cat_dir if cat_dir.exists() else OUTPUT_DIR
        try:
            os.startfile(str(target_dir))
        except Exception:
            webbrowser.open(str(target_dir))

    def _play_last_video(self):
        if self.last_rendered_video and os.path.exists(self.last_rendered_video):
            try:
                os.startfile(self.last_rendered_video)
            except Exception as e:
                self._log(f"Không thể mở file video: {e}", "error")

    def _open_api_settings_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("⚙️ Cài Đặt Gemini API Key")
        modal.geometry("480x280")
        modal.resizable(False, False)
        modal.grab_set()

        lbl = ctk.CTkLabel(
            modal,
            text="1. Khóa API Gemini (Kịch bản AI):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38BDF8"
        )
        lbl.pack(padx=20, pady=(15, 6))

        entry_k = ctk.CTkEntry(modal, placeholder_text="Dán Gemini API Key vào đây...", height=34, font=ctk.CTkFont(size=12))
        entry_k.pack(fill="x", padx=30, pady=(0, 10))
        entry_k.insert(0, self.config.get("gemini_api_key", ""))

        lbl_buf = ctk.CTkLabel(
            modal,
            text="2. Buffer Personal Access Token (Đăng TikTok tự động):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38BDF8"
        )
        lbl_buf.pack(padx=20, pady=(6, 6))

        entry_buf = ctk.CTkEntry(modal, placeholder_text="Dán Buffer Access Token...", height=34, font=ctk.CTkFont(size=12))
        entry_buf.pack(fill="x", padx=30, pady=(0, 10))
        entry_buf.insert(0, self.config.get("buffer_access_token", ""))

        var_tiktok = ctk.BooleanVar(value=self.config.get("auto_post_buffer_tiktok", True))
        chk_tiktok = ctk.CTkCheckBox(modal, text="Bật tự động đăng lên TikTok (Buffer) sau khi render", variable=var_tiktok, font=ctk.CTkFont(size=12))
        chk_tiktok.pack(padx=30, pady=(0, 12), anchor="w")

        lbl_st = ctk.CTkLabel(modal, text="", font=ctk.CTkFont(size=11))
        lbl_st.pack(padx=30, pady=(0, 8))

        def save_k():
            k = entry_k.get().strip()
            b = entry_buf.get().strip()
            self.config["gemini_api_key"] = k
            self.config["buffer_access_token"] = b
            self.config["auto_post_buffer_tiktok"] = var_tiktok.get()
            config_manager.set_config_value("gemini_api_key", k)
            config_manager.set_config_value("buffer_access_token", b)
            config_manager.set_config_value("auto_post_buffer_tiktok", var_tiktok.get())
            lbl_st.configure(text="✅ Đã lưu cấu hình thành công!", text_color="#10B981")
            self.after(800, modal.destroy)

        btn_save = ctk.CTkButton(modal, text="💾 Lưu Cấu Hình", font=ctk.CTkFont(size=12, weight="bold"), height=34, fg_color="#10B981", hover_color="#059669", command=save_k)
        btn_save.pack(fill="x", padx=30, pady=(0, 15))

    def _get_current_voice_config(self):
        saved_preset = self.combo_voice.get()
        self.config["selected_preset"] = saved_preset
        config_manager.set_config_value("selected_preset", saved_preset)
        
        if saved_preset == "🌟 Giọng Cá Nhân (Giọng của bạn)":
            return "CUSTOM_PERSONAL", "+0%", "+0Hz"
            
        preset = tts_service.VOICE_PRESETS.get(saved_preset, {})
        gender = preset.get("gender", "Nam")
        voice = tts_service.VOICE_FEMALE if gender == "Nữ" else tts_service.VOICE_MALE
        rate = preset.get("rate", "+12%")
        pitch = preset.get("pitch", "+1Hz")
        return voice, rate, pitch

    def _log(self, message: str, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put((f"[{timestamp}] {message}", level))

    def _process_log_queue(self):
        while not self.log_queue.empty():
            msg, level = self.log_queue.get_nowait()
            self.txt_logs.insert("end", msg + "\n")
            self.txt_logs.see("end")
        self.after(100, self._process_log_queue)

    def _set_status(self, text: str, progress: float = None):
        self.lbl_status.configure(text=text)
        if progress is not None:
            self.prog_bar.set(progress)

    # ------------------ PIPELINE EXECUTION ------------------
    def _start_generation(self):
        category = self.combo_category.get()
        total_count = self._get_target_count()
            
        self.is_processing = True
        self.cancel_requested = False
        self.btn_generate.configure(state="disabled")
        self.btn_play.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.prog_bar.set(0.0)
        
        voice, rate, pitch = self._get_current_voice_config()
        
        thread = threading.Thread(
            target=self._worker_pipeline,
            args=(category, voice, rate, pitch, total_count),
            daemon=True
        )
        thread.start()

    def _cancel_generation(self):
        if self.is_processing:
            self.cancel_requested = True
            self._log("Đang yêu cầu dừng tiến trình sau video hiện tại...", "warning")

    def _worker_pipeline(self, category: str, voice: str, rate: str, pitch: str, total_count: int):
        completed_count = 0
        api_key = self.config.get("gemini_api_key", "")
        
        self._log(f"🎬 BẮT ĐẦU CHIẾN DỊCH SẢN XUẤT {total_count} VIDEO CHO THỂ LOẠI: '{category}'...", "info")
        
        try:
            for vid_idx in range(1, total_count + 1):
                if self.cancel_requested:
                    self._log(f"⏹️ Đã dừng tiến trình theo yêu cầu của bạn.", "warning")
                    break

                video_prefix = f"[{vid_idx}/{total_count}]" if total_count > 1 else ""
                base_pct = (vid_idx - 1) / total_count
                span_pct = 1.0 / total_count

                # Step 1: Generate 1 fresh script on-demand with Gemini AI
                self._set_status(f"{video_prefix} Gemini AI đang sáng tạo kịch bản mới (chống trùng lặp)...", base_pct + 0.08 * span_pct)
                used_titles = script_manager.get_used_titles(category=category)
                used_pairs = script_manager.get_used_pairs(category=category)
                
                self._log(f"\n{video_prefix} 🧠 Đang gọi Gemini AI sáng tạo cặp so sánh mới cho: '{category}'...")
                raw_script = gemini_service.generate_single_comparison_script(
                    category=category,
                    used_titles=used_titles,
                    used_pairs=used_pairs,
                    api_key=api_key
                )
                
                script = script_manager.normalize_script_data(raw_script)
                script_title = script.get("title", "Kịch bản so sánh")
                script_angle = script.get("angle", "Góc nhìn toàn diện")
                item_a_name = script.get("item_a", {}).get("name", "Bên A")
                item_b_name = script.get("item_b", {}).get("name", "Bên B")
                segments = script.get("segments", [])
                
                self._log(f"{video_prefix} 🎬 Kịch bản: '{script_title}'", "success")
                self._log(f"{video_prefix} 🔍 Khía cạnh: [{script_angle}]")
                self._log(f"{video_prefix} ⚖️ Cặp đấu: {item_a_name} VS {item_b_name} | {len(segments)} phân đoạn (35-50s)")
                
                if self.cancel_requested:
                    break

                # Step 2: Download Images
                self._set_status(f"{video_prefix} Đang tải ảnh chất lượng cao...", base_pct + 0.25 * span_pct)
                
                timestamp_id = int(time.time() * 1000)
                img_a_path = str(TEMP_DIR / f"item_a_{timestamp_id}.png")
                img_b_path = str(TEMP_DIR / f"item_b_{timestamp_id}.png")
                
                query_a = script.get("item_a", {}).get("search_query", item_a_name)
                query_b = script.get("item_b", {}).get("search_query", item_b_name)
                
                self._log(f"{video_prefix} Tìm ảnh A: '{query_a}'")
                image_service.search_and_download_image(query_a, img_a_path, item_label="A", display_name=item_a_name)
                
                self._log(f"{video_prefix} Tìm ảnh B: '{query_b}'")
                image_service.search_and_download_image(query_b, img_b_path, item_label="B", display_name=item_b_name)
                
                self._update_thumbnails(img_a_path, img_b_path, item_a_name, item_b_name)

                if self.cancel_requested:
                    break

                # Step 3: Audio Generation
                self._set_status(f"{video_prefix} Đang tạo giọng đọc AI & Phụ đề chuẩn...", base_pct + 0.45 * span_pct)
                
                segment_audios = []
                for idx, seg in enumerate(segments):
                    seg_id = seg.get("segment_id", idx + 1)
                    text = seg.get("voiceover_text", "")
                    audio_file = str(TEMP_DIR / f"vo_{timestamp_id}_{seg_id}.mp3")
                    
                    tts_res = tts_service.generate_speech(
                        text=text,
                        output_audio_path=audio_file,
                        voice=voice,
                        rate=rate,
                        pitch=pitch
                    )
                    segment_audios.append({
                        "segment_id": seg_id,
                        "audio_path": tts_res["audio_path"],
                        "duration": tts_res["duration"],
                        "words": tts_res["words"]
                    })

                if self.cancel_requested:
                    break

                # Step 4: Render Video into Category Subfolder
                self._set_status(f"{video_prefix} Đang dựng video 9:16 (Layers, Subtitles, SFX)...", base_pct + 0.65 * span_pct)
                
                clean_cat = category.replace(":", " - ").replace("/", " - ").replace("\\", " - ")
                clean_cat = re.sub(r'[\\/*?:"<>|]', '', clean_cat).strip()
                cat_output_dir = OUTPUT_DIR / clean_cat
                cat_output_dir.mkdir(parents=True, exist_ok=True)
                
                final_video_file = sanitize_video_filename(script_title, cat_output_dir)
                final_video_path = str(final_video_file)
                
                def progress_cb(pct, msg, b_pct=base_pct, s_pct=span_pct, v_pref=video_prefix):
                    scaled = b_pct + (0.65 + pct * 0.33) * s_pct
                    self._set_status(f"{v_pref} [Dựng Video] {msg}", scaled)
                    
                video_engine.build_comparison_video(
                    script_data=script,
                    item_a_img=img_a_path,
                    item_b_img=img_b_path,
                    segment_audios=segment_audios,
                    output_path=final_video_path,
                    progress_callback=progress_cb
                )

                # Step 5: Save Used History & SEO Text File
                script_manager.mark_script_as_used(script, final_video_path)
                self.after(0, self._update_stats_ui)

                try:
                    seo_txt_file = final_video_file.with_suffix(".txt")
                    seo_text = gemini_service.generate_seo_metadata(script, category)
                    with open(seo_txt_file, "w", encoding="utf-8") as sf:
                        sf.write(seo_text)
                    self._log(f"{video_prefix} 📝 Đã tạo file SEO Caption: '{seo_txt_file.name}'", "info")
                except Exception as ex:
                    print(f"SEO file error: {ex}")

                self.last_rendered_video = final_video_path
                completed_count += 1
                self._log(f"{video_prefix} ✅ Xuất thành công: '{final_video_file.name}'", "success")

                # Step 6: Tự động gửi lên TikTok qua Buffer (Chạy ngầm)
                if self.config.get("auto_post_buffer_tiktok", False):
                    buf_tok = self.config.get("buffer_access_token", "").strip()
                    if buf_tok:
                        self._log(f"{video_prefix} 🚀 Đang tải video lên trung chuyển và phát hành TikTok...", "info")
                        def _bg_buffer_post(v_path, s_title, token, v_pref):
                            try:
                                import buffer_service
                                p_url = buffer_service.upload_to_catbox(v_path)
                                chans = buffer_service.get_connected_tiktok_channels(token)
                                if chans:
                                    c_ids = [c["id"] for c in chans]
                                    cap = f"{s_title}\n\nTheo bạn bên nào đỉnh hơn? Bình luận ngay nhé!\n#shorts #tiktok #sosanh #xuhuong #trending #fyp"
                                    buffer_service.post_video_to_buffer_tiktok(token, c_ids, p_url, cap)
                                    self._log(f"{v_pref} 📱 Đã gửi video thành công lên {len(c_ids)} kênh TikTok qua Buffer!", "success")
                            except Exception as bex:
                                self._log(f"{v_pref} ⚠️ Lỗi gửi Buffer TikTok: {bex}", "error")
                        threading.Thread(target=_bg_buffer_post, args=(final_video_path, script_title, buf_tok, video_prefix), daemon=True).start()

            # Finish Summary
            if completed_count == total_count:
                self._finish_processing(True, f"Đã sản xuất thành công {completed_count} video!")
            else:
                self._finish_processing(False, f"Đã dừng! Hoàn thành {completed_count}/{total_count} video.")
                
        except Exception as e:
            import traceback
            err_str = traceback.format_exc()
            self._log(f"Lỗi trong quá trình tạo video: {e}", "error")
            print(err_str)
            self._finish_processing(False, f"Lỗi: {e}")

    def _update_thumbnails(self, path_a: str, path_b: str, name_a: str, name_b: str):
        def update():
            try:
                if os.path.exists(path_a):
                    ia = Image.open(path_a).resize((90, 90), Image.Resampling.LANCZOS)
                    photo_a = ctk.CTkImage(light_image=ia, dark_image=ia, size=(90, 90))
                    self.lbl_img_a.configure(image=photo_a, text="")
                    self.lbl_img_a.image = photo_a
                    
                if os.path.exists(path_b):
                    ib = Image.open(path_b).resize((90, 90), Image.Resampling.LANCZOS)
                    photo_b = ctk.CTkImage(light_image=ib, dark_image=ib, size=(90, 90))
                    self.lbl_img_b.configure(image=photo_b, text="")
                    self.lbl_img_b.image = photo_b
            except Exception as e:
                print(f"Thumb error: {e}")
        self.after(0, update)

    def _finish_processing(self, success: bool, message: str):
        def finish():
            self.is_processing = False
            self.btn_generate.configure(state="normal")
            self.btn_cancel.configure(state="disabled")
            
            if success:
                self._set_status(message, 1.0)
                self.btn_play.configure(state="normal")
                self._log(f"🎉 HOÀN TẤT: {message}", "success")
                messagebox.showinfo("Thành công", f"{message}\n\nBạn có thể bấm nút 'Xem Video Vừa Tạo' hoặc mở 'Thư Mục Video' để xem thành phẩm.")
            else:
                self._set_status(f"❌ {message}", 0.0)
                self._log(f"❌ DỪNG LẠI DO LỖI: {message}", "error")
                if "Đã hủy bởi người dùng" not in message and "Đã dừng!" not in message:
                    messagebox.showerror("Thông Báo Lỗi", f"Tiến trình sản xuất đã dừng lại do lỗi sau:\n\n{message}\n\nVui lòng kiểm tra lại kết nối internet hoặc API Key rồi thử lại nhé!")
        self.after(0, finish)

def run_gui():
    app = AutoShortsApp()
    app.mainloop()

run_app = run_gui

if __name__ == "__main__":
    run_gui()
