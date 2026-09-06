from PIL import Image, ImageDraw

def create_app_icon(output_path):
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background rounded square with gradient look
    draw.rounded_rectangle([10, 10, 246, 246], radius=55, fill="#0F172A", outline="#38BDF8", width=8)
    draw.rounded_rectangle([25, 25, 231, 231], radius=45, fill="#1E293B")
    
    # Clapperboard / Video Camera Icon
    # Play Triangle in vibrant Gold/Cyan
    draw.polygon([(95, 75), (95, 181), (185, 128)], fill="#F59E0B", outline="#FEF08A", width=4)
    
    # Red recording dot
    draw.ellipse([185, 45, 215, 75], fill="#EF4444")
    
    # Save as .ico containing multiple resolutions
    img.save(output_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Created app icon: {output_path}")

if __name__ == "__main__":
    create_app_icon("assets/icon.ico")