import os
import json
import time
import re
import random
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional

import content_moderator

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)

USED_FILE = DB_DIR / "used_history.json"

def normalize_script_data(script: Dict[str, Any]) -> Dict[str, Any]:
    """Robustly normalize any script schema returned by Gemini AI or history."""
    title = script.get("title") or "So Sánh Sản Phẩm"
    
    # Handle item_a
    item_a_raw = script.get("item_a")
    if isinstance(item_a_raw, str):
        item_a = {"name": item_a_raw, "search_query": f"{item_a_raw} high quality photo"}
    elif isinstance(item_a_raw, dict) and item_a_raw.get("name"):
        item_a = item_a_raw
    else:
        item_a = {}

    # Handle item_b
    item_b_raw = script.get("item_b")
    if isinstance(item_b_raw, str):
        item_b = {"name": item_b_raw, "search_query": f"{item_b_raw} high quality photo"}
    elif isinstance(item_b_raw, dict) and item_b_raw.get("name"):
        item_b = item_b_raw
    else:
        item_b = {}

    if not item_a.get("name") or not item_b.get("name"):
        clean_title = title.split(":")[0].strip()
        parts = re.split(r"\s+(?:vs|và|với|hoặc)\s+", clean_title, flags=re.IGNORECASE)
        name_a = parts[0].strip() if len(parts) >= 1 else "Bên A"
        name_b = parts[1].strip() if len(parts) >= 2 else "Bên B"
        if not item_a.get("name"):
            item_a = {"name": name_a, "search_query": f"{name_a} high quality photo"}
        if not item_b.get("name"):
            item_b = {"name": name_b, "search_query": f"{name_b} high quality photo"}
        
    raw_segs = script.get("segments", [])
    normalized_segs = []
    poses = ["pointing", "thinking", "thinking", "chill", "chill", "cta"]
    
    for idx, seg in enumerate(raw_segs):
        if not isinstance(seg, dict):
            continue
        seg_id = seg.get("segment_id") or seg.get("segment_number") or (idx + 1)
        vo_text = (
            seg.get("voiceover_text") or
            seg.get("audio") or
            seg.get("text") or
            seg.get("voiceover") or
            seg.get("dialogue") or
            seg.get("content") or
            f"Phân đoạn {seg_id} so sánh giữa {item_a.get('name')} và {item_b.get('name')}."
        ).strip()
        
        normalized_segs.append({
            "segment_id": seg_id,
            "voiceover_text": vo_text,
            "pose": seg.get("pose") or poses[min(idx, len(poses)-1)],
            "sfx": seg.get("sfx") or ("whoosh" if idx in [0, len(raw_segs)-1] else "pop"),
            "highlight_item": seg.get("highlight_item") or ("A" if idx == 1 else "B" if idx == 2 else "both")
        })
        
    return {
        "id": script.get("id") or f"sc_{int(time.time()*1000)}",
        "title": title,
        "category": script.get("category") or "Tổng hợp",
        "angle": script.get("angle") or script.get("aspect") or "Toàn diện",
        "item_a": item_a,
        "item_b": item_b,
        "segments": normalized_segs,
        "created_at": script.get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S")
    }

def _load_used_history() -> List[Dict[str, Any]]:
    if USED_FILE.exists():
        try:
            with open(USED_FILE, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                return [s for s in data if isinstance(s, dict)]
        except Exception as e:
            print(f"[ScriptManager] Error loading used history: {e}")
            return []
    return []

def _save_used_history(data: List[Dict[str, Any]]):
    try:
        with open(USED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ScriptManager] Error saving used history: {e}")

def get_used_count(category: Optional[str] = None) -> int:
    used = _load_used_history()
    if not category or category == "Tất cả":
        return len(used)
    return sum(1 for s in used if s.get("category") == category)

def get_used_titles(category: Optional[str] = None) -> List[str]:
    """Lấy danh sách tiêu đề đã làm TOÀN CỤC trên toàn bộ hệ thống để chống trùng 100%."""
    used = _load_used_history()
    return [s.get("title", "").strip() for s in used if s.get("title")]

def get_used_pairs(category: Optional[str] = None) -> List[str]:
    """Lấy danh sách các cặp đối đầu TOÀN CỤC đã làm, không phân biệt thể loại hay kênh."""
    used = _load_used_history()
    pairs = []
    for s in used:
        a = s.get("item_a", "")
        b = s.get("item_b", "")
        if isinstance(a, dict):
            a = a.get("name", "")
        if isinstance(b, dict):
            b = b.get("name", "")
        if a and b:
            pairs.append(f"{a} vs {b}")
    return pairs

def extract_keywords(text: str) -> set:
    """Tách từ khóa cốt lõi để so sánh ngữ nghĩa và chống trùng lặp biến thể."""
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    stop_words = {"vs", "và", "với", "hay", "hoặc", "cho", "của", "là", "các", "những", "sự", "thật", "bí", "mật", "đỉnh", "hơn", "nhất", "thế", "nào"}
    words = {w for w in clean.split() if len(w) > 1 and w not in stop_words}
    return words

def is_duplicate(title: str, name_a: str, name_b: str, category: Optional[str] = None) -> bool:
    """
    Kiểm tra trùng lặp TOÀN CỤC tuyệt đối:
    1. Trùng khớp tiêu đề chính xác hoặc tiêu đề con.
    2. Trùng cặp đối đầu (A vs B hoặc B vs A).
    3. Trùng ngữ nghĩa cốt lõi (Keyword Jaccard overlap > 60%).
    """
    used = _load_used_history()
    clean_title = title.strip().lower()
    
    clean_a = name_a.strip().lower()
    clean_b = name_b.strip().lower()
    pair_1 = f"{clean_a} vs {clean_b}"
    pair_2 = f"{clean_b} vs {clean_a}"
    kw_input = extract_keywords(f"{title} {name_a} {name_b}")

    for s in used:
        # 1. Trùng tiêu đề
        u_title = s.get("title", "").strip().lower()
        if clean_title == u_title or (len(clean_title) > 6 and clean_title in u_title) or (len(u_title) > 6 and u_title in clean_title):
            return True
            
        # 2. Trùng cặp đối tượng
        u_a = (s.get("item_a", "") if isinstance(s.get("item_a"), str) else s.get("item_a", {}).get("name", "")).strip().lower()
        u_b = (s.get("item_b", "") if isinstance(s.get("item_b"), str) else s.get("item_b", {}).get("name", "")).strip().lower()
        
        u_pair_1 = f"{u_a} vs {u_b}"
        u_pair_2 = f"{u_b} vs {u_a}"
        
        if pair_1 in (u_pair_1, u_pair_2) or pair_2 in (u_pair_1, u_pair_2):
            return True
            
        # Trùng chéo đối tượng (ví dụ: cùng so sánh Nô lệ và Thợ xây)
        if (clean_a and clean_a in u_a) and (clean_b and clean_b in u_b):
            return True
        if (clean_a and clean_a in u_b) and (clean_b and clean_b in u_a):
            return True

        # 3. Trùng từ khóa cốt lõi (Overlap matching)
        kw_history = extract_keywords(f"{u_title} {u_a} {u_b}")
        if kw_input and kw_history:
            intersection = kw_input.intersection(kw_history)
            union = kw_input.union(kw_history)
            overlap_ratio = len(intersection) / len(union) if union else 0
            if overlap_ratio >= 0.55 or (len(intersection) >= 3 and len(intersection) >= len(kw_input) * 0.6):
                return True
                
    return False

def slugify_hashtag(text: str) -> str:
    """Chuyển đổi tên đối tượng tiếng Việt thành hashtag chuẩn không dấu (VD: 'Cà Phê Muối' -> '#caphemuoi')."""
    if not text:
        return ""
    text = text.replace("đ", "d").replace("Đ", "d")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]", "", text).lower()
    return f"#{text}" if text else ""

def generate_tiktok_seo(script: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tự động sản sinh Caption, Đoạn văn ngữ nghĩa (Semantic Description), Câu hỏi kích thích tranh cãi (Debate Hook)
    và Bộ Hashtag đa tầng (Entity + Niche + Format) đạt chuẩn TikTok SEO năm 2026.
    """
    title = script.get("title", "KÈO ĐẤU SO SÁNH").strip()
    cat = (script.get("category") or "").lower()
    angle = (script.get("angle") or "toàn diện").strip()
    
    item_a = script.get("item_a", {})
    item_b = script.get("item_b", {})
    name_a = (item_a.get("name") if isinstance(item_a, dict) else str(item_a)).strip() or "Bên A"
    name_b = (item_b.get("name") if isinstance(item_b, dict) else str(item_b)).strip() or "Bên B"
    
    # 1. Thẻ thực thể cụ thể (Entity Tags - Trọng tâm tìm kiếm của thuật toán TikTok)
    tag_a = slugify_hashtag(name_a)
    tag_b = slugify_hashtag(name_b)
    entity_tags = [t for t in [tag_a, tag_b] if t and len(t) > 2]
    
    # 2. Thẻ ngách ngành & Câu hỏi phân cực chia phe (Polarizing Debate Hooks)
    niche_tags = []
    if any(k in cat for k in ["ẩm thực", "món", "ăn", "uống", "cà phê", "nấu", "food"]):
        niche_tags = ["#amthuc", "#foodtiktok", "#reviewanngon", "#monngon"]
        debate_hooks = [
            f"Nếu chỉ được chọn 1 món duy nhất để thưởng thức, bạn chọn {name_a} hay {name_b}?",
            f"Team {name_a} hay Team {name_b}? Bình luận điểm danh xem phe nào đông hơn!",
            f"Theo khẩu vị của bạn, bên nào mới thực sự là 'chân ái'? Để lại góc nhìn bên dưới nhé!"
        ]
    elif any(k in cat for k in ["công nghệ", "điện thoại", "laptop", "máy tính", "apple", "samsung", "ai", "tech"]):
        niche_tags = ["#congnghe", "#tech", "#reviewcongnghe", "#smartphone"]
        debate_hooks = [
            f"Nếu được chọn 1 trong 2 máy để dùng 5 năm tới, bạn chọn {name_a} hay {name_b}?",
            f"Bỏ qua yếu tố thương hiệu, theo bạn bên nào mới thực sự 'đáng tiền' hơn?",
            f"Team {name_a} hay Team {name_b}? Bình luận công tâm xem ai vượt trội hơn nhé!"
        ]
    elif any(k in cat for k in ["thú cưng", "chó", "mèo", "động vật", "pet"]):
        niche_tags = ["#thucung", "#petsoftiktok", "#chomeo", "#yeudongvat"]
        debate_hooks = [
            f"Nuôi {name_a} hay {name_b} sẽ quấn chủ và tình cảm hơn? Bạn về phe nào?",
            f"Bạn thuộc hội yêu thích bé cưng nào? Bình luận khoe kinh nghiệm thực tế nhé!",
            f"Nếu được đón 1 bé về nhà ngay hôm nay, bạn chọn {name_a} hay {name_b}?"
        ]
    elif any(k in cat for k in ["tài chính", "tiền", "tiết kiệm", "đầu tư", "chi tiêu", "giàu"]):
        niche_tags = ["#taichinh", "#quanlytaichinh", "#dautu", "#kiemtien"]
        debate_hooks = [
            f"Ở góc nhìn quản lý tài chính thông minh, bạn chọn hướng đi của {name_a} hay {name_b}?",
            f"Liệu quyết định nào sẽ giúp bạn an tâm tài chính lâu dài hơn? Chia sẻ góc nhìn nhé!",
            f"Quan điểm của bạn thế nào: Đứng về phía {name_a} hay {name_b}?"
        ]
    elif any(k in cat for k in ["công sở", "đi làm", "việc", "sếp", "đồng nghiệp", "tâm lý"]):
        niche_tags = ["#congso", "#dilam", "#chuyencongso", "#tamly"]
        debate_hooks = [
            f"Trong môi trường làm việc thực tế, bạn đồng tình với {name_a} hay {name_b}?",
            f"Theo bạn, tư duy nào mới giúp sự nghiệp thăng tiến bền vững hơn?",
            f"Bạn thuộc tuýp người của {name_a} hay {name_b}? Bình luận chia sẻ nhé!"
        ]
    elif any(k in cat for k in ["xe", "ô tô", "xe máy", "vinfast"]):
        niche_tags = ["#xehay", "#danhgiaxe", "#oto", "#xemay"]
        debate_hooks = [
            f"Với nhu cầu đi lại thực tế hàng ngày, bạn sẽ xuống tiền cho {name_a} hay {name_b}?",
            f"Bên nào mang lại cảm giác lái và độ kinh tế vượt trội hơn? Để lại đánh giá nhé!"
        ]
    else:
        niche_tags = ["#kienthuc", "#meovat", "#suthat", "#gocnhin"]
        debate_hooks = [
            f"Nhiều người vẫn đang phân vân giữa {name_a} và {name_b}. Còn bạn, bạn chọn phe nào?",
            f"Góc nhìn của bạn thế nào? Để lại bình luận công tâm bên dưới nhé!",
            f"Nếu phải đưa ra lựa chọn ngay lúc này, bạn sẽ nghiêng về bên nào?"
        ]

    # 3. Thẻ định dạng & Khám phá xu hướng (Format & Discovery Tags)
    format_tags = ["#sosanh", "#doidau", "#learnontiktok", "#xuhuong"]

    # Tổng hợp 6-7 tags chuẩn SEO không trùng lặp
    all_tags = []
    for t in entity_tags + niche_tags[:2] + format_tags[:2]:
        if t and t not in all_tags:
            all_tags.append(t)
    hashtag_line = " ".join(all_tags[:7])

    # 4. Đoạn văn ngữ nghĩa (Semantic Description) tối ưu cho thanh tìm kiếm TikTok Search
    semantic_desc = f"So sánh đối đầu chi tiết giữa {name_a} và {name_b} về {angle.lower()}. Khám phá ưu nhược điểm thực tế để tìm ra lựa chọn tối ưu nhất dành cho bạn!"

    # 5. Câu hỏi kích hoạt tranh luận
    debate_hook = random.choice(debate_hooks)

    # 6. Ghép thành Caption hoàn chỉnh chuẩn SEO TikTok 2026
    full_caption = f"⚖️ {title}\n\n{semantic_desc}\n\n👉 {debate_hook}\n\n{hashtag_line}"

    return {
        "full_caption": full_caption,
        "hashtags": all_tags,
        "hashtag_line": hashtag_line,
        "semantic_desc": semantic_desc,
        "debate_hook": debate_hook
    }

def mark_script_as_used(script: Dict[str, Any], video_path: str, channel_id: str = "", channel_name: str = "", caption: str = ""):
    """Permanently record completed script in used history to ensure zero duplication."""
    used = _load_used_history()
    item_a_name = script.get("item_a", {}).get("name") if isinstance(script.get("item_a"), dict) else str(script.get("item_a", "Bên A"))
    item_b_name = script.get("item_b", {}).get("name") if isinstance(script.get("item_b"), dict) else str(script.get("item_b", "Bên B"))
    
    record = {
        "id": script.get("id", f"used_{int(time.time()*1000)}"),
        "title": script.get("title", "Unknown"),
        "category": script.get("category", "General"),
        "angle": script.get("angle", "Toàn diện"),
        "item_a": item_a_name,
        "item_b": item_b_name,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "video_path": video_path,
        "caption": caption,
        "rendered_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    used.append(record)
    _save_used_history(used)

if __name__ == "__main__":
    print("ScriptManager (Pure 1-Script On-Demand & Anti-Duplication) ready. Total used:", get_used_count())