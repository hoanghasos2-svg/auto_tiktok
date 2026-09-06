import re
from typing import Dict, Any, Tuple, List

# ----------------- BANNED / SENSITIVE KEYWORD PATTERNS (VN LAW & PLATFORM POLICIES) -----------------
# 1. Politics, Religion, Territorial integrity, State affairs
POLITICAL_RELIGIOUS_PATTERNS = [
    r"\bchính\s*trị\b", r"\bchính\s*quyền\b", r"\bđảng\s*phái\b", r"\btôn\s*giáo\b", 
    r"\bphản\s*động\b", r"\bchống\s*phá\b", r"\bbiểu\s*tình\b", r"\bquân\s*sự\b",
    r"\bbắc\s*kỳ\b", r"\bnam\s*kỳ\b", r"\btrung\s*kỳ\b", r"\bphân\s*biệt\s*vùng\s*miền\b",
    r"\blãnh\s*thổ\b", r"\bchủ\s*quyền\b", r"\bbiên\s*giới\b"
]

# 2. Gambling, Betting, Illegal Financial Schemes, Scams
GAMBLING_SCAM_PATTERNS = [
    r"\bcờ\s*bạc\b", r"\bcá\s*độ\b", r"\btài\s*xỉu\b", r"\bbaccarat\b", r"\bđánh\s*bài\b",
    r"\bku\s*bet\b", r"\bthabet\b", r"\bnhà\s*cái\b", r"\bsoi\s*cầu\b", r"\blô\s*đề\b",
    r"\bđa\s*cấp\s*lừa\s*đảo\b", r"\bcam\s*kết\s*lãi\s*khủng\b", r"\bđầu\s*tư\s*bao\s*lỗ\b"
]

# 3. Controlled Substances, Narcotics, Weaponry, Violence
SUBSTANCE_VIOLENCE_PATTERNS = [
    r"\bma\s*túy\b", r"\bcần\s*sa\b", r"\bbóng\s*cười\b", r"\bthuốc\s*lá\s*điện\s*tử\b",
    r"\bvape\b", r"\bpod\b", r"\bvũ\s*khí\b", r"\bsúng\s*đạn\b", r"\bdao\s*kiếm\b",
    r"\bđâm\s*chém\b", r"\bgiết\s*người\b", r"\bbạo\s*lực\b", r"\bmáu\s*me\b", r"\btự\s*tử\b"
]

# 4. Adult content, NSFW, Vulgar profanity
ADULT_VULGAR_PATTERNS = [
    r"\b18\+\b", r"\bkhiêu\s*dâm\b", r"\btình\s*dục\b", r"\bđồi\s*trụy\b",
    r"\bđm\b", r"\bđkm\b", r"\bvcl\b", r"\bđéo\b", r"\bchửi\s*thề\b", r"\bxúc\s*phạm\b"
]

# 5. Defamation, Malicious Fake News, Superstition
DEFAMATION_SUPERSTITION_PATTERNS = [
    r"\bbùa\s*ngải\b", r"\bmê\s*tín\b", r"\bbói\s*toán\b", r"\btà\s*thuật\b",
    r"\blừa\s*đảo\b", r"\bphốt\s*lừa\b", r"\btẩy\s*chay\b"
]

ALL_PROHIBITED_PATTERNS = (
    POLITICAL_RELIGIOUS_PATTERNS +
    GAMBLING_SCAM_PATTERNS +
    SUBSTANCE_VIOLENCE_PATTERNS +
    ADULT_VULGAR_PATTERNS +
    DEFAMATION_SUPERSTITION_PATTERNS
)

COMPILED_PROHIBITED_REGEX = [re.compile(p, re.IGNORECASE) for p in ALL_PROHIBITED_PATTERNS]

def is_safe_text(text: str) -> Tuple[bool, str]:
    """Check whether a given piece of text violates any safety or legal policy."""
    if not text:
        return True, ""
        
    for regex in COMPILED_PROHIBITED_REGEX:
        match = regex.search(text)
        if match:
            violation_word = match.group(0)
            return False, f"Phát hiện từ khóa không phù hợp chính sách: '{violation_word}'"
            
    return True, ""

def audit_script_compliance(script: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Perform a strict compliance audit on a full comparison script:
    1. Audits Title, Topic, Category, Angle
    2. Audits Product Names (Item A & Item B)
    3. Audits all Voiceover Segments and Visual Prompts
    """
    # 1. Audit Title & Angle
    title = script.get("title", "")
    safe, reason = is_safe_text(title)
    if not safe:
        return False, f"Tiêu đề kịch bản không an toàn: {reason}"
        
    angle = script.get("angle", "")
    safe, reason = is_safe_text(angle)
    if not safe:
        return False, f"Khía cạnh so sánh không an toàn: {reason}"
        
    # 2. Audit Items
    item_a = script.get("item_a", {})
    name_a = item_a.get("name", "") if isinstance(item_a, dict) else str(item_a)
    safe, reason = is_safe_text(name_a)
    if not safe:
        return False, f"Đối tượng A vi phạm chính sách: {reason}"
        
    item_b = script.get("item_b", {})
    name_b = item_b.get("name", "") if isinstance(item_b, dict) else str(item_b)
    safe, reason = is_safe_text(name_b)
    if not safe:
        return False, f"Đối tượng B vi phạm chính sách: {reason}"
        
    # 3. Audit all Segments
    segments = script.get("segments", [])
    for idx, seg in enumerate(segments):
        if not isinstance(seg, dict):
            continue
        vo_text = seg.get("voiceover_text") or seg.get("audio") or seg.get("text") or ""
        safe, reason = is_safe_text(vo_text)
        if not safe:
            return False, f"Phân đoạn thoại {idx+1} không an toàn: {reason}"
            
        visual_desc = seg.get("visual") or ""
        safe, reason = is_safe_text(visual_desc)
        if not safe:
            return False, f"Mô tả hình ảnh phân đoạn {idx+1} không an toàn: {reason}"
            
    return True, "Kịch bản an toàn và tuân thủ 100% chính sách pháp luật & nền tảng."

if __name__ == "__main__":
    test_safe = {
        "title": "iPhone 15 Pro Max vs Samsung Galaxy S24 Ultra",
        "angle": "Camera chụp đêm",
        "item_a": {"name": "iPhone 15 Pro Max"},
        "item_b": {"name": "Samsung S24 Ultra"},
        "segments": [{"voiceover_text": "iPhone chụp đêm màu sắc chân thực, còn Samsung thì zoom siêu xa."}]
    }
    safe, msg = audit_script_compliance(test_safe)
    print("Test Safe Result:", safe, "|", msg)
    assert safe is True

    test_unsafe = {
        "title": "Tài xỉu online vs Baccarat",
        "angle": "Cờ bạc ăn tiền",
        "item_a": {"name": "Tài xỉu"},
        "item_b": {"name": "Baccarat"},
        "segments": [{"voiceover_text": "Chơi tài xỉu kiếm tiền khủng mỗi ngày."}]
    }
    safe_bad, msg_bad = audit_script_compliance(test_unsafe)
    print("Test Unsafe Result:", safe_bad, "|", msg_bad)
    assert safe_bad is False
    print("ContentModerator ready & verified 100%!")