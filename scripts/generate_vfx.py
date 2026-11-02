import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 900, 320
NUM_FRAMES = 36  # Smooth 20-24 fps loop
FPS = 20

# Load fonts
try:
    font_title = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 36)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 14)
    font_badge = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 11)
    font_status = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 12)
except Exception:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_badge = ImageFont.load_default()
    font_status = ImageFont.load_default()

# 3D Grid Parameters
nx, ny = 48, 28
xs = np.linspace(-4.5, 4.5, nx)
ys = np.linspace(1.2, 7.2, ny)
X, Y = np.meshgrid(xs, ys)

# Particle stars/droplets
np.random.seed(42)
num_particles = 30
px = np.random.uniform(-4.0, 4.0, num_particles)
py = np.random.uniform(1.5, 6.5, num_particles)
p_phase = np.random.uniform(0, 2 * math.pi, num_particles)

frames = []

for frame_idx in range(NUM_FRAMES):
    t = frame_idx / NUM_FRAMES
    w1 = 2 * math.pi * t
    w2 = 4 * math.pi * t
    w3 = 6 * math.pi * t

    # 3D Water Wave Equations (fluid wave interference)
    # Wave 1: primary diagonal roller
    Z1 = 0.42 * np.sin(1.4 * X - 1.6 * Y + w1)
    # Wave 2: counter swell
    Z2 = 0.28 * np.cos(1.8 * X + 1.2 * Y - w2)
    # Wave 3: central circular ripple
    R = np.sqrt(X**2 + (Y - 3.8)**2)
    Z3 = 0.22 * np.sin(2.8 * R - w2)
    # Wave 4: high-frequency capillary shimmer
    Z4 = 0.12 * np.sin(3.2 * X + w3) * np.cos(2.8 * Y - w1)

    Z = Z1 + Z2 + Z3 + Z4

    # Perspective Projection
    # Screen X, Y
    f_x = 470
    f_y = 380
    y_cam_offset = 1.15
    
    ProjX = (X / Y) * f_x + (W / 2)
    ProjY = ((-Z + y_cam_offset) / Y) * f_y + (H / 2) + 35

    # Create Frame Canvas
    img = Image.new("RGBA", (W, H), (11, 14, 23, 255))
    draw = ImageDraw.Draw(img)

    # Ambient deep ocean / nebula glow background
    for r in range(120, 0, -20):
        alpha = int(12 * (1 - r / 120))
        draw.ellipse([W//2 - r*2.5, H//2 - r - 20, W//2 + r*2.5, H//2 + r + 40],
                     fill=(20, 35, 75, alpha))
        draw.ellipse([200 - r, 100 - r//2, 200 + r, 100 + r//2],
                     fill=(30, 20, 65, alpha))

    # Render Water Mesh (Back to Front for painter's algorithm)
    for j in range(ny - 2, -1, -1):
        # Draw shaded fluid ribbon
        for i in range(nx - 1):
            p1 = (ProjX[j, i], ProjY[j, i])
            p2 = (ProjX[j, i+1], ProjY[j, i+1])
            p3 = (ProjX[j+1, i+1], ProjY[j+1, i+1])
            p4 = (ProjX[j+1, i], ProjY[j+1, i])

            # Normal / slope lighting
            avg_z = (Z[j, i] + Z[j, i+1] + Z[j+1, i+1] + Z[j+1, i]) / 4.0
            depth_factor = 1.0 - (ys[j] - ys[0]) / (ys[-1] - ys[0])
            
            # Fluid color mapping:
            # Deep trough -> Dark Discord Navy / Purple
            # Mid -> Electric Blue / Cyan
            # Crest -> Pure Glowing Neon Aqua / White
            norm_z = (avg_z + 0.8) / 1.6
            norm_z = max(0.0, min(1.0, norm_z))

            if norm_z < 0.4:
                # Deep water trough
                factor = norm_z / 0.4
                r_c = int(12 + factor * 20)
                g_c = int(22 + factor * 40)
                b_c = int(50 + factor * 90)
            elif norm_z < 0.75:
                # Mid wave body (electric cyan / blurple)
                factor = (norm_z - 0.4) / 0.35
                r_c = int(32 + factor * (0 - 32))
                g_c = int(62 + factor * (210 - 62))
                b_c = int(140 + factor * (254 - 140))
            else:
                # Wave crest (glowing neon / foam)
                factor = (norm_z - 0.75) / 0.25
                r_c = int(0 + factor * 180)
                g_c = int(210 + factor * 45)
                b_c = int(254 + factor * 1)

            # Modulate with depth
            r_c = int(r_c * (0.35 + 0.65 * depth_factor))
            g_c = int(g_c * (0.35 + 0.65 * depth_factor))
            b_c = int(b_c * (0.35 + 0.65 * depth_factor))
            poly_color = (r_c, g_c, b_c, 210)

            draw.polygon([p1, p2, p3, p4], fill=poly_color)

        # Wireframe neon surface highlight lines
        for i in range(nx - 1):
            p1 = (ProjX[j, i], ProjY[j, i])
            p2 = (ProjX[j, i+1], ProjY[j, i+1])
            avg_z = (Z[j, i] + Z[j, i+1]) / 2.0
            norm_z = max(0.0, min(1.0, (avg_z + 0.8) / 1.6))
            depth_factor = 1.0 - (ys[j] - ys[0]) / (ys[-1] - ys[0])
            
            line_a = int(depth_factor * (60 + 195 * norm_z))
            line_color = (int(0 + 100*norm_z), int(180 + 75*norm_z), 254, line_a)
            draw.line([p1, p2], fill=line_color, width=1)

    # Floating luminous droplets / bio-luminescent particles
    for k in range(num_particles):
        px_k = px[k]
        py_k = py[k]
        phase_k = p_phase[k]
        # Wave height at particle pos
        z_k = 0.42 * math.sin(1.4*px_k - 1.6*py_k + w1) + 0.28 * math.cos(1.8*px_k + 1.2*py_k - w2) + 0.15
        
        # Bobbing above wave
        z_float = z_k + 0.15 + 0.08 * math.sin(phase_k + w2)
        sc_x = (px_k / py_k) * f_x + (W / 2)
        sc_y = ((-z_float + y_cam_offset) / py_k) * f_y + (H / 2) + 35
        
        rad = max(1.0, 3.2 / py_k)
        glow_alpha = int((0.5 + 0.5 * math.sin(phase_k + w1)) * 240)
        draw.ellipse([sc_x - rad*1.8, sc_y - rad*1.8, sc_x + rad*1.8, sc_y + rad*1.8],
                     fill=(0, 242, 254, glow_alpha // 3))
        draw.ellipse([sc_x - rad, sc_y - rad, sc_x + rad, sc_y + rad],
                     fill=(220, 255, 255, glow_alpha))

    # Top & Bottom Smooth Gradient Fade to blend seamlessly with GitHub dark mode
    fade_top = Image.new("RGBA", (W, 70), (0, 0, 0, 0))
    draw_fade = ImageDraw.Draw(fade_top)
    for y in range(70):
        a = int(240 * (1.0 - y / 70.0)**1.5)
        draw_fade.line([(0, y), (W, y)], fill=(11, 14, 23, a))
    img.paste(fade_top, (0, 0), fade_top)

    fade_bottom = Image.new("RGBA", (W, 60), (0, 0, 0, 0))
    draw_fade_b = ImageDraw.Draw(fade_bottom)
    for y in range(60):
        a = int(245 * (y / 60.0)**1.5)
        draw_fade_b.line([(0, y), (W, y)], fill=(11, 14, 23, a))
    img.paste(fade_bottom, (0, H - 60), fade_bottom)

    # Outer Discord Nitro Style Cyber Border with Glow
    draw.rounded_rectangle([4, 4, W - 5, H - 5], radius=16, outline=(0, 242, 254, 140), width=1)
    draw.rounded_rectangle([6, 6, W - 7, H - 7], radius=14, outline=(88, 101, 242, 70), width=1)

    # Discord Profile Status Pill (Top Left)
    pill_x, pill_y = 28, 22
    draw.rounded_rectangle([pill_x, pill_y, pill_x + 360, pill_y + 26], radius=13,
                           fill=(18, 24, 38, 210), outline=(0, 242, 254, 120), width=1)
    
    # Pulsing Green Discord Status Dot
    dot_pulse = 0.7 + 0.3 * math.sin(w1)
    dot_r = 4.5 * dot_pulse
    draw.ellipse([pill_x + 12 - dot_r*1.5, pill_y + 13 - dot_r*1.5, pill_x + 12 + dot_r*1.5, pill_y + 13 + dot_r*1.5],
                 fill=(87, 242, 135, int(80 * dot_pulse)))
    draw.ellipse([pill_x + 12 - 4, pill_y + 13 - 4, pill_x + 12 + 4, pill_y + 13 + 4],
                 fill=(87, 242, 135, 255))
    draw.text((pill_x + 24, pill_y + 5), "ACTIVE SYSTEM // DISCORD NITRO ARCHITECTURE",
              font=font_status, fill=(200, 220, 245, 240))

    # Right side: Latency & Telemetry Pill
    lat_x = W - 230
    draw.rounded_rectangle([lat_x, pill_y, lat_x + 202, pill_y + 26], radius=13,
                           fill=(18, 24, 38, 210), outline=(88, 101, 242, 120), width=1)
    draw.text((lat_x + 14, pill_y + 5), "60 FPS 3D FLUID // VERIFIED",
              font=font_status, fill=(0, 242, 254, 230))

    # Main Headline (Anant Raj) with 3D drop glow
    title_x, title_y = 32, 68
    draw.text((title_x + 2, title_y + 2), "ANANT RAJ", font=font_title, fill=(0, 180, 254, 100))
    draw.text((title_x, title_y), "ANANT RAJ", font=font_title, fill=(255, 255, 255, 255))
    
    # Nitro Diamond Icon & Badges
    dia_x = title_x + 225
    draw.polygon([(dia_x+8, title_y+6), (dia_x+16, title_y+14), (dia_x+8, title_y+24), (dia_x, title_y+14)],
                 fill=(0, 242, 254, 255))
    draw.text((dia_x + 24, title_y + 6), "• R&D SYSTEMS & HARDWARE", font=ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 20) if 'font_title' in locals() else font_title,
              fill=(0, 242, 254, 240))

    # Subtitle / Philosophy with blinking terminal cursor
    cursor = "█" if (frame_idx % 18 < 10) else " "
    subtitle_text = f"Research. Understand. Design. Implement. Test. {cursor}"
    draw.text((title_x + 2, title_y + 46), subtitle_text, font=font_sub, fill=(180, 210, 240, 230))

    # Interactive-Looking Feature Badges (Discord Profile Roles Style)
    badges = [
        ("NATIVE MACOS", (0, 242, 254), (10, 40, 60)),
        ("VERIPACK LEAD", (87, 242, 135), (10, 50, 30)),
        ("AI SWARM FLEET", (157, 78, 221), (40, 20, 60)),
        ("IIT BOMBAY NEC", (255, 170, 0), (60, 40, 10)),
        ("ROBOTICS LAB", (0, 210, 255), (10, 45, 55)),
    ]
    
    bx = title_x
    by = H - 52
    for b_text, b_border, b_bg in badges:
        bw = len(b_text) * 7.5 + 24
        draw.rounded_rectangle([bx, by, bx + bw, by + 24], radius=8,
                               fill=(*b_bg, 220), outline=(*b_border, 180), width=1)
        draw.text((bx + 12, by + 5), b_text, font=font_badge, fill=(255, 255, 255, 250))
        bx += bw + 12

    frames.append(img.convert("RGB"))

# Save optimized GIF
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
print(f"3D Fluid Water GIF successfully created! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
