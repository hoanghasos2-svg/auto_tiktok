import re

# Dictionary of common tech and brand pronunciations for Vietnamese TTS
TECH_PRONUNCIATION_MAP = {
    r"\bvs\b": "so với",
    r"\bVS\b": "đối đầu với",
    r"\bv/s\b": "so với",
    r"\biPhone\b": "Ai-phôn",
    r"\biphone\b": "ai-phôn",
    r"\bIPHONE\b": "Ai-phôn",
    r"\bSamsung\b": "Sam-sung",
    r"\bsamsung\b": "sam-sung",
    r"\bGalaxy\b": "Ga-la-xy",
    r"\bUltra\b": "Un-tra",
    r"\bultra\b": "un-tra",
    r"\bPro Max\b": "Rô Mắc",
    r"\bpro max\b": "rô mắc",
    r"\bPro\b": "Rô",
    r"\bpro\b": "rô",
    r"\bPlus\b": "P-lớt",
    r"\bplus\b": "p-lớt",
    r"\bMacBook\b": "Mác-búc",
    r"\bmacbook\b": "mác-búc",
    r"\biPad\b": "Ai-pát",
    r"\bipad\b": "ai-pát",
    r"\bApple\b": "Áp-pồ",
    r"\bapple\b": "áp-pồ",
    r"\bXiaomi\b": "Mì-xào",
    r"\bOppo\b": "Ốp-pô",
    r"\bChatGPT\b": "Chát G-P-T",
    r"\bchatgpt\b": "chát g-p-t",
    r"\bClaude\b": "C-lốt",
    r"\bGemini\b": "Ge-mi-ni",
    r"\bAI\b": "A-I",
    r"\bCamera\b": "Ca-mê-ra",
    r"\bcamera\b": "ca-mê-ra",
    r"\bRAM\b": "Ram",
    r"\bROM\b": "Rom",
    r"\bGB\b": "Ghi-ga-bai",
    r"\bgb\b": "ghi-ga-bai",
    r"\bTB\b": "Tê-ra-bai",
    r"\btb\b": "tê-ra-bai",
    r"\bmAh\b": "mi-li-am-pe giờ",
    r"\bmah\b": "mi-li-am-pe giờ",
    r"\bHz\b": "Héc",
    r"\bhz\b": "héc",
    r"\bFPS\b": "khung hình trên giây",
    r"\bfps\b": "khung hình trên giây",
    r"\bOLED\b": "Ô-lét",
    r"\bAMOLED\b": "A-mô-lét",
    r"\bDynamic Island\b": "Đai-na-míc Ai-lần",
    r"\bChip\b": "Chíp",
    r"\bchip\b": "chíp",
    r"\bSnapdragon\b": "S-náp đ-ra-gân",
    r"\bBionic\b": "Bi-ô-ních",
    r"\bCTA\b": "kêu gọi",
    r"\bReview\b": "Đánh giá",
    r"\breview\b": "đánh giá",
    r"\b0\s*VNĐ\b": "không đồng",
    r"\b0đ\b": "không đồng",
    r"\b0k\b": "không đồng",
    r"\b4K\b": "Bốn K",
    r"\b8K\b": "Tám K",
    r"\b1080p\b": "Full Hát-Đê",
    r"\bTikTok\b": "Tích Tốc",
    r"\btiktok\b": "tích tốc",
    r"\bYouTube\b": "Du Túp",
    r"\byoutube\b": "du túp",
    r"\bShorts\b": "Sọt",
    r"\bReels\b": "Riu",
}

def normalize_text_for_speech(text: str) -> str:
    """Normalize Vietnamese text, tech brand names, acronyms, and specs for natural AI voiceover."""
    if not text:
        return ""
        
    res = text.strip()
    
    # 1. Replace tech and brand words
    for pattern, replacement in TECH_PRONUNCIATION_MAP.items():
        res = re.sub(pattern, replacement, res)
        
    # 2. Convert specific number patterns (e.g. 5000mAh already handled above)
    # Convert 'vs.' -> 'so với'
    res = re.sub(r"\bvs\.\b", "so với", res, flags=re.IGNORECASE)
    
    # 3. Clean up excessive punctuations while preserving breathing pauses
    res = re.sub(r"\s*([,?.!])\s*", r"\1 ", res)
    res = re.sub(r"\s+", " ", res).strip()
    
    return res

if __name__ == "__main__":
    test_str = "iPhone 15 Pro Max vs Samsung Galaxy S24 Ultra với pin 5000mAh, RAM 12GB và camera 4K!"
    print("Original:", test_str)
    print("Normalized:", normalize_text_for_speech(test_str))