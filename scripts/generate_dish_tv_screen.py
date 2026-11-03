import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 920, 280
pad_x = 22
pad_y = 18

NUM_FRAMES = 450
FPS = 10
DUR = 45.0

# Typography: crisp, high-clarity font
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

W_box = max_x - min_x
H_box = max_y - min_y

tube_top = 10
tube_bottom = H - 18
tube_height = tube_bottom - tube_top
tube_left = 10
tube_right = W - 10

def tri_wave(val):
    p = (val * 2.0) % 2.0
    return 1.0 - abs(p - 1.0)

Rx = 1.0
Ry = 4.0
px = 0.12
py = 0.28

# 10 vibrant Dish TV phosphor colors
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

bounces = []
for k in range(-10, 20):
    tx = (k / 2.0 - px) / Rx
    if 0 <= tx < 1.0:
        bounces.append((int(tx * NUM_FRAMES), 'X'))
    ty = (k / 2.0 - py) / Ry
    if 0 <= ty < 1.0:
        bounces.append((int(ty * NUM_FRAMES), 'Y'))
bounces.sort(key=lambda x: x[0])

# Precompute statistical P&C glitch schedule on the name
np.random.seed(42)
random.seed(42)

MODALITIES = ['H_TEAR', 'RGB_SPLIT', 'STATIC_BAND', 'INTERLACE_JITTER']
glitch_schedule = {}

def schedule_glitch_burst(start_frame, duration, severity=1.0):
    k_modalities = min(4, max(1, np.random.binomial(n=3, p=0.65) + 1))
    active_mods = random.sample(MODALITIES, k_modalities)
    params = {'modalities': active_mods, 'severity': severity}
    
    if 'H_TEAR' in active_mods:
        num_slices = random.choice([1, 2])
        slices = []
        for _ in range(num_slices):
            h_slice = int(np.random.normal(loc=28, scale=8))
            h_slice = max(14, min(55, h_slice))
            y_start = int(np.random.uniform(5, (H - 28) - h_slice))
            shift_x = int(np.random.normal(loc=0, scale=15 * severity))
            if shift_x == 0:
                shift_x = random.choice([-8, 8])
            slices.append((y_start, y_start + h_slice, shift_x))
        params['tear_slices'] = slices
        
    if 'RGB_SPLIT' in active_mods:
        split_px = int(np.random.poisson(lam=4.0 * severity)) + 2
        params['rgb_split_px'] = min(10, split_px)
        
    if 'STATIC_BAND' in active_mods:
        band_h = int(np.random.normal(loc=22, scale=6))
        band_h = max(12, min(45, band_h))
        y_band = int(np.random.uniform(5, (H - 28) - band_h))
        noise_alpha = float(np.random.uniform(0.18, 0.35) * severity)
        params['static_band'] = (y_band, y_band + band_h, noise_alpha)
        
    if 'INTERLACE_JITTER' in active_mods:
        params['jitter_px'] = random.choice([-2, 2, -3, 3])
        
    for d in range(duration):
        f = (start_frame + d) % NUM_FRAMES
        decay = math.exp(-d * 0.7)
        glitch_schedule[f] = (params, decay)

# 1. Statistical Impact Glitches on Wall Collisions (Bernoulli trial)
for b_frame, axis in bounces:
    if np.random.random() < 0.45:
        dur = random.choice([2, 3])
        schedule_glitch_burst(b_frame, dur, severity=1.2)

# 2. Ambient Signal Tracking Glitches (Poisson process)
target_ambient = 4
ambient_times = np.random.choice(range(10, NUM_FRAMES - 10), size=target_ambient, replace=False)
for a_frame in ambient_times:
    dur = random.choice([2, 3])
    schedule_glitch_burst(int(a_frame), dur, severity=0.9)

# Colors for each frame
raw_b_times = [b[0] / NUM_FRAMES for b in bounces]
frame_colors = []
for i in range(NUM_FRAMES):
    t = i / NUM_FRAMES
    b_count = sum(1 for bt in raw_b_times if bt <= t + 1e-4)
    c_idx = b_count % len(palette)
    frame_colors.append(palette[c_idx])

# Tube glitch engine (applied only inside active glass)
def apply_tube_glitch(tube_arr, params, decay):
    out = tube_arr.copy()
    th, tw, tc = out.shape
    mods = params['modalities']
    
    # Interlace jitter
    if 'INTERLACE_JITTER' in mods:
        j = int(params['jitter_px'] * decay)
        if j != 0:
            out[0::2, :, :] = np.roll(out[0::2, :, :], j, axis=1)
            out[1::2, :, :] = np.roll(out[1::2, :, :], -j, axis=1)
            
    # Horizontal scanline tear
    if 'H_TEAR' in mods and 'tear_slices' in params:
        for y1, y2, shift in params['tear_slices']:
            s = int(shift * decay)
            if s != 0:
                y1_c = max(0, min(th - 1, y1))
                y2_c = max(0, min(th - 1, y2))
                if y1_c < y2_c:
                    out[y1_c:y2_c, :, :] = np.roll(out[y1_c:y2_c, :, :], s, axis=1)
                    
    # Static noise band
    if 'STATIC_BAND' in mods and 'static_band' in params:
        y1, y2, alpha = params['static_band']
        y1_c = max(0, min(th - 1, y1))
        y2_c = max(0, min(th - 1, y2))
        eff_alpha = alpha * decay
        if y1_c < y2_c and eff_alpha > 0.05:
            noise = np.random.normal(loc=120, scale=70, size=(y2_c - y1_c, tw, tc)).astype(np.float32)
            orig = out[y1_c:y2_c, :, :].astype(np.float32)
            blended = (1.0 - eff_alpha) * orig + eff_alpha * noise
            out[y1_c:y2_c, :, :] = np.clip(blended, 0, 255).astype(np.uint8)
            
    # RGB chromatic aberration (phosphor beam misconvergence)
    if 'RGB_SPLIT' in mods and 'rgb_split_px' in params:
        split = int(params['rgb_split_px'] * decay)
        if split > 0:
            r = np.roll(out[:, :, 0], -split, axis=1)
            g = out[:, :, 1]
            b = np.roll(out[:, :, 2], split, axis=1)
            out = np.stack([r, g, b], axis=2)
            
    return out

def render_crt_frame(frame_idx):
    t = frame_idx / NUM_FRAMES
    nx = tri_wave(Rx * t + px)
    ny = tri_wave(Ry * t + py)
    accent_col = frame_colors[frame_idx]

    cur_x = min_x + nx * W_box
    cur_y = min_y + ny * H_box
    tx = int(cur_x)
    ty = int(cur_y)

    # 1. Base CRT dark tube (#070a10)
    img = Image.new("RGBA", (W, H), (7, 10, 16, 255))

    # 2. Slow Rolling CRT Line / Hum Bar running slowly all over the screen
    # Takes 22.5s per sweep down the tube (2 full slow sweeps across 45.0s loop)
    roll_phase = (t * 2.0) % 1.0
    roll_y = tube_top + roll_phase * tube_height
    bar_height = 26

    roll_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_roll = ImageDraw.Draw(roll_overlay)

    for dy in range(-int(bar_height / 2), int(bar_height / 2)):
        y_pos = int(roll_y + dy)
        if tube_top <= y_pos <= tube_bottom:
            dist = abs(dy) / (bar_height / 2.0)
            alpha = int(32 * (1.0 - dist * dist))
            d_roll.line([(tube_left, y_pos), (tube_right, y_pos)], fill=(*accent_col, alpha), width=1)
            # Center bright scanline beam
            if dy == 0:
                d_roll.line([(tube_left, y_pos), (tube_right, y_pos)], fill=(255, 255, 255, 55), width=1)

    img = Image.alpha_composite(img, roll_overlay)

    # 3. Razor-Sharp Text & Tight Phosphor Glow (More clear pixels!)
    glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_glow = ImageDraw.Draw(glow_img)

    # High-clarity tight glow (sharp, vibrant halo, zero muddy blur)
    for rad, alpha in [(8, 45), (5, 65), (3, 90), (1, 140)]:
        d_glow.text((tx - rad, ty), text, font=font, fill=(*accent_col, alpha))
        d_glow.text((tx + rad, ty), text, font=font, fill=(*accent_col, alpha))
        d_glow.text((tx, ty - rad), text, font=font, fill=(*accent_col, alpha))
        d_glow.text((tx, ty + rad), text, font=font, fill=(*accent_col, alpha))

    # Dish TV curved antenna arc above "RAJ"
    arc_box = [tx + tw - 24, ty - 18, tx + tw + 10, ty + 18]
    d_glow.arc(arc_box, start=195, end=345, fill=(*accent_col, 200), width=3)
    d_glow.ellipse([tx + tw - 5, ty - 16, tx + tw + 2, ty - 9], fill=(*accent_col, 240))

    img = Image.alpha_composite(img, glow_img)
    draw = ImageDraw.Draw(img)

    # Core 100% white crisp text for pin-sharp readability
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))
    draw.text((tx, ty), text, font=font, fill=(*accent_col, 160))

    # Sharp antenna arc on top
    draw.arc(arc_box, start=195, end=345, fill=(*accent_col, 255), width=2)
    draw.ellipse([tx + tw - 5, ty - 16, tx + tw + 2, ty - 9], fill=(255, 255, 255, 255))

    # 4. Clean 1px CRT Scanlines across the tube
    for y_line in range(tube_top, tube_bottom, 3):
        draw.line([(tube_left, y_line), (tube_right, y_line)], fill=(0, 0, 0, 60), width=1)

    # 5. Statistical Old Television Glitch (Applied strictly inside cathode tube glass)
    if frame_idx in glitch_schedule:
        params, decay = glitch_schedule[frame_idx]
        tube_crop = np.array(img)[10:H-18, 10:W-10, :3]
        glitched_crop = apply_tube_glitch(tube_crop, params, decay)
        img_np = np.array(img)
        img_np[10:H-18, 10:W-10, :3] = glitched_crop
        img = Image.fromarray(img_np)
        draw = ImageDraw.Draw(img)

    # 6. Outer TV Chassis Bezel & Framing (Drawn on top so chassis remains physically solid)
    draw.rounded_rectangle([2, 2, W - 3, H - 3], radius=18, outline=(35, 45, 65, 255), width=3)
    draw.rounded_rectangle([7, 7, W - 8, H - 8], radius=14, outline=(14, 20, 30, 255), width=2)
    draw.line([(35, 9), (W - 35, 9)], fill=(50, 70, 105, 185), width=1)
    draw.rounded_rectangle([9, 9, W - 10, H - 10], radius=12, outline=(5, 7, 11, 230), width=2)

    # 7. Chassis Hardware Markings (on bottom plastic bezel, outside glass)
    draw.text((pad_x + 10, H - 14), "DISH TV  //  COLOR CRT  576i", font=font_bezel, fill=(60, 85, 115, 220))
    draw.ellipse([W - pad_x - 70, H - 12, W - pad_x - 64, H - 6], fill=(0, 255, 102, 255))
    draw.ellipse([W - pad_x - 72, H - 14, W - pad_x - 62, H - 4], outline=(0, 255, 102, 120), width=1)
    draw.text((W - pad_x - 58, H - 14), "STANDBY", font=font_bezel, fill=(80, 120, 160, 210))

    return img.convert("RGB")

print(f"Rendering {NUM_FRAMES} frames of ultra-slow Dish TV screensaver with slow rolling line & crystal clear pixels...")
frames = []
for i in range(NUM_FRAMES):
    frames.append(render_crt_frame(i))

# Quantize frames with 256 colors and NO dithering for razor-sharp pixel clarity!
print("Quantizing with 256 colors & Dither.NONE for crisp pixels...")
q_frames = []
for f in frames:
    q_frames.append(f.convert('P', palette=Image.ADAPTIVE, colors=256, dither=Image.Dither.NONE))

out_gif = "/Users/anantraj/anant-rajj/assets/dish-tv-screensaver.gif"
q_frames[0].save(
    out_gif,
    save_all=True,
    append_images=q_frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=True
)

import shutil
shutil.copyfile(out_gif, "/Users/anantraj/anant-rajj/assets/classic-crt-dishtv.gif")
shutil.copyfile(out_gif, "/Users/anantraj/anant-rajj/assets/banner-3d-water.gif")

sz = os.path.getsize(out_gif)
print(f"Generated {out_gif}! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
