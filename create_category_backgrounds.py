import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
BG_DIR = BASE_DIR / "assets" / "backgrounds"
BG_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920

def create_gradient(top_color, bottom_color):
    base = Image.new("RGBA", (WIDTH, HEIGHT), top_color)
    top_r, top_g, top_b = top_color[:3]
    bot_r, bot_g, bot_b = bottom_color[:3]
    
    # Generate vertical gradient
    for y in range(HEIGHT):
        ratio = y / float(HEIGHT)
        r = int(top_r + (bot_r - top_r) * ratio)
        g = int(top_g + (bot_g - top_g) * ratio)
        b = int(top_b + (bot_b - top_b) * ratio)
        line = Image.new("RGBA", (WIDTH, 1), (r, g, b, 255))
        base.paste(line, (0, y))
    return base

def add_vignette(img, intensity=0.4):
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = WIDTH // 2, HEIGHT // 2
    max_radius = math.sqrt(cx**2 + cy**2)
    
    for r in range(int(max_radius * 0.4), int(max_radius), 8):
        alpha = int(255 * intensity * ((r - max_radius * 0.4) / (max_radius * 0.6)))
        alpha = min(255, max(0, alpha))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(0, 0, 0, alpha), width=8)
        
    blurred = overlay.filter(ImageFilter.GaussianBlur(30))
    return Image.alpha_composite(img, blurred)

# 1. Tech & Electronics (Cyber Navy & Blue Neon Grid)
def make_tech_bg():
    bg = create_gradient((10, 15, 30, 255), (15, 23, 42, 255))
    draw = ImageDraw.Draw(bg)
    # Draw subtle tech grid
    grid_color = (56, 189, 248, 20)
    for x in range(0, WIDTH, 60):
        draw.line([(x, 0), (x, HEIGHT)], fill=grid_color, width=1)
    for y in range(0, HEIGHT, 60):
        draw.line([(0, y), (WIDTH, y)], fill=grid_color, width=1)
    # Subtle glowing circles
    draw.ellipse([WIDTH//2 - 400, 200, WIDTH//2 + 400, 1000], fill=(14, 165, 233, 15))
    return add_vignette(bg, 0.45)

# 2. Food & Culinary (Warm Wooden Amber & Cozy Kitchen Glow)
def make_food_bg():
    bg = create_gradient((45, 20, 10, 255), (28, 15, 8, 255))
    draw = ImageDraw.Draw(bg)
    # Draw warm horizontal wood plank lines
    wood_color = (245, 158, 11, 15)
    for y in range(0, HEIGHT, 45):
        draw.line([(0, y), (WIDTH, y)], fill=wood_color, width=2)
    # Warm amber glow in center
    draw.ellipse([WIDTH//2 - 450, 300, WIDTH//2 + 450, 1200], fill=(245, 158, 11, 20))
    return add_vignette(bg, 0.4)

# 3. Vehicles & Transportation (Carbon Fiber Dark & Asphalt Speed)
def make_vehicles_bg():
    bg = create_gradient((15, 15, 18, 255), (24, 24, 27, 255))
    draw = ImageDraw.Draw(bg)
    # Carbon fiber diagonal pattern
    line_color = (239, 68, 68, 15)
    for i in range(-HEIGHT, WIDTH + HEIGHT, 35):
        draw.line([(i, 0), (i + HEIGHT, HEIGHT)], fill=line_color, width=1)
    # Red speed accent streak
    draw.ellipse([WIDTH//2 - 400, 150, WIDTH//2 + 400, 950], fill=(239, 68, 68, 15))
    return add_vignette(bg, 0.5)

# 4. AI & Software (Deep Digital Purple & Neural Nodes)
def make_ai_bg():
    bg = create_gradient((15, 10, 30, 255), (20, 15, 45, 255))
    draw = ImageDraw.Draw(bg)
    # Digital node connections
    node_color = (168, 85, 247, 25)
    for i in range(12):
        x1 = (i * 137) % WIDTH
        y1 = (i * 251) % HEIGHT
        x2 = ((i + 3) * 191) % WIDTH
        y2 = ((i + 3) * 313) % HEIGHT
        draw.line([(x1, y1), (x2, y2)], fill=node_color, width=2)
        draw.ellipse([x1 - 6, y1 - 6, x1 + 6, y1 + 6], fill=(192, 132, 252, 40))
    draw.ellipse([WIDTH//2 - 400, 200, WIDTH//2 + 400, 1000], fill=(147, 51, 234, 18))
    return add_vignette(bg, 0.45)

# 5. Finance & Life (Emerald Green & Golden Wealth Texture)
def make_finance_bg():
    bg = create_gradient((6, 35, 25, 255), (10, 25, 20, 255))
    draw = ImageDraw.Draw(bg)
    # Subtle gold geometric lines
    gold_color = (234, 179, 8, 18)
    for x in range(0, WIDTH, 80):
        draw.line([(x, 0), (x, HEIGHT)], fill=gold_color, width=1)
    draw.ellipse([WIDTH//2 - 450, 250, WIDTH//2 + 450, 1100], fill=(16, 185, 129, 20))
    return add_vignette(bg, 0.4)

# 6. Gaming & Entertainment (Synthwave Cyber Magenta & RGB Grid)
def make_gaming_bg():
    bg = create_gradient((20, 10, 35, 255), (10, 5, 25, 255))
    draw = ImageDraw.Draw(bg)
    # Synthwave perspective grid in bottom half
    grid_pink = (236, 72, 153, 25)
    for x in range(0, WIDTH, 50):
        draw.line([(x, 800), (x, HEIGHT)], fill=grid_pink, width=1)
    for y in range(800, HEIGHT, 40):
        draw.line([(0, y), (WIDTH, y)], fill=grid_pink, width=1)
    draw.ellipse([WIDTH//2 - 400, 200, WIDTH//2 + 400, 900], fill=(219, 39, 119, 20))
    return add_vignette(bg, 0.45)

# 7. Pets & Animals (Cozy Honey Pastel & Warm Aesthetic)
def make_pets_bg():
    bg = create_gradient((45, 30, 15, 255), (30, 20, 10, 255))
    draw = ImageDraw.Draw(bg)
    # Warm soft circles / bokeh
    paw_color = (251, 191, 36, 15)
    for i in range(15):
        cx = (i * 179) % (WIDTH - 100) + 50
        cy = (i * 283) % (HEIGHT - 100) + 50
        draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=paw_color)
    draw.ellipse([WIDTH//2 - 400, 300, WIDTH//2 + 400, 1100], fill=(245, 158, 11, 20))
    return add_vignette(bg, 0.4)

# 8. Default Universal
def make_default_bg():
    bg = create_gradient((15, 23, 42, 255), (2, 6, 23, 255))
    return add_vignette(bg, 0.4)

def generate_all_backgrounds():
    make_tech_bg().convert("RGB").save(BG_DIR / "bg_tech.png", quality=95)
    make_food_bg().convert("RGB").save(BG_DIR / "bg_food.png", quality=95)
    make_vehicles_bg().convert("RGB").save(BG_DIR / "bg_vehicles.png", quality=95)
    make_ai_bg().convert("RGB").save(BG_DIR / "bg_ai.png", quality=95)
    make_finance_bg().convert("RGB").save(BG_DIR / "bg_finance.png", quality=95)
    make_gaming_bg().convert("RGB").save(BG_DIR / "bg_gaming.png", quality=95)
    make_pets_bg().convert("RGB").save(BG_DIR / "bg_pets.png", quality=95)
    make_default_bg().convert("RGB").save(BG_DIR / "bg_default.png", quality=95)
    make_default_bg().convert("RGB").save(BG_DIR / "paper_bg.png", quality=95)
    print("Successfully generated all 8 category backgrounds in assets/backgrounds/!")

if __name__ == "__main__":
    generate_all_backgrounds()