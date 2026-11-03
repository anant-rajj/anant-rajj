import math
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 920, 320
NUM_FRAMES = 40
FPS = 20
bg_color = (13, 17, 23, 255)  # Exact GitHub Dark background #0d1117

# System Fonts
try:
    font_title = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 34)
    font_subtitle = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 13)
    font_mono = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 10)
    font_badge = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 11)
except Exception:
    font_title = ImageFont.load_default()
    font_subtitle = ImageFont.load_default()
    font_mono = ImageFont.load_default()
    font_badge = ImageFont.load_default()

# Dot Grid Configuration
spacing = 18
cols = int(W / spacing) + 3
rows = int(H / spacing) + 3

grid_x = np.arange(cols) * spacing - 15
grid_y = np.arange(rows) * spacing - 15
GridX, GridY = np.meshgrid(grid_x, grid_y)
GridX = GridX.flatten().astype(np.float64)
GridY = GridY.flatten().astype(np.float64)
num_dots = len(GridX)

R = 135.0  # 3D sphere radius

# Virtual Light
Lx, Ly, Lz = -0.35, -0.45, 0.82
l_len = math.sqrt(Lx**2 + Ly**2 + Lz**2)
Lx /= l_len; Ly /= l_len; Lz /= l_len

def render_frame(t):
    w = 2 * math.pi * t

    # Smooth motion on right/center-right so it never occludes name on left
    cur_x = W * 0.64 + 80.0 * math.cos(w)
    cur_y = H * 0.52 + 25.0 * math.sin(w)

    dx = GridX - cur_x
    dy = GridY - cur_y
    dist = np.sqrt(dx**2 + dy**2)
    inside = dist < R

    z = np.zeros(num_dots)
    z[inside] = np.sqrt(np.maximum(0.0, R**2 - dist[inside]**2))

    nx = np.zeros(num_dots)
    ny = np.zeros(num_dots)
    nz = np.ones(num_dots)
    nx[inside] = dx[inside] / R
    ny[inside] = dy[inside] / R
    nz[inside] = z[inside] / R

    angle = np.arctan2(dy, dx)
    norm_dist = np.clip(dist / R, 0.0, 1.0)
    sphere_angle = np.arcsin(norm_dist)
    proj_r = R * np.sin(sphere_angle * 0.78)

    fx = GridX.copy()
    fy = GridY.copy()
    fx[inside] = cur_x + np.cos(angle[inside]) * proj_r[inside]
    fy[inside] = cur_y + np.sin(angle[inside]) * proj_r[inside]

    NdotL = np.clip(nx * Lx + ny * Ly + nz * Lz, 0.0, 1.0)
    spec = np.power(NdotL, 18.0)

    img = Image.new("RGBA", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # Soft ambient glow under sphere
    sphere_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_glow = ImageDraw.Draw(sphere_glow)
    for rad in range(int(R * 1.3), 15, -15):
        alpha = int(20 * (1.0 - rad / (R * 1.3)))
        d_glow.ellipse([cur_x - rad, cur_y - rad, cur_x + rad, cur_y + rad],
                       fill=(0, 255, 136, alpha))
    img = Image.alpha_composite(img, sphere_glow)
    draw = ImageDraw.Draw(img)

    # Draw all dots (flowing across full area, no lines)
    for i in range(num_dots):
        px = fx[i]
        py = fy[i]

        if px < -6 or px > W + 6 or py < -6 or py > H + 6:
            continue

        edge_x = min(px, W - px) / 40.0
        edge_y = min(py, H - py) / 30.0
        edge_fade = max(0.0, min(1.0, min(edge_x, edge_y)))

        if inside[i]:
            illum = 0.5 + 0.5 * NdotL[i] + spec[i] * 0.8
            r_col = int(min(255, 20 + 200 * spec[i]))
            g_col = int(min(255, 185 + 70 * illum))
            b_col = int(min(255, 60 + 190 * spec[i]))
            dot_alpha = int(255 * edge_fade)
            dot_r = 1.6 + 2.2 * (z[i] / R)

            if (z[i] / R) > 0.35:
                draw.ellipse([px - dot_r*1.8, py - dot_r*1.8, px + dot_r*1.8, py + dot_r*1.8],
                             fill=(r_col, g_col, b_col, dot_alpha // 4))
        else:
            r_col, g_col, b_col = 45, 190, 110
            dot_alpha = int(105 * edge_fade)
            dot_r = 1.3

        draw.ellipse([px - dot_r, py - dot_r, px + dot_r, py + dot_r],
                     fill=(r_col, g_col, b_col, dot_alpha))

    # Clean Typography directly over the dots with soft text drop shadow
    title_x = 42
    title_y = 48

    for dx_s, dy_s in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(0,2)]:
        draw.text((title_x + dx_s, title_y + dy_s), "ANANT RAJ", font=font_title, fill=(13, 17, 23, 230))
        draw.text((title_x + 215 + dx_s, title_y + 8 + dy_s), "• R&D SYSTEMS & HARDWARE CONTROLS", font=font_subtitle, fill=(13, 17, 23, 230))
        draw.text((title_x + dx_s, title_y + 44 + dy_s), "Research. Understand. Design. Implement. Test. Improve.", font=font_mono, fill=(13, 17, 23, 230))

    draw.text((title_x, title_y), "ANANT RAJ", font=font_title, fill=(255, 255, 255, 255))
    draw.text((title_x + 215, title_y + 8), "• R&D SYSTEMS & HARDWARE CONTROLS", font=font_subtitle, fill=(87, 242, 135, 245))
    draw.text((title_x, title_y + 44), "Research. Understand. Design. Implement. Test. Improve.", font=font_mono, fill=(180, 210, 240, 235))

    # Top right status badge
    st_x = W - 245
    st_y = 50
    draw.rounded_rectangle([st_x, st_y, st_x + 205, st_y + 28], radius=14,
                           fill=(18, 25, 38, 210), outline=(87, 242, 135, 130), width=1)
    pulse = 0.75 + 0.25 * math.sin(w)
    draw.ellipse([st_x + 12, st_y + 10, st_x + 20, st_y + 18], fill=(87, 242, 135, int(255 * pulse)))
    draw.text((st_x + 26, st_y + 7), "AGY 3D DOT GRID SPHERE", font=font_badge, fill=(215, 250, 230, 240))

    # Bottom Roles Badges
    badges = [
        ("NATIVE MACOS", (0, 242, 254)),
        ("VERIPACK AUDIT", (87, 242, 135)),
        ("AI SWARM FLEET", (157, 78, 221)),
        ("IIT BOMBAY NEC", (255, 170, 0)),
        ("ROBOTICS LAB", (0, 210, 255)),
    ]
    bx = title_x
    by = H - 46
    for b_text, b_col in badges:
        bw = len(b_text) * 7.0 + 20
        draw.rounded_rectangle([bx, by, bx + bw, by + 22], radius=6,
                               fill=(16, 22, 34, 210), outline=(*b_col, 110), width=1)
        draw.text((bx + 10, by + 4), b_text, font=font_badge, fill=(255, 255, 255, 240))
        bx += bw + 10

    return img.convert("RGB")

t0 = time.time()
frames = []
print("Rendering 40 frames of AGY 3D Dot Grid Sphere Banner...")
for frame_idx in range(NUM_FRAMES):
    t = frame_idx / NUM_FRAMES
    f = render_frame(t)
    frames.append(f)

output_path = "/Users/anantraj/anant-rajj/assets/banner-3d-water.gif"
frames[0].save(
    output_path,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=True
)

import os
sz = os.path.getsize(output_path)
print(f"AGY Dot Grid Banner generated in {(time.time() - t0):.1f}s! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
