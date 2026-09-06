import time
import os
import gemini_service
import image_service
import tts_service
import video_engine
import asset_manager

def main():
    print("[Full Run] Bắt đầu quy trình sản xuất video hoàn chỉnh...")
    asset_manager.init_all_assets()
    
    topic = "Cơm tấm Sài Gòn vs Phở bò Hà Nội"
    script = gemini_service.generate_comparison_script(topic)
    print(f"Tiêu đề kịch bản: {script['title']}")

    img_a = "temp/full_item_a.png"
    img_b = "temp/full_item_b.png"
    image_service.search_and_download_image(script['item_a']['search_query'], img_a, item_label='A', display_name=script['item_a']['name'])
    image_service.search_and_download_image(script['item_b']['search_query'], img_b, item_label='B', display_name=script['item_b']['name'])

    seg_audios = []
    for seg in script['segments']:
        sid = seg['segment_id']
        audio_p = f"temp/full_vo_{sid}.mp3"
        print(f"Tạo audio segment {sid}...")
        res = tts_service.generate_speech(seg['voiceover_text'], audio_p, voice='vi-VN-NamMinhNeural')
        seg_audios.append({
            'segment_id': sid,
            'audio_path': res['audio_path'],
            'duration': res['duration'],
            'words': res['words']
        })

    out_vid = "output/Shorts_ComTam_vs_PhoBo_Full.mp4"
    video_engine.build_comparison_video(
        script,
        img_a,
        img_b,
        seg_audios,
        out_vid,
        lambda p, m: print(f"Progress {p*100:.1f}%: {m}")
    )

    if os.path.exists(out_vid):
        print(f"[SUCCESS] Video hoàn chỉnh đã tạo thành công tại: {out_vid}")
        print(f"[SUCCESS] Dung lượng video: {os.path.getsize(out_vid):,} bytes")

if __name__ == "__main__":
    main()