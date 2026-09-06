import os
import sys
import time
import json
import random
import shutil
from pathlib import Path

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

def run_headless_pipeline():
    print("=" * 65)
    print("🤖 AUTO SHORTS - HEADLESS ZERO-TOUCH PRODUCER (0 VNĐ)")
    print(f"⏰ Thời gian chạy: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    cfg = config_manager.load_config()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip() or cfg.get("gemini_api_key", "").strip()
    buffer_token = os.environ.get("BUFFER_TOKEN", "").strip() or cfg.get("buffer_access_token", "").strip()

    if not gemini_key:
        print("[LỖI] Thiếu GEMINI_API_KEY. Vui lòng cấu hình trong GitHub Secrets hoặc config.json.")
        sys.exit(1)

    # 1. Khởi tạo tài nguyên hệ thống
    print("[1/6] Đang kiểm tra & khởi tạo tài nguyên đồ họa/font...")
    asset_manager.init_all_assets()

    # 2. Lựa chọn chủ đề không trùng lặp (Infinite Topic Engine)
    print("[2/6] Đang chọn lọc chủ đề so sánh (Chống trùng lặp 100%)...")
    categories = list(gemini_service.TOPIC_CATEGORIES.keys())
    random.shuffle(categories)
    selected_category = categories[0]

    used_titles = script_manager.get_used_titles(selected_category)
    used_pairs = script_manager.get_used_pairs(selected_category)

    # Tìm chủ đề tĩnh chưa dùng
    static_topics = gemini_service.TOPIC_CATEGORIES[selected_category]
    candidate_topic = None
    for top in static_topics:
        parts = top.split(" vs ")
        name_a = parts[0].strip() if len(parts) > 1 else top
        name_b = parts[1].strip() if len(parts) > 1 else "Bên B"
        if not script_manager.is_duplicate(top, name_a, name_b, selected_category):
            candidate_topic = top
            break

    print(f"-> Thể loại: {selected_category}")
    if candidate_topic:
        print(f"-> Chủ đề chọn từ kho: {candidate_topic}")
    else:
        print("-> Kho chủ đề tĩnh của thể loại này đã dùng hết. Kích hoạt AI sáng tạo chủ đề mới toanh!")

    # Sinh kịch bản qua Gemini
    script = gemini_service.generate_single_comparison_script(
        category=selected_category,
        specific_topic=candidate_topic,
        used_titles=used_titles,
        used_pairs=used_pairs,
        api_key=gemini_key
    )
    script = script_manager.normalize_script_data(script)
    print(f"-> Tiêu đề kịch bản: {script['title']}")
    print(f"-> So sánh: {script['item_a']['name']} VS {script['item_b']['name']}")

    # 3. Tải và xử lý hình ảnh 1:1
    print("[3/6] Đang tìm kiếm và xử lý hình ảnh sản phẩm 1:1...")
    img_a_path = str(TEMP_DIR / "item_a_square.png")
    img_b_path = str(TEMP_DIR / "item_b_square.png")

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
    print("[4/6] Đang sinh giọng đọc AI tiếng Việt chất lượng cao...")
    voice_choice = random.choice(["vi-VN-NamMinhNeural", "vi-VN-HoaiMyNeural"])
    seg_audios = []
    for seg in script["segments"]:
        sid = seg["segment_id"]
        audio_file = str(TEMP_DIR / f"vo_{sid}.mp3")
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

    # 5. Dựng video 9:16
    print("[5/6] Đang render video Full HD 1080x1920 (MoviePy + Pillow)...")
    clean_title = "".join(c for c in script["title"] if c.isalnum() or c in (" ", "_", "-")).strip()
    clean_title = clean_title.replace(" ", "_")[:35]
    out_video_path = str(OUTPUT_DIR / f"TikTok_{clean_title}_{int(time.time())}.mp4")

    video_engine.build_comparison_video(
        script_data=script,
        item_a_img=img_a_path,
        item_b_img=img_b_path,
        segment_audios=seg_audios,
        output_path=out_video_path,
        progress_callback=lambda p, msg: print(f"  [Render {p*100:4.1f}%] {msg}")
    )

    if not os.path.exists(out_video_path) or os.path.getsize(out_video_path) < 1000:
        print("[LỖI] Render video thất bại.")
        sys.exit(1)

    print(f"-> Render thành công: {out_video_path} ({os.path.getsize(out_video_path):,} bytes)")

    # Lưu lịch sử chống trùng
    script_manager.mark_script_as_used(script, out_video_path)
    print(f"-> Đã ghi nhận vào lịch sử chống trùng. Tổng video đã làm: {script_manager.get_used_count()}")

    # 6. Đăng tải lên TikTok qua Buffer API
    if buffer_token:
        print("[6/6] Đang tự động phát hành lên TikTok qua Buffer API...")
        try:
            # Lấy link direct public video
            public_video_url = buffer_service.upload_to_catbox(out_video_path)

            # Lấy các kênh TikTok
            channels = buffer_service.get_connected_tiktok_channels(buffer_token)
            if not channels:
                print("[BufferService] Cảnh báo: Không tìm thấy kênh TikTok nào trong Buffer.")
            else:
                ch_ids = [c["id"] for c in channels]
                ch_names = [c["name"] for c in channels]
                print(f"[BufferService] Đang đăng đồng loạt lên {len(ch_ids)} kênh: {', '.join(ch_names)}")

                caption = f"{script['title']}\n\nTheo bạn bên nào đỉnh hơn? Bình luận ngay nhé!\n#shorts #tiktok #sosanh #xuhuong #trending #fyp"
                
                # Nếu là lượt test ngay (TEST_NOW=true) thì đăng shareNow, ngược lại hẹn giờ ngẫu nhiên
                is_test_now = os.environ.get("TEST_NOW", "").lower() in ("true", "1", "yes")
                if is_test_now:
                    print("[BufferService] ⚡ Chế độ TEST_NOW kích hoạt: Đăng ngay lập tức (shareNow)!")
                    results = buffer_service.post_video_to_buffer_tiktok(
                        access_token=buffer_token,
                        channel_ids=ch_ids,
                        video_url=public_video_url,
                        caption=caption,
                        mode="shareNow",
                        due_at=None
                    )
                else:
                    from datetime import datetime, timedelta, timezone
                    rand_minutes = random.randint(12, 50)
                    rand_seconds = random.randint(0, 59)
                    rand_offset = timedelta(minutes=rand_minutes, seconds=rand_seconds)
                    scheduled_due_at = (datetime.now(timezone.utc) + rand_offset).strftime("%Y-%m-%dT%H:%M:%SZ")
                    print(f"[BufferService] 🎲 Đã tính mốc giờ đăng ngẫu nhiên: {scheduled_due_at} (Sau {rand_minutes} phút {rand_seconds} giây)")

                    results = buffer_service.post_video_to_buffer_tiktok(
                        access_token=buffer_token,
                        channel_ids=ch_ids,
                        video_url=public_video_url,
                        caption=caption,
                        mode="customScheduled",
                        due_at=scheduled_due_at
                    )
                print(f"[BufferService] Hoàn tất xử lý phát hành cho {len(results)} kênh TikTok!")
        except Exception as ex:
            print(f"[BufferService LỖI] {ex}")
    else:
        print("[6/6] Bỏ qua bước đăng TikTok vì chưa cấu hình BUFFER_TOKEN.")

    # Dọn dẹp temp
    cleanup_temp_folder()
    print("=" * 65)
    print("✅ QUY TRÌNH HOÀN TẤT THÀNH CÔNG!")
    print("=" * 65)

if __name__ == "__main__":
    run_headless_pipeline()
