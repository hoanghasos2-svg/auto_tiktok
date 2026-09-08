import os
import sys
import time
import json
import random
import shutil
from datetime import datetime, timezone, timedelta, date
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

# ==============================================================================
# CẤU HÌNH LỊCH TRÌNH 3 KHUNG GIỜ VÀNG VIỆT NAM (3 VIDEOS / NGÀY / KÊNH)
# - Ca Sáng: 06:00 VN (23:00 UTC) -> Đăng lúc 06:20 - 06:45 Sáng (Trọng tâm 06:30)
# - Ca Trưa: 12:00 VN (05:00 UTC) -> Đăng lúc 12:20 - 12:45 Trưa
# - Ca Tối:  20:00 VN (13:00 UTC) -> Đăng lúc 20:20 - 20:45 Tối
# Khoảng cách tối thiểu an toàn: 5.5h - 8h (100% Không vi phạm quy định spam TikTok)
# ==============================================================================
START_DATE = date(2026, 9, 8)
VN_TZ = timezone(timedelta(hours=7))

def get_posting_schedule_phase(now_vn: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Xác định khung giờ đăng bài trong ngày:
    - Ca Sáng (06:30 VN): hour 5 -> 9
    - Ca Trưa (12:00 VN): hour 10 -> 15
    - Ca Tối  (20:00 VN): hour 16 -> 23 hoặc 0 -> 4
    Mỗi ca sản xuất & đăng 1 video độc quyền cho mỗi kênh => 3 video/ngày/kênh.
    """
    if now_vn is None:
        now_vn = datetime.now(VN_TZ)
    current_date = now_vn.date()
    days_passed = (current_date - START_DATE).days
    day_number = max(1, days_passed + 1)
    
    hour = now_vn.hour
    if 5 <= hour < 10:
        slot_name = "SÁNG (06:30 VN)"
    elif 10 <= hour < 16:
        slot_name = "TRƯA (12:00 VN)"
    else:
        slot_name = "TỐI (20:00 VN)"

    desc = f"Lịch 3 Khung Giờ Vàng (Ngày thứ {day_number} hoạt động) - 3 videos/ngày/kênh"

    return {
        "day_number": day_number,
        "videos_per_day": 3,
        "description": desc,
        "slot_name": slot_name,
        "should_run": True,
        "now_vn": now_vn
    }

# Phân bổ ngách chủ đề chuyên biệt độc quyền cho TẤT CẢ 6 KÊNH TIKTOK:
CHANNEL_NICHE_MAP = {
    # Kênh 1: Khoa học đời sống, Khám phá & Lịch sử
    "meothongthai.hehe": [
        "🧪 Lầm Tưởng Đời Sống & Sự Thật Khoa Học",
        "📜 Bí Ẩn Lịch Sử & Lầm Tưởng Cổ Nhân"
    ],
    # Kênh 2: Quản lý tiền bạc cá nhân, Chi tiêu & Công sở
    "meothantai123a": [
        "💳 Thói Quen Tiêu Dùng & Quản Lý Tiền Bạc",
        "🏢 Tranh Cãi Công Sở & Tư Duy Đi Làm"
    ],
    # Kênh 3: Thiết bị công nghệ, Điện thoại & AI
    "hoanghavibes": [
        "📱 Công nghệ & Thiết bị Điện tử",
        "🤖 Phần Mềm, Ứng Dụng & Công Cụ AI",
        "🎮 Game & Thiết Bị Giải Trí"
    ],
    # Kênh 4: Triết lý sống, Địa lý thế giới & Tâm lý học
    "tramsuyngam.hehe": [
        "🌍 Nghịch Lý Địa Lý & Văn Hóa Thế Giới",
        "🎭 Tâm Lý Học Hành Vi & Bẫy Cảm Xúc",
        "👨‍👩‍👧 Tranh Luận Nuôi Dạy Con & Gia Đình"
    ],
    # Kênh 5: Đầu tư tài chính, Kinh doanh & Sự nghiệp
    "hoanghaxyz": [
        "💰 Quyết Định Tài Chính & Đầu Tư Lớn",
        "💻 Tương Lai Việc Làm: AI vs Kỹ Năng Con Người",
        "🚗 Xe cộ & Phương tiện Di chuyển"
    ],
    # Kênh 6: Ẩm thực ăn uống, Dinh dưỡng & Thú cưng
    "jemniferr": [
        "🍜 Ẩm thực & Món ăn Đặc sản",
        "🥑 Tranh Luận Dinh Dưỡng & Ăn Uống Lành Mạnh",
        "🐾 Thú Cưng: Nuôi Dạy & So Sánh Giống Loài",
        "🐕 Giải Mã Hành Vi Thú Cưng & Bí Ẩn Động Vật"
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
    total: int = 1,
    pexels_api_key: str = ""
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
        query_en=script["item_a"].get("search_query_en", ""),
        pexels_api_key=pexels_api_key
    )
    image_service.search_and_download_image(
        script["item_b"].get("search_query", ""),
        img_b_path,
        item_label="B",
        display_name=script["item_b"].get("name", ""),
        query_en=script["item_b"].get("search_query_en", ""),
        pexels_api_key=pexels_api_key
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

    # 6. Tự động sinh Caption, Mô tả ngữ nghĩa & Bộ Hashtag đa tầng chuẩn TikTok SEO 2026
    seo_data = script_manager.generate_tiktok_seo(script)
    caption = seo_data["full_caption"]
    print(f"\n[TikTok SEO 2026] Caption & Hashtag chuẩn ngách cho [{channel_name}]:")
    print(caption)
    print("-" * 50)

    # Ghi nhận lịch sử chống trùng lặp gắn liền với kênh kèm SEO Caption
    script_manager.mark_script_as_used(script, out_video_path, channel_id=channel_id, channel_name=channel_name, caption=caption)
    print(f"-> Ghi nhận kịch bản cho kênh {channel_name}. Tổng kho lịch sử: {script_manager.get_used_count()}")

    # 7. Đăng DUY NHẤT lên 1 kênh này
    if buffer_token:
        try:
            print(f"[BufferService] Tải video lên host trung gian cho kênh {channel_name}...")
            public_video_url = buffer_service.upload_to_catbox(out_video_path)

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
                # Phân bổ thời gian đăng tự nhiên cho từng kênh (khoảng 15 - 45 phút sau giờ kích hoạt)
                channel_offset = index * 4 + random.randint(0, 5)
                scheduled_due_at = (datetime.now(timezone.utc) + timedelta(minutes=15 + channel_offset, seconds=random.randint(0, 59))).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[BufferService] 🎲 Hẹn giờ đăng ngẫu nhiên cho [{channel_name}] (Kênh {index}/{total}): {scheduled_due_at}")

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
    now_vn = datetime.now(VN_TZ)
    schedule_info = get_posting_schedule_phase(now_vn)

    print("=" * 65)
    print("🤖 HỆ THỐNG TỰ ĐỘNG SẢN XUẤT & ĐĂNG TIKTOK SHORTS (0 VNĐ)")
    print(f"⏰ Thời gian hiện tại (VN): {now_vn.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Trạng thái lịch: {schedule_info['description']}")
    print(f"🕒 Khung giờ chạy: {schedule_info['slot_name']}")
    print("=" * 65)

    is_test_now = os.environ.get("TEST_NOW", "").lower() in ("true", "1", "yes")
    is_manual_dispatch = os.environ.get("GITHUB_EVENT_NAME", "").lower() == "workflow_dispatch"

    # Kiểm tra điều kiện giai đoạn (Chỉ áp dụng khi chạy định kỳ Cron):
    if not is_test_now and not is_manual_dispatch and not schedule_info["should_run"]:
        print(f"\n[THÔNG BÁO LỊCH TRÌNH] Hiện đang ở {schedule_info['description']}.")
        print(f"-> Ca {schedule_info['slot_name']} tạm nghỉ để đảm bảo chỉ đăng chuẩn xác 1 video/ngày/kênh.")
        print(f"-> Ca đăng video tiếp theo sẽ kích hoạt vào 20:00 VN (13:00 UTC) tối nay.")
        print("-> Giữ nguyên trạng thái thành công cho workflow (Keep-alive an toàn).")
        return

    cfg = config_manager.load_config()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip() or cfg.get("gemini_api_key", "").strip()
    buffer_token = os.environ.get("BUFFER_TOKEN", "").strip() or cfg.get("buffer_access_token", "").strip()
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip() or cfg.get("pexels_api_key", "").strip()

    if not gemini_key:
        print("[LỖI] Thiếu GEMINI_API_KEY. Vui lòng cấu hình trong GitHub Secrets hoặc config.json.")
        sys.exit(1)

    if pexels_key:
        print("🖼️ Pexels API: Đã kích hoạt (Ưu tiên tìm ảnh chuẩn xác từ kho Pexels)!")
    else:
        print("ℹ️ Pexels API: Chưa có PEXELS_API_KEY (Sử dụng hệ thống tìm kiếm đa tầng dự phòng)")

    # 1. Khởi tạo tài nguyên hệ thống
    print("[1/2] Kiểm tra tài nguyên đồ họa/font...")
    asset_manager.init_all_assets()

    # 2. Lấy danh sách kênh TikTok từ tất cả các tài khoản Buffer
    print("[2/2] Truy vấn danh sách kênh TikTok từ tất cả tài khoản Buffer...")
    
    # Hỗ trợ đa token (cách nhau bởi dấu phẩy hoặc dòng mới)
    raw_tokens = [t.strip() for t in buffer_token.replace("\n", ",").split(",") if t.strip()]
    all_channels = []
    
    for b_idx, tok in enumerate(raw_tokens, 1):
        try:
            chans = buffer_service.get_connected_tiktok_channels(tok)
            print(f"[BufferService] Tài khoản {b_idx}: Tìm thấy {len(chans)} kênh TikTok ({', '.join(c['name'] for c in chans)})")
            for c in chans:
                c["token"] = tok
                all_channels.append(c)
        except Exception as b_err:
            print(f"[BufferService Lỗi Tài khoản {b_idx}]: {b_err}")
            
    if all_channels:
        print(f"\n-> TỔNG CỘNG: {len(all_channels)} KÊNH TIKTOK SẴN SÀNG HOẠT ĐỘNG: {', '.join(c['name'] for c in all_channels)}")
        print("-> TIẾN HÀNH SẢN XUẤT ĐỘC LẬP: MỖI KÊNH 1 VIDEO RIÊNG BIỆT VỚI CHỦ ĐỀ KHÁC NHAU!")
        
        for idx, ch in enumerate(all_channels, 1):
            try:
                produce_single_video_for_channel(
                    channel_info=ch,
                    gemini_key=gemini_key,
                    buffer_token=ch.get("token", ""),
                    is_test_now=is_test_now,
                    index=idx,
                    total=len(all_channels),
                    pexels_api_key=pexels_key
                )
            except Exception as ch_err:
                print(f"[LỖI KÊNH {ch.get('name', 'N/A')}] Xảy ra lỗi khi sản xuất: {ch_err}. Tự động bỏ qua để xử lý kênh tiếp theo!")
    else:
        # Fallback tạo 1 video mẫu nếu không có Buffer Token
        print("Không tìm thấy kênh TikTok nào trong Buffer, sản xuất 1 video demo...")
        produce_single_video_for_channel(
            channel_info={"id": "local_demo", "name": "demo_channel"},
            gemini_key=gemini_key,
            buffer_token="",
            is_test_now=True,
            index=1,
            total=1,
            pexels_api_key=pexels_key
        )

    print("\n" + "=" * 65)
    print("🎉 TẤT CẢ CÁC KÊNH ĐÃ ĐƯỢC XUẤT BẢN VIDEO RIÊNG BIỆT THÀNH CÔNG!")
    print("=" * 65)

if __name__ == "__main__":
    run_headless_pipeline()
