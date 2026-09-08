import io
import os
import re
import sys
import urllib.parse
import urllib.request
import requests
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageDraw, ImageOps, ImageFilter, ImageFont, ImageStat

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

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

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def clean_query_variations(query: str, display_name: str = "", query_en: str = "") -> List[str]:
    variations = []
    
    # 1. English query (Best for international APIs like Wikimedia, Pollinations, DDGS)
    if query_en:
        clean_en = re.sub(r"[^\w\s\-,]", " ", query_en).strip()
        clean_en = re.sub(r"\s+", " ", clean_en)
        if clean_en and clean_en not in variations:
            variations.append(clean_en)
        # Broaden English query: if it has 3+ words, also add the core 2 words
        words = clean_en.split()
        if len(words) >= 3:
            simplified = " ".join(words[:2])
            if simplified not in variations:
                variations.append(simplified)
            
    # 2. Clean display name
    if display_name:
        clean_dn = re.sub(r"[\(\[].*?[\)\]]", "", display_name).strip()
        if clean_dn and clean_dn not in variations:
            variations.append(clean_dn)
            
    # 3. Clean Vietnamese query by stripping boilerplate keywords
    clean_q = re.sub(r"(?:high resolution|high quality|product photo|white background|portrait|full body|photo|4k|hd|wallpaper)", "", query, flags=re.IGNORECASE).strip()
    clean_q = re.sub(r"\s+", " ", clean_q)
    if clean_q and clean_q not in variations:
        variations.append(clean_q)
        
    # 4. Original query
    if query and query not in variations:
        variations.append(query)
        
    return variations

def is_valid_image(img: Image.Image) -> bool:
    """Check if image is not corrupted, blank, or monochromatic placeholder."""
    try:
        w, h = img.size
        if w < 80 or h < 80:
            return False
        stat = ImageStat.Stat(img.convert("RGB"))
        # Check standard deviation: lowered to 3.0 to allow dark/monochromatic real photos (coffee, night sky, sleek electronics)
        avg_stddev = sum(stat.stddev) / len(stat.stddev)
        if avg_stddev < 3.0:
            return False
        return True
    except Exception:
        return False

def process_and_crop_square(
    image_input,
    output_path: str,
    target_size=(480, 480),
    radius=28,
    border_color="#FFFFFF"
) -> bool:
    """Crops and styles square image. Returns True if valid image was saved."""
    try:
        if isinstance(image_input, (str, Path)):
            base_img = Image.open(image_input)
        else:
            base_img = Image.open(io.BytesIO(image_input))
            
        base_img = base_img.convert("RGBA")
        if not is_valid_image(base_img):
            return False
            
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
        return True
    except Exception as e:
        print(f"[ImageService] Crop error: {e}")
        return False

def search_wikimedia_image(query: str) -> Optional[bytes]:
    """Secondary image engine: Wikimedia Commons API with namespace 6 (Files only)."""
    try:
        clean_q = re.sub(r"[^\w\s]", " ", query).strip()
        url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(clean_q)}&gsrnamespace=6&gsrlimit=5&prop=imageinfo&iiprop=url|mime|size&format=json"
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for pid, page in pages.items():
                imageinfo = page.get("imageinfo", [])
                if imageinfo:
                    info = imageinfo[0]
                    img_url = info.get("url")
                    mime = info.get("mime", "")
                    size = info.get("size", 0)
                    if img_url and ("jpeg" in mime or "png" in mime or "webp" in mime or "jpg" in mime) and size > 8000:
                        img_resp = requests.get(img_url, headers=headers, timeout=8)
                        if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                            return img_resp.content
    except Exception:
        pass
    return None

def search_wikipedia_image(query: str) -> Optional[bytes]:
    """Secondary image engine: Wikipedia Direct PageImages API (both en & vi) with redirect resolution."""
    for lang in ["en", "vi"]:
        try:
            clean_q = re.sub(r"[^\w\s]", " ", query).strip()
            # 1. PageImages with redirects
            url = f"https://{lang}.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(clean_q)}&gsrlimit=3&redirects=1&prop=pageimages&pithumbsize=600&format=json"
            headers = {"User-Agent": USER_AGENT}
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    thumb = pdata.get("thumbnail", {}).get("source")
                    if thumb:
                        img_resp = requests.get(thumb, headers=headers, timeout=8)
                        if img_resp.status_code == 200 and len(img_resp.content) > 4000:
                            return img_resp.content
        except Exception:
            pass
    return None

def search_openverse_image(query: str) -> Optional[bytes]:
    """Openverse API (Over 700 million verified Creative Commons photos)."""
    try:
        clean_q = re.sub(r"[^\w\s]", " ", query).strip()
        url = f"https://api.openverse.org/v1/images/?q={urllib.parse.quote(clean_q)}&page_size=4"
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            for item in results:
                raw_url = item.get("url")
                if raw_url and any(ext in raw_url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    img_resp = requests.get(raw_url, headers=headers, timeout=8)
                    if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                        return img_resp.content
    except Exception:
        pass
    return None

def generate_pollinations_image(query: str, query_en: str = "") -> Optional[bytes]:
    """Tertiary engine: Pollinations.ai High-Res Image (100% Free, No Key, Datacenter-friendly)."""
    target = query_en if query_en else query
    prompts_to_try = [
        f"hyperrealistic studio photo of {target}, vibrant lighting, 8k resolution, photorealistic",
        f"high quality clear photo of {target}, centered, realistic colors",
        f"{target}, professional product photography"
    ]
    for prompt_text in prompts_to_try:
        try:
            clean_prompt = urllib.parse.quote(prompt_text)
            url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=480&height=480&nologo=true&seed={abs(hash(prompt_text)) % 99999}"
            headers = {"User-Agent": USER_AGENT}
            resp = requests.get(url, headers=headers, timeout=22)
            if resp.status_code == 200 and len(resp.content) > 5000:
                return resp.content
        except Exception as ex:
            print(f"[ImageService] Pollinations AI attempt error: {ex}")
    return None

def get_category_icon(display_name: str) -> str:
    """Tự động chọn biểu tượng 3D phù hợp với chủ đề."""
    name_lower = display_name.lower()
    if any(k in name_lower for k in ["tiền", "giàu", "vàng", "đồ hiệu", "chi tiêu", "tiết kiệm", "giá"]):
        return "💰"
    if any(k in name_lower for k in ["rẻ", "đồ rẻ", "mua sắm", "thay liên tục"]):
        return "🏷️"
    if any(k in name_lower for k in ["cơm", "phở", "bún", "ăn", "lẩu", "món", "thịt", "trà"]):
        return "🍲"
    if any(k in name_lower for k in ["thợ", "lương", "lao động", "nghề"]):
        return "🔨"
    if any(k in name_lower for k in ["nô lệ", "ép buộc", "xiềng"]):
        return "⛓️"
    if any(k in name_lower for k in ["kim tự tháp", "ai cập", "lịch sử", "cổ đại"]):
        return "🏛️"
    if any(k in name_lower for k in ["nắng", "nóng", "sa mạc", "ngày"]):
        return "☀️"
    if any(k in name_lower for k in ["đêm", "lạnh", "sao", "băng"]):
        return "🌙"
    if any(k in name_lower for k in ["chó", "mèo", "thú cưng"]):
        return "🐾"
    if any(k in name_lower for k in ["điện thoại", "iphone", "samsung", "ai", "máy tính"]):
        return "📱"
    return "⚖️"

def create_graphic_placeholder_card(display_name: str, output_path: str, border_color: str, target_size=(480, 480)):
    """Ultimate Fallback: Tạo thẻ đồ họa sản phẩm cao cấp nếu mọi nguồn mạng bị chặn."""
    card = Image.new("RGBA", target_size, (15, 23, 42, 255))
    draw = ImageDraw.Draw(card)
    
    # Nền gradient sang trọng sâu lắng
    for y in range(target_size[1]):
        factor = y / target_size[1]
        r = int(28 * (1 - factor) + 12 * factor)
        g = int(38 * (1 - factor) + 18 * factor)
        b = int(60 * (1 - factor) + 32 * factor)
        draw.line([(0, y), (target_size[0], y)], fill=(r, g, b))

    # Viền bo tròn kép tạo chiều sâu
    draw.rounded_rectangle([4, 4, target_size[0] - 4, target_size[1] - 4], radius=28, outline=border_color, width=6)
    draw.rounded_rectangle([12, 12, target_size[0] - 12, target_size[1] - 12], radius=22, outline="#334155", width=2)

    # Biểu tượng chủ đề ở vị trí trên
    icon = get_category_icon(display_name)
    font_path = BASE_DIR / "assets" / "fonts" / "BeVietnamPro-ExtraBold.ttf"
    try:
        font_text = ImageFont.truetype(str(font_path), 36) if font_path.exists() else ImageFont.load_default()
        font_icon = ImageFont.truetype(str(font_path), 72) if font_path.exists() else ImageFont.load_default()
    except Exception:
        font_text = ImageFont.load_default()
        font_icon = ImageFont.load_default()

    # Vẽ Icon
    draw.text((target_size[0] // 2, 110), icon, font=font_icon, anchor="mm")

    # Vẽ Tên đối tượng căn giữa hoàn hảo
    words = display_name.split()
    lines, cur_l = [], []
    for w in words:
        cur_l.append(w)
        if len(" ".join(cur_l)) > 11:
            lines.append(" ".join(cur_l[:-1]))
            cur_l = [w]
    if cur_l:
        lines.append(" ".join(cur_l))
        
    line_height = 56
    total_text_h = len(lines[:3]) * line_height
    y_text = (target_size[1] - total_text_h) // 2

    # Huy hiệu nhỏ ở trên
    badge_label = "CHỦ ĐỀ ĐỐI ĐẦU"
    try:
        font_badge = ImageFont.truetype(str(font_path), 20) if font_path.exists() else ImageFont.load_default()
    except Exception:
        font_badge = ImageFont.load_default()
    draw.rounded_rectangle([target_size[0] // 2 - 110, y_text - 65, target_size[0] // 2 + 110, y_text - 25], radius=10, fill="#1E293B", outline=border_color, width=2)
    draw.text((target_size[0] // 2, y_text - 45), badge_label, font=font_badge, fill=border_color, anchor="mm")

    for line in lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font_text)
        tw = bbox[2] - bbox[0]
        # Text shadow
        draw.text(((target_size[0] - tw) // 2 + 3, y_text + 3), line, font=font_text, fill="#020617")
        # Text main
        draw.text(((target_size[0] - tw) // 2, y_text), line, font=font_text, fill="#FFFFFF")
        y_text += line_height

    card.save(output_path, "PNG")
    return output_path

def search_unsplash_image(query: str) -> Optional[bytes]:
    """High-speed Stock CDN fallback: Unsplash Public Source (free, instant, high aesthetic)."""
    try:
        clean_q = re.sub(r"[^\w\s]", " ", query).strip()
        encoded = urllib.parse.quote(clean_q)
        url = f"https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=480&h=480&fit=crop" # Default fallback
        # Search unsplash direct page
        search_url = f"https://unsplash.com/napi/search/photos?query={encoded}&per_page=3&page=1"
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(search_url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            for r in results:
                raw_url = r.get("urls", {}).get("small") or r.get("urls", {}).get("regular")
                if raw_url:
                    img_resp = requests.get(raw_url, headers=headers, timeout=8)
                    if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                        return img_resp.content
    except Exception:
        pass
    return None

def search_pexels_image(query: str, api_key: str) -> Optional[bytes]:
    """
    Ưu tiên số 1: Pexels Official API (Kho ảnh bản quyền miễn phí 100%, chất lượng studio cao cấp).
    Endpoint: https://api.pexels.com/v1/search
    """
    if not api_key:
        return None
    try:
        clean_q = re.sub(r"[^\w\s\-]", " ", query).strip()
        if not clean_q:
            return None
        
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(clean_q)}&per_page=5"
        headers = {
            "Authorization": api_key,
            "User-Agent": USER_AGENT
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            photos = data.get("photos", [])
            for photo in photos:
                srcs = photo.get("src", {})
                # Chọn độ phân giải lớn, sắc nét nhất để crop vuông 480x480
                img_url = srcs.get("large") or srcs.get("large2x") or srcs.get("medium") or srcs.get("original")
                if img_url:
                    img_resp = requests.get(img_url, headers=headers, timeout=12)
                    if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                        return img_resp.content
        elif resp.status_code == 401:
            print("[ImageService] [Pexels API] Lỗi 401: API Key không hợp lệ hoặc đã hết hạn.")
        elif resp.status_code == 429:
            print("[ImageService] [Pexels API] Lỗi 429: Vượt quá giới hạn lượt gọi Pexels API (Rate limit).")
    except Exception as ex:
        print(f"[ImageService] [Pexels API Lỗi]: {ex}")
    return None

def search_and_download_image(
    query: str,
    output_path: str,
    item_label: str = "A",
    display_name: str = "",
    query_en: str = "",
    pexels_api_key: str = ""
) -> str:
    """Download real product/topic photo with Pexels API priority + resilient multi-tier fallback."""
    border_color = "#38BDF8" if item_label == "A" else "#FB7185"
    variations = clean_query_variations(query, display_name, query_en)
    target_label = display_name if display_name else query
    
    # 0. Xác định Pexels API Key
    if not pexels_api_key:
        pexels_api_key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not pexels_api_key:
        try:
            import config_manager
            pexels_api_key = config_manager.load_config().get("pexels_api_key", "").strip()
        except Exception:
            pass

    # Tier 0 (ƯU TIÊN SỐ 1 TUYỆT ĐỐI): Pexels Official API
    if pexels_api_key:
        print(f"[ImageService] [Tier 1 Pexels API] Đang tìm ảnh chuẩn xác trên Pexels cho: '{target_label}'...")
        for q_var in variations:
            pexels_bytes = search_pexels_image(q_var, pexels_api_key)
            if pexels_bytes:
                if process_and_crop_square(
                    pexels_bytes,
                    output_path,
                    target_size=(480, 480),
                    border_color=border_color
                ):
                    print(f"[ImageService] ✅ Tìm thấy ảnh Pexels chuẩn xác cho '{q_var}': {output_path}")
                    return output_path
        print(f"[ImageService] Pexels không tìm thấy ảnh phù hợp cho '{target_label}'. Chuyển sang engine dự phòng...")
    else:
        print(f"[ImageService] (Chưa cấu hình PEXELS_API_KEY. Dùng các nguồn tìm kiếm mở dự phòng)")

    # Tier 1: DuckDuckGo Search
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
                        if resp.status_code == 200 and len(resp.content) > 5000:
                            if process_and_crop_square(
                                resp.content,
                                output_path,
                                target_size=(480, 480),
                                border_color=border_color
                            ):
                                print(f"[ImageService] Tải thành công ảnh DDGS cho '{q_var}': {output_path}")
                                return output_path
                    except Exception:
                        continue
            except Exception as search_err:
                print(f"[ImageService] DDGS không khả dụng ({search_err}). Chuyển sang engine dự phòng...")
                break
                
    # Tier 2: Wikipedia & Wikimedia Commons Direct API (Thư viện bách khoa không chặn Cloud IP)
    print(f"[ImageService] [Tier 2 Wiki] Đang truy vấn ảnh bách khoa cho: '{target_label}'...")
    for q_var in variations:
        img_bytes = search_wikipedia_image(q_var) or search_wikimedia_image(q_var)
        if img_bytes:
            if process_and_crop_square(
                img_bytes,
                output_path,
                target_size=(480, 480),
                border_color=border_color
            ):
                print(f"[ImageService] Tải thành công qua Wiki Engine cho '{q_var}': {output_path}")
                return output_path

    # Tier 3: Openverse Global API (Kho hơn 700 triệu ảnh chụp thật có cấp phép Creative Commons)
    print(f"[ImageService] [Tier 3 Openverse] Đang tìm ảnh kho mở toàn cầu cho: '{target_label}'...")
    for q_var in variations:
        ov_bytes = search_openverse_image(q_var)
        if ov_bytes:
            if process_and_crop_square(
                ov_bytes,
                output_path,
                target_size=(480, 480),
                border_color=border_color
            ):
                print(f"[ImageService] Tải thành công qua Openverse cho '{q_var}': {output_path}")
                return output_path

    # Tier 4: Pollinations AI Image Synthesis (Tạo ảnh siêu nét, hỗ trợ chủ đề hiếm)
    print(f"[ImageService] [Tier 4 AI Studio] Đang tạo hình ảnh minh họa cho: '{target_label}'...")
    ai_img_bytes = generate_pollinations_image(target_label, query_en=query_en)
    if ai_img_bytes:
        if process_and_crop_square(
            ai_img_bytes,
            output_path,
            target_size=(480, 480),
            border_color=border_color
        ):
            print(f"[ImageService] Tạo ảnh AI thành công cho '{target_label}': {output_path}")
            return output_path

    # Tier 5: Fallback Graphic Card (Bảo đảm tiến trình 100% không bao giờ crash)
    print(f"[ImageService] [Tier 5 Card] Tạo thẻ đồ họa cao cấp cho: '{target_label}'")
    create_graphic_placeholder_card(target_label, output_path, border_color)
    return output_path

if __name__ == "__main__":
    print("Testing image_service...")