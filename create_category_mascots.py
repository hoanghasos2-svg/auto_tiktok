import math
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
MASCOTS_ROOT = BASE_DIR / "assets" / "mascots"
MASCOTS_ROOT.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 600, 700

def draw_base_shadow(draw, cx):
    draw.ellipse([cx - 160, HEIGHT - 80, cx + 160, HEIGHT - 30], fill=(0, 0, 0, 45))

# ----------------- 1. TECH ROBOT -----------------
def draw_tech_mascot(pose: str, filepath: Path):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 50
    draw_base_shadow(draw, cx)
    
    # Body
    draw.rounded_rectangle([cx - 140, cy - 120, cx + 140, cy + 210], radius=90, fill="#2563EB", outline="#1D4ED8", width=6)
    draw.ellipse([cx - 85, cy + 10, cx + 85, cy + 160], fill="#60A5FA")
    # Head / Monitor
    draw.rounded_rectangle([cx - 160, cy - 240, cx + 160, cy - 40], radius=60, fill="#0F172A", outline="#1E293B", width=8)
    draw.rounded_rectangle([cx - 140, cy - 220, cx + 140, cy - 60], radius=45, fill="#020617")
    # Antenna
    draw.line([(cx, cy - 240), (cx, cy - 290)], fill="#3B82F6", width=8)
    draw.ellipse([cx - 18, cy - 320, cx + 18, cy - 284], fill="#00F2FE", outline="#38BDF8", width=4)
    # Eyes & Mouth based on pose
    if pose == "pointing":
        draw.ellipse([cx - 85, cy - 165, cx - 45, cy - 115], fill="#00F2FE")
        draw.ellipse([cx + 45, cy - 165, cx + 85, cy - 115], fill="#00F2FE")
        draw.arc([cx - 30, cy - 115, cx + 30, cy - 80], start=10, end=170, fill="#00F2FE", width=5)
        # Laser Pointer Hand
        draw.line([(cx + 110, cy + 30), (cx + 210, cy - 110)], fill="#2563EB", width=28)
        draw.line([(cx + 210, cy - 110), (cx + 250, cy - 240)], fill="#E2E8F0", width=8)
        draw.polygon([(cx + 250, cy - 260), (cx + 238, cy - 238), (cx + 262, cy - 238)], fill="#EF4444")
        draw.arc([cx - 190, cy - 10, cx - 100, cy + 80], start=90, end=270, fill="#2563EB", width=26)
    elif pose == "thinking":
        draw.ellipse([cx - 80, cy - 170, cx - 45, cy - 125], fill="#00F2FE")
        draw.arc([cx + 45, cy - 155, cx + 85, cy - 125], start=190, end=350, fill="#00F2FE", width=5)
        draw.ellipse([cx - 12, cy - 100, cx + 12, cy - 80], fill="#00F2FE")
        # Hand on chin
        draw.arc([cx + 50, cy - 30, cx + 160, cy + 70], start=200, end=350, fill="#2563EB", width=26)
        draw.ellipse([cx + 35, cy - 70, cx + 80, cy - 30], fill="#60A5FA")
        draw.arc([cx - 180, cy + 20, cx - 100, cy + 110], start=100, end=260, fill="#2563EB", width=24)
    elif pose == "chill":
        draw.arc([cx - 85, cy - 155, cx - 40, cy - 115], start=200, end=340, fill="#00F2FE", width=6)
        draw.arc([cx + 40, cy - 155, cx + 85, cy - 115], start=200, end=340, fill="#00F2FE", width=6)
        draw.chord([cx - 35, cy - 115, cx + 35, cy - 65], start=0, end=180, fill="#EF4444", outline="#FFFFFF", width=3)
        draw.arc([cx + 80, cy - 15, cx + 170, cy + 85], start=220, end=360, fill="#2563EB", width=26)
        draw.arc([cx - 180, cy - 40, cx - 100, cy + 50], start=120, end=270, fill="#2563EB", width=24)
    else: # cta
        draw.ellipse([cx - 85, cy - 165, cx - 40, cy - 100], fill="#00F2FE")
        draw.ellipse([cx + 40, cy - 165, cx + 85, cy - 100], fill="#00F2FE")
        draw.chord([cx - 45, cy - 115, cx + 45, cy - 55], start=0, end=180, fill="#F59E0B", outline="#FFFFFF", width=4)
        draw.arc([cx - 190, cy - 50, cx - 100, cy + 40], start=90, end=270, fill="#2563EB", width=28)
        draw.arc([cx + 100, cy - 50, cx + 190, cy + 40], start=270, end=90, fill="#2563EB", width=28)
    img.save(filepath, "PNG")

# ----------------- 2. FOOD CHEF CAT -----------------
def draw_food_mascot(pose: str, filepath: Path):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 50
    draw_base_shadow(draw, cx)
    
    # Body (Cute Orange Tabby)
    draw.rounded_rectangle([cx - 135, cy - 100, cx + 135, cy + 220], radius=85, fill="#EA580C", outline="#C2410C", width=6)
    draw.ellipse([cx - 80, cy + 20, cx + 80, cy + 170], fill="#FED7AA") # Cream belly
    # Cat Ears
    draw.polygon([(cx - 140, cy - 170), (cx - 70, cy - 240), (cx - 20, cy - 170)], fill="#EA580C", outline="#C2410C")
    draw.polygon([(cx - 120, cy - 170), (cx - 70, cy - 220), (cx - 40, cy - 170)], fill="#FECDD3")
    draw.polygon([(cx + 20, cy - 170), (cx + 70, cy - 240), (cx + 140, cy - 170)], fill="#EA580C", outline="#C2410C")
    draw.polygon([(cx + 40, cy - 170), (cx + 70, cy - 220), (cx + 120, cy - 170)], fill="#FECDD3")
    # Head
    draw.ellipse([cx - 150, cy - 200, cx + 150, cy - 20], fill="#FB923C", outline="#EA580C", width=6)
    # Chef Hat (Toque)
    draw.ellipse([cx - 110, cy - 320, cx + 110, cy - 200], fill="#FFFFFF", outline="#E2E8F0", width=4)
    draw.rectangle([cx - 85, cy - 230, cx + 85, cy - 190], fill="#FFFFFF", outline="#CBD5E1", width=4)
    # Red Neckerchief
    draw.polygon([(cx - 50, cy - 30), (cx + 50, cy - 30), (cx, cy + 35)], fill="#DC2626")
    # Cat Whiskers & Nose
    draw.polygon([(cx - 12, cy - 100), (cx + 12, cy - 100), (cx, cy - 88)], fill="#BE123C")
    draw.line([(cx - 50, cy - 90), (cx - 110, cy - 100)], fill="#7C2D12", width=3)
    draw.line([(cx - 50, cy - 80), (cx - 110, cy - 80)], fill="#7C2D12", width=3)
    draw.line([(cx + 50, cy - 90), (cx + 110, cy - 100)], fill="#7C2D12", width=3)
    draw.line([(cx + 50, cy - 80), (cx + 110, cy - 80)], fill="#7C2D12", width=3)
    
    if pose == "pointing":
        draw.ellipse([cx - 75, cy - 145, cx - 40, cy - 105], fill="#1E293B")
        draw.ellipse([cx + 40, cy - 145, cx + 75, cy - 105], fill="#1E293B")
        draw.arc([cx - 25, cy - 88, cx + 25, cy - 65], start=0, end=180, fill="#BE123C", width=4)
        # Wooden Spoon Pointer
        draw.line([(cx + 100, cy + 40), (cx + 200, cy - 100)], fill="#FB923C", width=26)
        draw.line([(cx + 200, cy - 100), (cx + 240, cy - 210)], fill="#D97706", width=10)
        draw.ellipse([cx + 225, cy - 245, cx + 255, cy - 205], fill="#D97706")
    elif pose == "thinking":
        draw.arc([cx - 75, cy - 140, cx - 40, cy - 110], start=200, end=340, fill="#1E293B", width=5)
        draw.ellipse([cx + 40, cy - 145, cx + 75, cy - 105], fill="#1E293B")
        draw.ellipse([cx - 10, cy - 75, cx + 10, cy - 60], fill="#BE123C")
        draw.arc([cx + 50, cy - 20, cx + 150, cy + 70], start=200, end=350, fill="#FB923C", width=24)
    elif pose == "chill":
        draw.arc([cx - 75, cy - 140, cx - 40, cy - 110], start=200, end=340, fill="#1E293B", width=5)
        draw.arc([cx + 40, cy - 140, cx + 75, cy - 110], start=200, end=340, fill="#1E293B", width=5)
        draw.chord([cx - 30, cy - 80, cx + 30, cy - 45], start=0, end=180, fill="#DC2626", outline="#FFFFFF", width=2)
    else: # cta
        draw.ellipse([cx - 75, cy - 150, cx - 35, cy - 100], fill="#1E293B")
        draw.ellipse([cx + 35, cy - 150, cx + 75, cy - 100], fill="#1E293B")
        draw.chord([cx - 35, cy - 85, cx + 35, cy - 45], start=0, end=180, fill="#F59E0B", outline="#FFFFFF", width=3)
        draw.arc([cx - 180, cy - 40, cx - 100, cy + 40], start=90, end=270, fill="#FB923C", width=26)
        draw.arc([cx + 100, cy - 40, cx + 180, cy + 40], start=270, end=90, fill="#FB923C", width=26)
    img.save(filepath, "PNG")

# ----------------- 3. VEHICLES RACER FOX -----------------
def draw_vehicles_mascot(pose: str, filepath: Path):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 50
    draw_base_shadow(draw, cx)
    
    # Body (Leather Racing Jacket)
    draw.rounded_rectangle([cx - 135, cy - 110, cx + 135, cy + 220], radius=80, fill="#1E293B", outline="#0F172A", width=6)
    draw.line([(cx, cy - 110), (cx, cy + 210)], fill="#EF4444", width=8) # Racing stripe
    # Fox Ears
    draw.polygon([(cx - 145, cy - 160), (cx - 85, cy - 250), (cx - 25, cy - 160)], fill="#F97316", outline="#EA580C")
    draw.polygon([(cx + 25, cy - 160), (cx + 85, cy - 250), (cx + 145, cy - 160)], fill="#F97316", outline="#EA580C")
    # Fox Head
    draw.polygon([(cx - 150, cy - 170), (cx + 150, cy - 170), (cx, cy - 20)], fill="#FB923C", outline="#EA580C")
    draw.polygon([(cx - 80, cy - 70), (cx + 80, cy - 70), (cx, cy - 20)], fill="#FFFFFF")
    # Aviator Goggles
    draw.rounded_rectangle([cx - 120, cy - 210, cx - 20, cy - 160], radius=20, fill="#F59E0B", outline="#1E293B", width=6)
    draw.rounded_rectangle([cx + 20, cy - 210, cx + 120, cy - 160], radius=20, fill="#F59E0B", outline="#1E293B", width=6)
    draw.line([(cx - 20, cy - 185), (cx + 20, cy - 185)], fill="#1E293B", width=6)
    # Nose
    draw.ellipse([cx - 12, cy - 35, cx + 12, cy - 18], fill="#1E293B")
    
    if pose == "pointing":
        draw.ellipse([cx - 75, cy - 140, cx - 40, cy - 100], fill="#1E293B")
        draw.ellipse([cx + 40, cy - 140, cx + 75, cy - 100], fill="#1E293B")
        draw.line([(cx + 100, cy + 30), (cx + 210, cy - 100)], fill="#FB923C", width=26)
        draw.polygon([(cx + 220, cy - 110), (cx + 250, cy - 100), (cx + 220, cy - 90)], fill="#EF4444")
    elif pose == "thinking":
        draw.arc([cx - 75, cy - 135, cx - 40, cy - 105], start=200, end=340, fill="#1E293B", width=5)
        draw.ellipse([cx + 40, cy - 140, cx + 75, cy - 100], fill="#1E293B")
    elif pose == "chill":
        draw.arc([cx - 75, cy - 135, cx - 40, cy - 105], start=200, end=340, fill="#1E293B", width=5)
        draw.arc([cx + 40, cy - 135, cx + 75, cy - 105], start=200, end=340, fill="#1E293B", width=5)
    else: # cta
        draw.ellipse([cx - 75, cy - 145, cx - 35, cy - 95], fill="#1E293B")
        draw.ellipse([cx + 35, cy - 145, cx + 75, cy - 95], fill="#1E293B")
        draw.arc([cx - 180, cy - 40, cx - 100, cy + 40], start=90, end=270, fill="#FB923C", width=26)
        draw.arc([cx + 100, cy - 40, cx + 180, cy + 40], start=270, end=90, fill="#FB923C", width=26)
    img.save(filepath, "PNG")

# ----------------- 4. AI ANDROID HOLOGRAM -----------------
def draw_ai_mascot(pose: str, filepath: Path):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 50
    draw_base_shadow(draw, cx)
    
    # Body (Cyber Purple Android)
    draw.rounded_rectangle([cx - 135, cy - 120, cx + 135, cy + 210], radius=85, fill="#581C87", outline="#7E22CE", width=6)
    draw.ellipse([cx - 80, cy + 10, cx + 80, cy + 160], fill="#A855F7")
    # Head Visor
    draw.rounded_rectangle([cx - 150, cy - 240, cx + 150, cy - 40], radius=65, fill="#1E1B4B", outline="#6B21A8", width=8)
    draw.rounded_rectangle([cx - 135, cy - 220, cx + 135, cy - 60], radius=45, fill="#0F172A")
    # Neon Magenta HUD line
    draw.line([(cx - 120, cy - 140), (cx + 120, cy - 140)], fill="#EC4899", width=6)
    draw.ellipse([cx - 75, cy - 165, cx - 40, cy - 115], fill="#F43F5E")
    draw.ellipse([cx + 40, cy - 165, cx + 75, cy - 115], fill="#F43F5E")
    
    if pose == "pointing":
        draw.line([(cx + 110, cy + 30), (cx + 210, cy - 110)], fill="#7E22CE", width=26)
        draw.ellipse([cx + 205, cy - 130, cx + 240, cy - 95], fill="#EC4899")
    elif pose == "thinking":
        draw.arc([cx + 50, cy - 30, cx + 160, cy + 70], start=200, end=350, fill="#7E22CE", width=26)
    elif pose == "chill":
        draw.arc([cx + 80, cy - 15, cx + 170, cy + 85], start=220, end=360, fill="#7E22CE", width=26)
    else:
        draw.arc([cx - 180, cy - 50, cx - 100, cy + 40], start=90, end=270, fill="#7E22CE", width=28)
        draw.arc([cx + 100, cy - 50, cx + 180, cy + 40], start=270, end=90, fill="#7E22CE", width=28)
    img.save(filepath, "PNG")

# ----------------- 5. FINANCE BUSINESS OWL -----------------
def draw_finance_mascot(pose: str, filepath: Path):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 50
    draw_base_shadow(draw, cx)
    
    # Body (Wise Emerald Business Suit)
    draw.rounded_rectangle([cx - 140, cy - 110, cx + 140, cy + 220], radius=90, fill="#064E3B", outline="#047857", width=6)
    draw.polygon([(cx - 40, cy - 110), (cx + 40, cy - 110), (cx, cy + 60)], fill="#FFFFFF") # Shirt
    draw.polygon([(cx - 15, cy - 80), (cx + 15, cy - 80), (cx, cy + 50)], fill="#F59E0B") # Golden Tie
    # Owl Head
    draw.ellipse([cx - 150, cy - 230, cx + 150, cy - 40], fill="#78350F", outline="#92400E", width=6)
    # Glasses
    draw.ellipse([cx - 110, cy - 180, cx - 20, cy - 90], outline="#F59E0B", width=7)
    draw.ellipse([cx + 20, cy - 180, cx + 110, cy - 90], outline="#F59E0B", width=7)
    draw.line([(cx - 20, cy - 135), (cx + 20, cy - 135)], fill="#F59E0B", width=6)
    # Beak
    draw.polygon([(cx - 16, cy - 100), (cx + 16, cy - 100), (cx, cy - 65)], fill="#F59E0B")
    
    if pose == "pointing":
        draw.ellipse([cx - 75, cy - 145, cx - 55, cy - 125], fill="#047857")
        draw.ellipse([cx + 55, cy - 145, cx + 75, cy - 125], fill="#047857")
        draw.line([(cx + 110, cy + 30), (cx + 210, cy - 100)], fill="#78350F", width=26)
    elif pose == "thinking":
        draw.ellipse([cx - 75, cy - 145, cx - 55, cy - 125], fill="#047857")
        draw.ellipse([cx + 55, cy - 145, cx + 75, cy - 125], fill="#047857")
    elif pose == "chill":
        draw.arc([cx - 80, cy - 150, cx - 50, cy - 120], start=200, end=340, fill="#047857", width=5)
        draw.arc([cx + 50, cy - 150, cx + 80, cy - 120], start=200, end=340, fill="#047857", width=5)
    else:
        draw.ellipse([cx - 75, cy - 150, cx - 45, cy - 110], fill="#047857")
        draw.ellipse([cx + 45, cy - 150, cx + 75, cy - 110], fill="#047857")
    img.save(filepath, "PNG")

# ----------------- 6. GAMING CYBER BUNNY -----------------
def draw_gaming_mascot(pose: str, filepath: Path):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 50
    draw_base_shadow(draw, cx)
    
    # Bunny Ears
    draw.rounded_rectangle([cx - 110, cy - 320, cx - 50, cy - 160], radius=30, fill="#F8FAFC", outline="#E2E8F0", width=5)
    draw.rounded_rectangle([cx - 95, cy - 295, cx - 65, cy - 180], radius=15, fill="#F472B6")
    draw.rounded_rectangle([cx + 50, cy - 320, cx + 110, cy - 160], radius=30, fill="#F8FAFC", outline="#E2E8F0", width=5)
    draw.rounded_rectangle([cx + 65, cy - 295, cx + 95, cy - 180], radius=15, fill="#F472B6")
    # Body
    draw.rounded_rectangle([cx - 130, cy - 110, cx + 130, cy + 220], radius=85, fill="#F8FAFC", outline="#CBD5E1", width=6)
    # Head
    draw.ellipse([cx - 145, cy - 220, cx + 145, cy - 35], fill="#FFFFFF", outline="#E2E8F0", width=6)
    # RGB Gaming Headset
    draw.arc([cx - 160, cy - 240, cx + 160, cy - 70], start=180, end=360, fill="#06B6D4", width=14)
    draw.rounded_rectangle([cx - 170, cy - 170, cx - 130, cy - 80], radius=20, fill="#EC4899", outline="#DB2777", width=4)
    draw.rounded_rectangle([cx + 130, cy - 170, cx + 170, cy - 80], radius=20, fill="#EC4899", outline="#DB2777", width=4)
    # Bunny Face
    draw.polygon([(cx - 12, cy - 90), (cx + 12, cy - 90), (cx, cy - 78)], fill="#F472B6")
    
    if pose == "pointing":
        draw.ellipse([cx - 75, cy - 145, cx - 40, cy - 105], fill="#0284C7")
        draw.ellipse([cx + 40, cy - 145, cx + 75, cy - 105], fill="#0284C7")
        draw.line([(cx + 100, cy + 30), (cx + 200, cy - 100)], fill="#F8FAFC", width=24)
    elif pose == "thinking":
        draw.arc([cx - 75, cy - 140, cx - 40, cy - 110], start=200, end=340, fill="#0284C7", width=5)
        draw.ellipse([cx + 40, cy - 145, cx + 75, cy - 105], fill="#0284C7")
    elif pose == "chill":
        draw.arc([cx - 75, cy - 140, cx - 40, cy - 110], start=200, end=340, fill="#0284C7", width=5)
        draw.arc([cx + 40, cy - 140, cx + 75, cy - 110], start=200, end=340, fill="#0284C7", width=5)
    else:
        draw.ellipse([cx - 75, cy - 150, cx - 35, cy - 100], fill="#0284C7")
        draw.ellipse([cx + 35, cy - 150, cx + 75, cy - 100], fill="#0284C7")
    img.save(filepath, "PNG")

# ----------------- 7. PETS HAPPY SHIBA -----------------
def draw_pets_mascot(pose: str, filepath: Path):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 50
    draw_base_shadow(draw, cx)
    
    # Shiba Ears
    draw.polygon([(cx - 140, cy - 170), (cx - 75, cy - 260), (cx - 15, cy - 170)], fill="#D97706", outline="#B45309")
    draw.polygon([(cx + 15, cy - 170), (cx + 75, cy - 260), (cx + 140, cy - 170)], fill="#D97706", outline="#B45309")
    # Body
    draw.rounded_rectangle([cx - 135, cy - 100, cx + 135, cy + 220], radius=85, fill="#F59E0B", outline="#D97706", width=6)
    draw.ellipse([cx - 80, cy + 20, cx + 80, cy + 170], fill="#FEF3C7")
    # Head
    draw.ellipse([cx - 150, cy - 210, cx + 150, cy - 30], fill="#F59E0B", outline="#D97706", width=6)
    draw.ellipse([cx - 95, cy - 110, cx + 95, cy - 30], fill="#FFFFFF") # White Muzzle
    # Red Bandana Scarf
    draw.polygon([(cx - 90, cy - 35), (cx + 90, cy - 35), (cx, cy + 45)], fill="#EF4444")
    # Shiba Nose
    draw.ellipse([cx - 14, cy - 85, cx + 14, cy - 65], fill="#1E293B")
    
    if pose == "pointing":
        draw.arc([cx - 75, cy - 140, cx - 35, cy - 100], start=180, end=360, fill="#1E293B", width=6)
        draw.arc([cx + 35, cy - 140, cx + 75, cy - 100], start=180, end=360, fill="#1E293B", width=6)
        draw.line([(cx + 100, cy + 30), (cx + 200, cy - 100)], fill="#F59E0B", width=24)
    elif pose == "thinking":
        draw.arc([cx - 75, cy - 140, cx - 35, cy - 100], start=180, end=360, fill="#1E293B", width=6)
        draw.ellipse([cx + 40, cy - 140, cx + 75, cy - 100], fill="#1E293B")
    elif pose == "chill":
        draw.arc([cx - 75, cy - 140, cx - 35, cy - 100], start=180, end=360, fill="#1E293B", width=6)
        draw.arc([cx + 35, cy - 140, cx + 75, cy - 100], start=180, end=360, fill="#1E293B", width=6)
        draw.chord([cx - 25, cy - 65, cx + 25, cy - 35], start=0, end=180, fill="#EF4444")
    else:
        draw.ellipse([cx - 75, cy - 145, cx - 35, cy - 95], fill="#1E293B")
        draw.ellipse([cx + 35, cy - 145, cx + 75, cy - 95], fill="#1E293B")
        draw.chord([cx - 30, cy - 65, cx + 30, cy - 25], start=0, end=180, fill="#EF4444")
    img.save(filepath, "PNG")

# ----------------- 8. DEFAULT / UNIVERSAL ROBOT -----------------
def draw_default_mascot(pose: str, filepath: Path):
    draw_tech_mascot(pose, filepath)

def generate_all_category_mascots():
    generators = {
        "tech": draw_tech_mascot,
        "food": draw_food_mascot,
        "vehicles": draw_vehicles_mascot,
        "ai": draw_ai_mascot,
        "finance": draw_finance_mascot,
        "gaming": draw_gaming_mascot,
        "pets": draw_pets_mascot,
        "default": draw_default_mascot
    }
    
    poses = ["pointing", "thinking", "chill", "cta"]
    
    for cat_key, gen_func in generators.items():
        cat_dir = MASCOTS_ROOT / cat_key
        cat_dir.mkdir(parents=True, exist_ok=True)
        for pose in poses:
            target_file = cat_dir / f"{pose}.png"
            gen_func(pose, target_file)
            
    # Also mirror default to assets/mascot/
    legacy_mascot_dir = BASE_DIR / "assets" / "mascot"
    legacy_mascot_dir.mkdir(parents=True, exist_ok=True)
    for pose in poses:
        draw_default_mascot(pose, legacy_mascot_dir / f"{pose}.png")
        
    print("Successfully generated all 8 category mascots (32 pose files) in assets/mascots/!")

if __name__ == "__main__":
    generate_all_category_mascots()