import io
import os
import re
import urllib.parse
import urllib.request
import requests
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageDraw, ImageOps, ImageFilter, ImageFont

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

def search_and_download_image(
    query: str,
    output_path: str,
    item_label: str = "A",
    display_name: str = ""
) -> str:
    """Download real product/topic photo with multi-engine fail-fast mechanism."""
    border_color = "#38BDF8" if item_label == "A" else "#FB7185"
    variations = clean_query_variations(query, display_name)
    
    # 1. Primary Engine: DuckDuckGo Search (DDGS)
    if DDGS_AVAILABLE:
        for q_var in variations:
            try:
                print(f"[ImageService] Đang tìm ảnh DDGS cho: '{q_var}'...")
                with DDGS() as ddgs:
                    results = list(ddgs.images(
                        q_var,
                        region="wt-wt",
                        safesearch="moderate",
                        max_results=6
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
                            print(f"[ImageService] Tải thành công ảnh thật cho '{q_var}': {output_path}")
                            return output_path
                    except Exception:
                        continue
            except Exception as search_err:
                print(f"[ImageService] DDGS search error on '{q_var}': {search_err}")
                
    # 2. Secondary Engine: Wikimedia Commons API
    for q_var in variations:
        img_bytes = search_wikimedia_image(q_var)
        if img_bytes:
            process_and_crop_square(
                img_bytes,
                output_path,
                target_size=(480, 480),
                border_color=border_color
            )
            print(f"[ImageService] Tải thành công qua Wikimedia: {output_path}")
            return output_path
            
    # Fail-Fast: Never silently draw a dummy text card!
    target_label = display_name if display_name else query
    raise RuntimeError(f"Không thể tìm hoặc tải ảnh thực tế cho '{target_label}'. Vui lòng kiểm tra lại kết nối internet.")

if __name__ == "__main__":
    print("Testing image_service...")