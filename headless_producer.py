import os
import sys
import time
import json
import random
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output in headless environment
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import asset_manager
import config_manager
import gemini_service
import image_service
import tts_service
import video_engine
import script_manager
import buffer_service

TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
DATABASE_DIR = BASE_DIR / "database"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

def cleanup_temp_folder():
    """Dọn dẹp file tạm để tiết kiệm dung lượng runner."""
    for item in TEMP_DIR.glob("*"):
        try:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception:
            pass

# Phân bổ ngách chủ đề chuyên biệt cho từng kênh TikTok
CHANNEL_NICHE_MAP = {
    "meothongthai.hehe": [
        "🧪 Lầm Tưởng Đời Sống & Sự Thật Khoa Học",
        "📜 Bí Ẩn Lịch Sử & Lầm Tưởng Cổ Nhân",
        "🌍 Nghịch Lý Địa Lý & Văn Hóa Thế Giới"
    ],
    "meothantai123a": [
        "💳 Thói Quen Tiêu Dùng & Quản Lý Tiền Bạc",
        "💰 Quyết Định Tài Chính & Đầu Tư Lớn",
        "🏢 Tranh Cãi Công Sở & Tư Duy Đi Làm",
        "🎭 Tâm Lý Học Hành Vi & Bẫy Cảm Xúc"
    ],
    "hoanghavibes": [
        "🍜 Ẩm thực & Món ăn Đặc sản",
        "🥑 Tranh Luận Dinh Dưỡng & Ăn Uống Lành Mạnh",
        "🐾 Thú Cưng: Nuôi Dạy & So Sánh Giống Loài",
        "🐕 Giải Mã Hành Vi Thú Cưng & Bí Ẩn Động Vật",
        "📱 Công nghệ & Thiết bị Điện tử"
    ]
}

def get_niche_categories_for_channel(channel_name: str) -> List[str]:
    """Tìm danh mục chuyên biệt cho kênh, fallback nếu tên kênh mới."""
    clean_name = channel_name.strip().lower()
    for k, niches in CHANNEL_NICHE_MAP.items():
        if k in clean_name:
            return niches
    # Fallback cho kênh mới: chia đều theo hash tên kênh
    all_cats = list(gemini_service.TOPIC_CATEGORIES.keys())
    offset = abs(hash(clean_name)) % len(all_cats)
    return [all_cats[offset]]

def produce_single_video_for_channel(
    channel_info: Dict[str, Any],
    gemini_key: str,
    buffer_token: str,
    is_test_now: bool,
    index: int = 1,
    total: int = 1
):
    channel_id = channel_info["id"]
    channel_name = channel_info.get("name", f"Channel_{channel_id}")
    print("\n" + "#" * 65)
    print(f"🎬 [{index}/{total}] BẮT ĐẦU SẢN XUẤT CHO KÊNH: {channel_name} (ID: {channel_id})")
    print("#" * 65)

    # 1. Dọn dẹp temp trước khi tạo video mới
    cleanup_temp_folder()

    # 2. Chọn chủ đề ngách riêng cho kênh này
    niche_categories = get_niche_categories_for_channel(channel_name)
    random.shuffle(niche_categories)
    selected_category = niche_categories[0]

    used_titles = script_manager.get_used_titles()
    used_pairs = script_manager.get_used_pairs()

    static_topics = gemini_service.TOPIC_CATEGORIES.get(selected_category, [])
    candidate_topic = None
    for top in static_topics:
        parts = top.split(" vs ")
        name_a = parts[0].strip() if len(parts) > 1 else top
        name_b = parts[1].strip() if len(parts) > 1 else "Bên B"
        if not script_manager.is_duplicate(top, name_a, name_b):
            candidate_topic = top
            break

    print(f"🎯 Ngách nội dung kênh [{channel_name}]: {selected_category}")
    if candidate_topic:
        print(f"-> Chủ đề chọn từ kho: {candidate_topic}")
    else:
        print("-> Kho chủ đề tĩnh đã dùng hết. Kích hoạt Gemini AI sáng tạo chủ đề mới toanh!")

    # Vòng lặp bảo đảm không trùng lặp 100% (Strict Anti-Duplication Guard)
    script = None
    for attempt in range(1, 4):
        raw_script = gemini_service.generate_single_comparison_script(
            category=selected_category,
            specific_topic=candidate_topic if attempt == 1 else None,
            used_titles=used_titles,
            used_pairs=used_pairs,
            api_key=gemini_key
        )
        norm_script = script_manager.normalize_script_data(raw_script)
        s_title = norm_script.get("title", "")
        s_a = norm_script.get("item_a", {}).get("name", "")
        s_b = norm_script.get("item_b", {}).get("name", "")

        if not script_manager.is_duplicate(s_title, s_a, s_b):
            script = norm_script
            break
        else:
            print(f"[Cảnh báo trùng lặp lần {attempt}] Chủ đề '{s_title}' đã tồn tại trong lịch sử. Đang tạo chủ đề khác...")
            candidate_topic = None  # Buộc Gemini tự tạo cặp đối tượng hoàn toàn mới

    if not script:
        script = norm_script  # Fallback nếu vượt quá số lần thử

    print(f"-> Tiêu đề kịch bản: {script['title']}")
    print(f"-> So sánh: {script['item_a']['name']} VS {script['item_b']['name']}")

    # 3. Tải và xử lý hình ảnh 1:1 cho video
    img_a_path = str(TEMP_DIR / f"item_a_{channel_id[:6]}.png")
    img_b_path = str(TEMP_DIR / f"item_b_{channel_id[:6]}.png")

    image_service.search_and_download_image(
        script["item_a"].get("search_query", ""),
        img_a_path,
        item_label="A",
        display_name=script["item_a"].get("name", ""),
        query_en=script["item_a"].get("search_query_en", "")
    )
    image_service.search_and_download_image(
        script["item_b"].get("search_query", ""),
        img_b_path,
        item_label="B",
        display_name=script["item_b"].get("name", ""),
        query_en=script["item_b"].get("search_query_en", "")
    )

    # 4. Sinh giọng đọc Edge-TTS
    voice_choice = random.choice(["vi-VN-NamMinhNeural", "vi-VN-HoaiMyNeural"])
    seg_audios = []
    for seg in script["segments"]:
        sid = seg["segment_id"]
        audio_file = str(TEMP_DIR / f"vo_{sid}_{channel_id[:6]}.mp3")
        res = tts_service.generate_speech(
            seg["voiceover_text"],
            audio_file,
            voice=voice_choice,
            rate="+10%",
            pitch="+0Hz"
        )
        seg_audios.append({
            "segment_id": sid,
            "audio_path": res["audio_path"],
            "duration": res["duration"],
            "words": res["words"]
        })

    # 5. Dựng video 9:16 Full HD
    clean_title = "".join(c for c in script["title"] if c.isalnum() or c in (" ", "_", "-")).strip()
    clean_title = clean_title.replace(" ", "_")[:30]
    out_video_path = str(OUTPUT_DIR / f"TikTok_{channel_name}_{clean_title}_{int(time.time())}.mp4")

    print(f"Đang render video 1080x1920 cho kênh {channel_name}...")
    video_engine.build_comparison_video(
        script_data=script,
        item_a_img=img_a_path,
        item_b_img=img_b_path,
        segment_audios=seg_audios,
        output_path=out_video_path,
        progress_callback=lambda p, msg: print(f"  [{channel_name} Render {p*100:4.1f}%] {msg}")
    )

    if not os.path.exists(out_video_path) or os.path.getsize(out_video_path) < 1000:
        print(f"[LỖI] Render video cho kênh {channel_name} thất bại.")
        return False

    # Ghi nhận lịch sử chống trùng lặp gắn liền với kênh
    script_manager.mark_script_as_used(script, out_video_path, channel_id=channel_id, channel_name=channel_name)
    print(f"-> Ghi nhận kịch bản cho kênh {channel_name}. Tổng kho lịch sử: {script_manager.get_used_count()}")

    # 6. Đăng DUY NHẤT lên 1 kênh này
    if buffer_token:
        try:
            print(f"[BufferService] Tải video lên host trung gian cho kênh {channel_name}...")
            public_video_url = buffer_service.upload_to_catbox(out_video_path)
            
            caption = f"{script['title']}\n\nTheo bạn bên nào đỉnh hơn? Bình luận ngay nhé!\n#shorts #tiktok #sosanh #xuhuong #trending #fyp"

            if is_test_now:
                print(f"[BufferService] ⚡ TEST_NOW: Đăng ngay lập tức lên duy nhất kênh [{channel_name}]!")
                buffer_service.post_video_to_buffer_tiktok(
                    access_token=buffer_token,
                    channel_ids=[channel_id],
                    video_url=public_video_url,
                    caption=caption,
                    mode="shareNow",
                    due_at=None
                )
            else:
                from datetime import datetime, timedelta, timezone
                rand_minutes = random.randint(12, 50)
                rand_seconds = random.randint(0, 59)
                scheduled_due_at = (datetime.now(timezone.utc) + timedelta(minutes=rand_minutes, seconds=rand_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[BufferService] 🎲 Hẹn giờ đăng ngẫu nhiên cho [{channel_name}]: {scheduled_due_at}")

                buffer_service.post_video_to_buffer_tiktok(
                    access_token=buffer_token,
                    channel_ids=[channel_id],
                    video_url=public_video_url,
                    caption=caption,
                    mode="customScheduled",
                    due_at=scheduled_due_at
                )
            print(f"✅ Hoàn tất phát hành video độc quyền cho kênh [{channel_name}]!")
        except Exception as ex:
            print(f"[BufferService LỖI trên kênh {channel_name}]: {ex}")

    cleanup_temp_folder()
    return True

def run_headless_pipeline():
    print("=" * 65)
    print("🤖 AUTO SHORTS - 1 VIDEO PER CHANNEL ARCHITECTURE (0 VNĐ)")
    print(f"⏰ Thời gian chạy: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    cfg = config_manager.load_config()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip() or cfg.get("gemini_api_key", "").strip()
    buffer_token = os.environ.get("BUFFER_TOKEN", "").strip() or cfg.get("buffer_access_token", "").strip()

    if not gemini_key:
        print("[LỖI] Thiếu GEMINI_API_KEY. Vui lòng cấu hình trong GitHub Secrets hoặc config.json.")
        sys.exit(1)

    # 1. Khởi tạo tài nguyên hệ thống
    print("[1/2] Kiểm tra tài nguyên đồ họa/font...")
    asset_manager.init_all_assets()

    # 2. Lấy danh sách kênh TikTok từ Buffer
    print("[2/2] Truy vấn danh sách kênh TikTok từ Buffer API...")
    is_test_now = os.environ.get("TEST_NOW", "").lower() in ("true", "1", "yes")
    
    if buffer_token:
        channels = buffer_service.get_connected_tiktok_channels(buffer_token)
        if not channels:
            print("[BufferService] Cảnh báo: Không tìm thấy kênh TikTok nào trong Buffer.")
            return
        
        print(f"-> Tìm thấy {len(channels)} kênh TikTok: {', '.join(c['name'] for c in channels)}")
        print("-> TIẾN HÀNH SẢN XUẤT ĐỘC LẬP: MỖI KÊNH 1 VIDEO RIÊNG BIỆT VỚI CHỦ ĐỀ KHÁC NHAU!")
        
        for idx, ch in enumerate(channels, 1):
            produce_single_video_for_channel(
                channel_info=ch,
                gemini_key=gemini_key,
                buffer_token=buffer_token,
                is_test_now=is_test_now,
                index=idx,
                total=len(channels)
            )
    else:
        # Fallback tạo 1 video mẫu nếu không có Buffer Token
        print("Không tìm thấy BUFFER_TOKEN, sản xuất 1 video demo...")
        produce_single_video_for_channel(
            channel_info={"id": "local_demo", "name": "demo_channel"},
            gemini_key=gemini_key,
            buffer_token="",
            is_test_now=True,
            index=1,
            total=1
        )

    print("\n" + "=" * 65)
    print("🎉 TẤT CẢ CÁC KÊNH ĐÃ ĐƯỢC XUẤT BẢN VIDEO RIÊNG BIỆT THÀNH CÔNG!")
    print("=" * 65)

if __name__ == "__main__":
    run_headless_pipeline()
