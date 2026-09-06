import io
import os
import re
import urllib.parse
import urllib.request
import requests
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageDraw, ImageOps, ImageFilter, ImageFont

BASE_DIR = Path(__file__).resolve().parent

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def clean_query_variations(query: str, display_name: str = "") -> List[str]:
    variations = []
    
    # 1. Clean display name
    if display_name:
        clean_dn = re.sub(r"[\(\[].*?[\)\]]", "", display_name).strip()
        if clean_dn and clean_dn not in variations:
            variations.append(clean_dn)
            
    # 2. Clean query by stripping boilerplate keywords
    clean_q = re.sub(r"(?:high resolution|high quality|product photo|white background|portrait|full body|photo|4k|hd|wallpaper)", "", query, flags=re.IGNORECASE).strip()
    clean_q = re.sub(r"\s+", " ", clean_q)
    if clean_q and clean_q not in variations:
        variations.append(clean_q)
        
    # 3. Original query
    if query and query not in variations:
        variations.append(query)
        
    return variations

def process_and_crop_square(
    image_input,
    output_path: str,
    target_size=(480, 480),
    radius=28,
    border_color="#FFFFFF"
) -> str:
    if isinstance(image_input, (str, Path)):
        base_img = Image.open(image_input)
    else:
        base_img = Image.open(io.BytesIO(image_input))
        
    base_img = base_img.convert("RGBA")
    
    w, h = base_img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    cropped = base_img.crop((left, top, left + min_dim, top + min_dim))
    
    resized = cropped.resize(target_size, Image.Resampling.LANCZOS)
    
    mask = Image.new("L", target_size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, target_size[0], target_size[1]], radius=radius, fill=255)
    
    rounded = Image.new("RGBA", target_size, (0, 0, 0, 0))
    rounded.paste(resized, (0, 0), mask)
    
    draw = ImageDraw.Draw(rounded)
    draw.rounded_rectangle(
        [2, 2, target_size[0] - 2, target_size[1] - 2],
        radius=radius,
        outline=border_color,
        width=5
    )
    
    rounded.save(output_path, "PNG")
    return output_path

def search_wikimedia_image(query: str) -> Optional[bytes]:
    """Secondary image engine: Wikimedia Commons API."""
    try:
        url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrlimit=3&prop=imageinfo&iiprop=url|mime&format=json"
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for pid, page in pages.items():
                imageinfo = page.get("imageinfo", [])
                if imageinfo:
                    img_url = imageinfo[0].get("url")
                    mime = imageinfo[0].get("mime", "")
                    if img_url and ("jpeg" in mime or "png" in mime or "webp" in mime or "jpg" in mime):
                        img_resp = requests.get(img_url, headers=headers, timeout=6)
                        if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                            return img_resp.content
    except Exception:
        pass
    return None

def search_wikipedia_image(query: str) -> Optional[bytes]:
    """Secondary image engine: Wikipedia Direct PageImages API."""
    try:
        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(clean_q)}&prop=pageimages&format=json&pithumbsize=600"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                thumb = pdata.get("thumbnail", {}).get("source")
                if thumb:
                    img_resp = requests.get(thumb, headers=headers, timeout=8)
                    if img_resp.status_code == 200 and len(img_resp.content) > 3000:
                        return img_resp.content
    except Exception:
        pass
    return None

def generate_pollinations_image(query: str) -> Optional[bytes]:
    """Tertiary engine: Pollinations.ai High-Res Image (100% Free, No Key, Datacenter-friendly)."""
    try:
        clean_prompt = urllib.parse.quote(f"clean professional product photo of {query}, white clean studio background, 4k high quality")
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=480&height=480&nologo=true"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=18)
        if resp.status_code == 200 and len(resp.content) > 4000:
            return resp.content
    except Exception as ex:
        print(f"[ImageService] Pollinations AI error: {ex}")
    return None

def create_graphic_placeholder_card(display_name: str, output_path: str, border_color: str, target_size=(480, 480)):
    """Ultimate Fallback: Tạo thẻ đồ họa sản phẩm cao cấp nếu mọi nguồn mạng bị chặn."""
    card = Image.new("RGBA", target_size, (15, 23, 42, 255))
    draw = ImageDraw.Draw(card)
    
    # Nền gradient nhẹ
    for y in range(target_size[1]):
        factor = y / target_size[1]
        r = int(24 * (1 - factor) + 15 * factor)
        g = int(32 * (1 - factor) + 23 * factor)
        b = int(50 * (1 - factor) + 42 * factor)
        draw.line([(0, y), (target_size[0], y)], fill=(r, g, b))

    # Viền bo tròn sang trọng
    draw.rounded_rectangle([4, 4, target_size[0] - 4, target_size[1] - 4], radius=28, outline=border_color, width=6)

    # Chữ tên đối tượng
    font_path = BASE_DIR / "assets" / "fonts" / "BeVietnamPro-ExtraBold.ttf"
    try:
        font = ImageFont.truetype(str(font_path), 36) if font_path.exists() else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    words = display_name.split()
    lines, cur_l = [], []
    for w in words:
        cur_l.append(w)
        if len(" ".join(cur_l)) > 14:
            lines.append(" ".join(cur_l[:-1]))
            cur_l = [w]
    if cur_l:
        lines.append(" ".join(cur_l))
        
    y_text = 200
    for line in lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((target_size[0] - tw) // 2, y_text), line, font=font, fill="#F8FAFC")
        y_text += 50

    card.save(output_path, "PNG")
    return output_path

def search_and_download_image(
    query: str,
    output_path: str,
    item_label: str = "A",
    display_name: str = ""
) -> str:
    """Download real product/topic photo with resilient multi-tier fallback."""
    border_color = "#38BDF8" if item_label == "A" else "#FB7185"
    variations = clean_query_variations(query, display_name)
    target_label = display_name if display_name else query
    
    # Tier 1: DuckDuckGo Search (Tốt nhất cho IP cá nhân)
    if DDGS_AVAILABLE:
        for q_var in variations:
            try:
                print(f"[ImageService] [Tier 1 DDGS] Đang tìm ảnh cho: '{q_var}'...")
                with DDGS() as ddgs:
                    results = list(ddgs.images(
                        q_var,
                        region="wt-wt",
                        safesearch="moderate",
                        max_results=5
                    ))
                    
                for item in results:
                    image_url = item.get("image")
                    if not image_url:
                        continue
                    try:
                        headers = {"User-Agent": USER_AGENT}
                        resp = requests.get(image_url, headers=headers, timeout=6)
                        if resp.status_code == 200 and len(resp.content) > 4000:
                            process_and_crop_square(
                                resp.content,
                                output_path,
                                target_size=(480, 480),
                                border_color=border_color
                            )
                            print(f"[ImageService] Tải thành công ảnh DDGS cho '{q_var}': {output_path}")
                            return output_path
                    except Exception:
                        continue
            except Exception as search_err:
                print(f"[ImageService] DDGS không khả dụng ({search_err}). Chuyển sang engine dự phòng...")
                break
                
    # Tier 2: Wikipedia & Wikimedia Direct API (Không bao giờ chặn IP máy chủ Datacenter)
    print(f"[ImageService] [Tier 2 Wiki] Đang truy vấn hình ảnh bách khoa cho: '{target_label}'...")
    for q_var in variations:
        img_bytes = search_wikipedia_image(q_var) or search_wikimedia_image(q_var)
        if img_bytes:
            process_and_crop_square(
                img_bytes,
                output_path,
                target_size=(480, 480),
                border_color=border_color
            )
            print(f"[ImageService] Tải thành công qua Wiki Engine cho '{q_var}': {output_path}")
            return output_path

    # Tier 3: Pollinations AI Image Synthesis (100% Free, luôn có ảnh 480x480 siêu nét)
    print(f"[ImageService] [Tier 3 AI Studio] Đang tạo hình ảnh minh họa cho: '{target_label}'...")
    ai_img_bytes = generate_pollinations_image(target_label)
    if ai_img_bytes:
        process_and_crop_square(
            ai_img_bytes,
            output_path,
            target_size=(480, 480),
            border_color=border_color
        )
        print(f"[ImageService] Tạo ảnh AI thành công cho '{target_label}': {output_path}")
        return output_path

    # Tier 4: Fallback Graphic Card (Bảo đảm tiến trình 100% không bao giờ crash trên Cloud)
    print(f"[ImageService] [Tier 4 Card] Tạo thẻ đồ họa cao cấp cho: '{target_label}'")
    create_graphic_placeholder_card(target_label, output_path, border_color)
    return output_path

if __name__ == "__main__":
    print("Testing image_service...")