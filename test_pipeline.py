import time
import os
from pathlib import Path
import gemini_service
import image_service
import tts_service
import video_engine
import asset_manager

def run_test():
    print("[Test] 1. Khoi tao assets...")
    asset_manager.init_all_assets()

    print("[Test] 2. Sinh kich ban mau...")
    topic = "iPhone 15 Pro Max vs Samsung Galaxy S24 Ultra"
    script = gemini_service.generate_comparison_script(topic)
    print("Script title:", script["title"])

    print("[Test] 3. Xu ly hinh anh...")
    img_a = "temp/test_item_a.png"
    img_b = "temp/test_item_b.png"
    image_service.search_and_download_image(script["item_a"]["search_query"], img_a, item_label="A", display_name=script["item_a"]["name"])
    image_service.search_and_download_image(script["item_b"]["search_query"], img_b, item_label="B", display_name=script["item_b"]["name"])

    print("[Test] 4. Tao giong doc TTS...")
    seg_audios = []
    test_segments = script["segments"][:2]
    for seg in test_segments:
        sid = seg["segment_id"]
        audio_p = f"temp/test_vo_{sid}.mp3"
        print(f"Segment {sid}: {seg['voiceover_text']}")
        res = tts_service.generate_speech(seg["voiceover_text"], audio_p)
        seg_audios.append({
            "segment_id": sid,
            "audio_path": res["audio_path"],
            "duration": res["duration"],
            "words": res["words"]
        })

    print("[Test] 5. Dung video test 9:16 (MoviePy + Pillow)...")
    test_script = {
        "title": script["title"],
        "item_a": script["item_a"],
        "item_b": script["item_b"],
        "segments": test_segments
    }
    out_vid = "output/test_sample_shorts.mp4"
    video_engine.build_comparison_video(
        test_script,
        img_a,
        img_b,
        seg_audios,
        out_vid,
        lambda p, m: print(f"Progress {p*100:.1f}%: {m}")
    )

    if os.path.exists(out_vid) and os.path.getsize(out_vid) > 1000:
        print(f"[Test SUCCESS] Video render thanh cong tai: {out_vid}")
        print(f"[Test SUCCESS] Kich thuoc video: {os.path.getsize(out_vid):,} bytes")
    else:
        print("[Test FAILED] Khong tim thay file video.")

if __name__ == "__main__":
    run_test()