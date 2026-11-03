import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 920, 280
pad_x = 22
pad_y = 18
NUM_FRAMES = 180
FPS = 20

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

min_x = pad_x + 14
max_x = W - pad_x - 14 - (tw + extra_w)
min_y = pad_y + 14
max_y = H - pad_y - 20 - (th + extra_h)

def tri_wave(val):
    p = (val * 2.0) % 2.0
    return 1.0 - abs(p - 1.0)

# True 45-degree dynamical billiard parameters with mid-loop corner hits
Rx = 2
Ry = 7
px = 0.700
py = 0.700

# Rich 12-color Dish TV phosphor palette
palette = [
    (0, 255, 102),   # Electric Phosphor Green
    (0, 212, 255),   # Cyan Laser
    (255, 140, 0),   # Iconic Dish TV Tangerine
    (255, 20, 147),  # Hot Neon Fuchsia
    (255, 230, 0),   # Solar Canary
    (155, 81, 224),  # Electric Violet
    (255, 51, 102),  # Crimson Coral
    (56, 189, 248),  # Sky Diamond
    (163, 230, 53),  # Cyber Lime
    (245, 158, 11),  # Golden Amber
    (240, 246, 252), # Pure Phosphor White
    (0, 245, 212),   # Turquoise Glow
]

# Find all bounce events
bounces = []
for k in range(-10, 30):
    tx = (k / 2.0 - px) / Rx
    if 0 <= tx < 1.0:
        bounces.append((tx, "X"))
    ty = (k / 2.0 - py) / Ry
    if 0 <= ty < 1.0:
        bounces.append((ty, "Y"))

# Merge simultaneous bounces (corner hits)
b_times = sorted(list(set([round(b[0], 5) for b in bounces])))

# Assign color to each frame based on which bounce segment it is in
frame_colors = []
frame_flash = []
frame_corner = []

for i in range(NUM_FRAMES):
    t = i / NUM_FRAMES
    b_count = sum(1 for bt in b_times if bt <= t + 1e-4)
    c_idx = b_count % len(palette)
    frame_colors.append(palette[c_idx])
    
    is_hit = any(abs(t - bt) <= (1.1 / NUM_FRAMES) for bt in b_times)
    frame_flash.append(is_hit)
    
    is_corner = abs(i - 72) <= 1 or abs(i - 162) <= 1
    frame_corner.append(is_corner)

def render_crt_frame(frame_idx):
    t = frame_idx / NUM_FRAMES
    nx = tri_wave(Rx * t + px)
    ny = tri_wave(Ry * t + py)
    accent_col = frame_colors[frame_idx]
    is_hit = frame_flash[frame_idx]
    is_corner = frame_corner[frame_idx]

    cur_x = min_x + nx * (max_x - min_x)
    cur_y = min_y + ny * (max_y - min_y)
    tx = int(cur_x)
    ty = int(cur_y)

    # 1. Base CRT dark tube (#070a10)
    img = Image.new("RGBA", (W, H), (7, 10, 16, 255))

    # 2. Phosphor Glow Bloom Layer
    glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_glow = ImageDraw.Draw(glow_img)

    if is_corner:
        bloom_radii = (26, 18, 12, 6, 2)
        base_alpha = 75
    elif is_hit:
        bloom_radii = (20, 14, 8, 4)
        base_alpha = 55
    else:
        bloom_radii = (14, 9, 5, 2)
        base_alpha = 40

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
    # Phosphor tint on letters
    draw.text((tx, ty), text, font=font, fill=(*accent_col, 175))

    # Sharp antenna arc on top
    draw.arc(arc_box, start=195, end=345, fill=(*accent_col, 255), width=2)
    draw.ellipse([tx + tw - 5, ty - 16, tx + tw + 2, ty - 9], fill=(255, 255, 255, 255))

    # 3. Authentic CRT Horizontal Scanlines across the ENTIRE tube
    for y in range(9, H - 9, 3):
        draw.line([(9, y), (W - 9, y)], fill=(0, 0, 0, 75), width=1)

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

print("Rendering 180 frames of slowed, mathematical Dish TV screensaver...")
frames = []
for i in range(NUM_FRAMES):
    frames.append(render_crt_frame(i))

out_gif = "/Users/anantraj/anant-rajj/assets/classic-crt-dishtv.gif"
frames[0].save(
    out_gif,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=True
)

import shutil
shutil.copyfile(out_gif, "/Users/anantraj/anant-rajj/assets/banner-3d-water.gif")

sz = os.path.getsize(out_gif)
print(f"Generated {out_gif}! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
