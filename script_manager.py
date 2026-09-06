import os
import json
import time
import re
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
    used = _load_used_history()
    if not category:
        return [s.get("title", "").strip() for s in used if s.get("title")]
    return [s.get("title", "").strip() for s in used if s.get("category") == category and s.get("title")]

def get_used_pairs(category: Optional[str] = None) -> List[str]:
    """Get list of already compared product pairs, e.g. 'iPhone vs Samsung'."""
    used = _load_used_history()
    pairs = []
    for s in used:
        if category and s.get("category") != category:
            continue
        a = s.get("item_a", "")
        b = s.get("item_b", "")
        if isinstance(a, dict):
            a = a.get("name", "")
        if isinstance(b, dict):
            b = b.get("name", "")
        if a and b:
            pairs.append(f"{a} vs {b}")
    return pairs

def is_duplicate(title: str, name_a: str, name_b: str, category: Optional[str] = None) -> bool:
    """Check if title or the exact pair was already produced in history."""
    used = _load_used_history()
    clean_title = title.strip().lower()
    pair_str_1 = f"{name_a.strip().lower()} vs {name_b.strip().lower()}"
    pair_str_2 = f"{name_b.strip().lower()} vs {name_a.strip().lower()}"
    
    for s in used:
        if category and s.get("category") != category:
            continue
        u_title = s.get("title", "").strip().lower()
        if clean_title == u_title:
            return True
            
        u_a = (s.get("item_a", "") if isinstance(s.get("item_a"), str) else s.get("item_a", {}).get("name", "")).strip().lower()
        u_b = (s.get("item_b", "") if isinstance(s.get("item_b"), str) else s.get("item_b", {}).get("name", "")).strip().lower()
        
        u_pair_1 = f"{u_a} vs {u_b}"
        u_pair_2 = f"{u_b} vs {u_a}"
        
        if pair_str_1 == u_pair_1 or pair_str_1 == u_pair_2 or pair_str_2 == u_pair_1:
            return True
            
    return False

def mark_script_as_used(script: Dict[str, Any], video_path: str, channel_id: str = "", channel_name: str = ""):
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
        "rendered_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    used.append(record)
    _save_used_history(used)

if __name__ == "__main__":
    print("ScriptManager (Pure 1-Script On-Demand & Anti-Duplication) ready. Total used:", get_used_count())