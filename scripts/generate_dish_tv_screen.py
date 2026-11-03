import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 920, 280
pad_x = 22
pad_y = 18
NUM_FRAMES = 96
FPS = 24

# Typography
font_candidates = [
    ("/System/Library/Fonts/Supplemental/Arial Black.ttf", 36),
    ("/System/Library/Fonts/Supplemental/Futura.ttc", 38),
    ("/System/Library/Fonts/Helvetica.ttc", 38),
]
font_main = None
for p, s in font_candidates:
    if os.path.exists(p):
        try:
            font_main = ImageFont.truetype(p, s)
            break
        except Exception:
            pass
if not font_main:
    font_main = ImageFont.load_default()

try:
    font_bezel = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 9)
except Exception:
    font_bezel = ImageFont.load_default()

# Measure Name dimensions
text = "ANANT RAJ"
dummy = Image.new("RGBA", (100, 100))
d_dum = ImageDraw.Draw(dummy)
bbox = d_dum.textbbox((0, 0), text, font=font_main)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
extra_w = 20
extra_h = 18

# Full bouncing area within CRT glass
min_x = pad_x + 14
max_x = W - pad_x - 14 - (tw + extra_w)
min_y = pad_y + 14
max_y = H - pad_y - 20 - (th + extra_h)

def tri_wave(val):
    p = (val * 2.0) % 2.0
    return 1.0 - abs(p - 1.0)

# Authentic Dish TV & CRT Phosphor Colors
palette = [
    (0, 255, 102),   # Phosphor Green
    (0, 229, 255),   # Cyber Cyan
    (255, 153, 0),   # Dish TV Orange
    (255, 42, 133),  # Hot Magenta
    (155, 81, 224),  # Electric Violet
    (255, 230, 0),   # Neon Yellow
]

phi_x = 0.18
phi_y = 0.32

# Precompute bounce event times in [0, 1)
bounces = []
for k in range(-10, 20):
    tx = (k / 2.0 - phi_x) / 3.0
    if 0 <= tx < 1.0:
        bounces.append(tx)
    ty = (k / 2.0 - phi_y) / 4.0
    if 0 <= ty < 1.0:
        bounces.append(ty)
bounces.sort()

# Assign color to each frame based on which bounce interval it falls in
frame_colors = []
frame_flash = []

for i in range(NUM_FRAMES):
    t = i / NUM_FRAMES
    # Count how many bounces happened before t
    b_count = sum(1 for b in bounces if b <= t)
    c_idx = b_count % len(palette)
    frame_colors.append(palette[c_idx])
    
    # Check if this frame is right at a bounce impact (within 1 frame)
    is_hit = any(abs(t - b) <= (1.2 / NUM_FRAMES) for b in bounces)
    frame_flash.append(is_hit)

def render_crt_frame(frame_idx):
    t = frame_idx / NUM_FRAMES
    nx = tri_wave(3.0 * t + phi_x)
    ny = tri_wave(4.0 * t + phi_y)
    accent_col = frame_colors[frame_idx]
    is_hit = frame_flash[frame_idx]

    cur_x = min_x + nx * (max_x - min_x)
    cur_y = min_y + ny * (max_y - min_y)
    tx = int(cur_x)
    ty = int(cur_y)

    # 1. Base CRT dark tube (#070a10)
    img = Image.new("RGBA", (W, H), (7, 10, 16, 255))

    # 2. Phosphor Glow Bloom Layer (drawn before scanlines so scanlines cut through everything uniformly)
    glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_glow = ImageDraw.Draw(glow_img)

    # If hit a wall, produce a subtle bright flash bloom
    bloom_radii = (22, 16, 10, 5, 2) if is_hit else (16, 11, 7, 3)
    base_alpha = 65 if is_hit else 45

    for rad in bloom_radii:
        alpha = int(base_alpha * (1.0 - rad / (bloom_radii[0] + 2)))
        d_glow.text((tx - rad, ty), text, font=font_main, fill=(*accent_col, alpha))
        d_glow.text((tx + rad, ty), text, font=font_main, fill=(*accent_col, alpha))
        d_glow.text((tx, ty - rad), text, font=font_main, fill=(*accent_col, alpha))
        d_glow.text((tx, ty + rad), text, font=font_main, fill=(*accent_col, alpha))

    # Dish TV curved antenna arc above "RAJ"
    arc_box = [tx + tw - 26, ty - 18, tx + tw + 10, ty + 18]
    d_glow.arc(arc_box, start=195, end=345, fill=(*accent_col, 190), width=3)
    d_glow.ellipse([tx + tw - 5, ty - 16, tx + tw + 2, ty - 9], fill=(*accent_col, 230))

    img = Image.alpha_composite(img, glow_img)
    draw = ImageDraw.Draw(img)

    # Core crisp text
    draw.text((tx, ty), text, font=font_main, fill=(255, 255, 255, 255))
    # Phosphor tint on letters
    draw.text((tx, ty), text, font=font_main, fill=(*accent_col, 175))

    # Sharp antenna arc on top
    draw.arc(arc_box, start=195, end=345, fill=(*accent_col, 255), width=2)
    draw.ellipse([tx + tw - 5, ty - 16, tx + tw + 2, ty - 9], fill=(255, 255, 255, 255))

    # 3. Authentic CRT Horizontal Scanlines across the ENTIRE tube
    for y in range(9, H - 9, 3):
        draw.line([(9, y), (W - 9, y)], fill=(0, 0, 0, 75), width=1)

    # 4. Outer TV Chassis Bezel & Framing (drawn on top of tube for crisp corners)
    # Heavy outer chassis
    draw.rounded_rectangle([2, 2, W - 3, H - 3], radius=18, outline=(30, 40, 58, 255), width=3)
    # Bezel inner recess border
    draw.rounded_rectangle([7, 7, W - 8, H - 8], radius=14, outline=(14, 20, 30, 255), width=2)
    # Glass glare reflection on top edge of CRT tube
    draw.line([(35, 9), (W - 35, 9)], fill=(45, 65, 95, 175), width=1)
    # Inner tube shadow vignette
    draw.rounded_rectangle([9, 9, W - 10, H - 10], radius=12, outline=(5, 7, 11, 230), width=2)

    # 5. Chassis Hardware Markings (on bottom plastic bezel, outside glass)
    # Left: DISH TV brand debossed in chassis plastic
    draw.text((pad_x + 10, H - 14), "DISH TV  //  COLOR CRT  576i", font=font_bezel, fill=(50, 70, 95, 190))
    # Right: Standby LED & power label
    draw.ellipse([W - pad_x - 70, H - 12, W - pad_x - 64, H - 6], fill=(0, 255, 102, 255))
    draw.ellipse([W - pad_x - 72, H - 14, W - pad_x - 62, H - 4], outline=(0, 255, 102, 90), width=1)
    draw.text((W - pad_x - 58, H - 14), "STANDBY", font=font_bezel, fill=(70, 100, 140, 180))

    return img.convert("RGB")

print("Rendering 96 frames of perfected Dish TV bouncing name screensaver...")
frames = []
for i in range(NUM_FRAMES):
    frames.append(render_crt_frame(i))

# Export test frames
for sample_idx in [4, 10, 26, 40, 58]:
    frames[sample_idx].save(f"/Users/anantraj/.gemini/antigravity-cli/brain/1377b4ea-ad8b-442b-a8a5-d381ae393649/dishtv_bounce_hit_{sample_idx}.png")

out_gif = "/Users/anantraj/anant-rajj/assets/classic-crt-dishtv.gif"
frames[0].save(
    out_gif,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=True
)

# Overwrite banner-3d-water.gif as well
import shutil
shutil.copyfile(out_gif, "/Users/anantraj/anant-rajj/assets/banner-3d-water.gif")

sz = os.path.getsize(out_gif)
print(f"Generated {out_gif}! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
