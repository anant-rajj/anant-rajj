import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 920, 280
pad_x = 22
pad_y = 18
NUM_FRAMES = 300
FPS = 18

# Typography
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", 34)
try:
    font_bezel = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 9)
except Exception:
    font_bezel = ImageFont.load_default()

text = "ANANT RAJ"
dummy = Image.new("RGBA", (100, 100))
d_dum = ImageDraw.Draw(dummy)
bbox = d_dum.textbbox((0, 0), text, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
extra_w = 20
extra_h = 18

# Exact room dimensions for periodic billiard orbit (72 px/sec authentic slow screensaver drift)
X_room = 600
Y_room = 150
s = 4

# Center the bouncing room within CRT tube
min_x = pad_x + int((W - 2 * pad_x - (X_room + tw + extra_w)) / 2)
min_y = pad_y + int((H - 2 * pad_y - (Y_room + th + extra_h)) / 2)

# Palette of 10 classic Dish TV / Phosphor colors
palette = [
    (0, 255, 102),   # Electric Phosphor Green
    (0, 212, 255),   # Cyan Laser
    (255, 130, 0),   # Iconic Dish TV Tangerine
    (255, 30, 140),  # Hot Neon Fuchsia
    (255, 230, 0),   # Solar Canary
    (155, 81, 224),  # Electric Violet
    (255, 60, 100),  # Crimson Coral
    (56, 189, 248),  # Sky Diamond
    (163, 230, 53),  # Cyber Lime
    (245, 158, 11),  # Golden Amber
]

# Run discrete step simulation (exact open-source bouncing screensaver engine)
x0 = 80
y0 = 60
dx = 1
dy = 1

x = x0
y = y0

positions = []
current_color_idx = 0
frame_colors = []
frame_flash = []

for step in range(NUM_FRAMES):
    positions.append((min_x + x, min_y + y))
    
    x += dx * s
    y += dy * s
    
    hit = False
    if x <= 0:
        x = 0; dx = 1; hit = True
    elif x >= X_room:
        x = X_room; dx = -1; hit = True
        
    if y <= 0:
        y = 0; dy = 1; hit = True
    elif y >= Y_room:
        y = Y_room; dy = -1; hit = True
        
    if hit:
        current_color_idx = (current_color_idx + 1) % len(palette)
        
    frame_colors.append(palette[current_color_idx])
    frame_flash.append(hit)

def render_crt_frame(frame_idx):
    cur_x, cur_y = positions[frame_idx]
    accent_col = frame_colors[frame_idx]
    is_hit = frame_flash[frame_idx]

    tx = int(cur_x)
    ty = int(cur_y)

    # 1. Base CRT dark tube (#070a10)
    img = Image.new("RGBA", (W, H), (7, 10, 16, 255))

    # 2. Phosphor Glow Bloom Layer
    glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_glow = ImageDraw.Draw(glow_img)

    if is_hit:
        bloom_radii = (22, 15, 9, 4)
        base_alpha = 60
    else:
        bloom_radii = (15, 10, 6, 2)
        base_alpha = 42

    for rad in bloom_radii:
        alpha = int(base_alpha * (1.0 - rad / (bloom_radii[0] + 2)))
        d_glow.text((tx - rad, ty), text, font=font, fill=(*accent_col, alpha))
        d_glow.text((tx + rad, ty), text, font=font, fill=(*accent_col, alpha))
        d_glow.text((tx, ty - rad), text, font=font, fill=(*accent_col, alpha))
        d_glow.text((tx, ty + rad), text, font=font, fill=(*accent_col, alpha))

    # Dish TV curved antenna arc above "RAJ"
    arc_box = [tx + tw - 24, ty - 18, tx + tw + 10, ty + 18]
    d_glow.arc(arc_box, start=195, end=345, fill=(*accent_col, 190), width=3)
    d_glow.ellipse([tx + tw - 5, ty - 16, tx + tw + 2, ty - 9], fill=(*accent_col, 230))

    img = Image.alpha_composite(img, glow_img)
    draw = ImageDraw.Draw(img)

    # Core crisp text
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))
    draw.text((tx, ty), text, font=font, fill=(*accent_col, 175))

    # Sharp antenna arc on top
    draw.arc(arc_box, start=195, end=345, fill=(*accent_col, 255), width=2)
    draw.ellipse([tx + tw - 5, ty - 16, tx + tw + 2, ty - 9], fill=(255, 255, 255, 255))

    # 3. Authentic CRT Horizontal Scanlines across the ENTIRE tube
    for y_line in range(9, H - 9, 3):
        draw.line([(9, y_line), (W - 9, y_line)], fill=(0, 0, 0, 75), width=1)

    # 4. Outer TV Chassis Bezel & Framing
    draw.rounded_rectangle([2, 2, W - 3, H - 3], radius=18, outline=(30, 40, 58, 255), width=3)
    draw.rounded_rectangle([7, 7, W - 8, H - 8], radius=14, outline=(14, 20, 30, 255), width=2)
    draw.line([(35, 9), (W - 35, 9)], fill=(45, 65, 95, 175), width=1)
    draw.rounded_rectangle([9, 9, W - 10, H - 10], radius=12, outline=(5, 7, 11, 230), width=2)

    # 5. Chassis Hardware Markings (on bottom plastic bezel, outside glass)
    draw.text((pad_x + 10, H - 14), "DISH TV  //  COLOR CRT  576i", font=font_bezel, fill=(50, 70, 95, 190))
    draw.ellipse([W - pad_x - 70, H - 12, W - pad_x - 64, H - 6], fill=(0, 255, 102, 255))
    draw.ellipse([W - pad_x - 72, H - 14, W - pad_x - 62, H - 4], outline=(0, 255, 102, 90), width=1)
    draw.text((W - pad_x - 58, H - 14), "STANDBY", font=font_bezel, fill=(70, 100, 140, 180))

    return img.convert("RGB")

print("Rendering 300 frames of authentic slow-drift Dish TV screensaver...")
frames = []
for i in range(NUM_FRAMES):
    frames.append(render_crt_frame(i))

out_gif = "/Users/anantraj/anant-rajj/assets/dish-tv-screensaver.gif"
frames[0].save(
    out_gif,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=True
)

import shutil
shutil.copyfile(out_gif, "/Users/anantraj/anant-rajj/assets/classic-crt-dishtv.gif")
shutil.copyfile(out_gif, "/Users/anantraj/anant-rajj/assets/banner-3d-water.gif")

sz = os.path.getsize(out_gif)
print(f"Generated {out_gif}! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
