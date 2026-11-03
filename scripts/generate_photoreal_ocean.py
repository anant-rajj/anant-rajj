import math
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 920, 340
NUM_FRAMES = 36  # Seamless loop
FPS = 20

# System Fonts
try:
    font_title = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 32)
    font_subtitle = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 13)
    font_mono = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 10)
    font_status = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 11)
    font_badge = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 11)
except Exception:
    font_title = ImageFont.load_default()
    font_subtitle = ImageFont.load_default()
    font_mono = ImageFont.load_default()
    font_status = ImageFont.load_default()
    font_badge = ImageFont.load_default()

# Cinematic VFX Telephoto Camera (Depth-compressed, full-canvas 3D ocean)
fov = 0.65  # Narrow cinematic lens: compresses perspective gracefully
pitch = math.radians(22)  # Downward angle: 100% of screen is ocean
cam_height = 4.8

px = np.linspace(-1.0, 1.0, W)
py = np.linspace(1.0, -1.0, H)
PX, PY = np.meshgrid(px, py)
aspect = W / H

RayX = PX * aspect * math.tan(fov / 2)
RayY = PY * math.tan(fov / 2)
RayZ = np.ones_like(RayX)
ray_len = np.sqrt(RayX**2 + RayY**2 + RayZ**2)
RD_x = RayX / ray_len
RD_y = RayY / ray_len
RD_z = RayZ / ray_len

cos_p, sin_p = math.cos(pitch), math.sin(pitch)
RD_y_final = RD_y * cos_p - RD_z * sin_p
RD_z_final = RD_y * sin_p + RD_z * cos_p
RD_x_final = RD_x

# Moonlight Key Light (glowing shimmer trail down the center)
L = np.array([0.04, 0.38, 0.92])
L = L / np.linalg.norm(L)

nominal_dist = -cam_height / RD_y_final

# Multi-scale Gerstner waves: rich organic ocean harmonics
gerstner_waves = [
    # Primary rolling oceanic swell
    (0.45, 0.85, 0.22, 1),
    (-0.65, 0.75, 0.16, 1),
    # Secondary cross-sea swells
    (0.95, 1.30, 0.08, 2),
    (-1.30, 0.90, 0.06, 2),
    # Mid-range liquid ridges
    (1.40, 2.00, 0.035, 2),
    # High-definition capillary surface ripples (crisp realistic caustics)
    (2.10, 2.80, 0.024, 3),
    (-2.80, 1.90, 0.018, 3),
    (4.20, 3.80, 0.009, 4),
    (-4.50, 3.20, 0.006, 4)
]

def render_frame(t):
    w = 2 * math.pi * t

    # 1. 2-Step Geometric Refinement
    dist = nominal_dist.copy()
    WX = dist * RD_x_final
    WZ = dist * RD_z_final

    H_est = np.zeros_like(WX)
    for kx, kz, A, speed in gerstner_waves:
        phase = kx * WX + kz * WZ - speed * w
        H_est += A * np.cos(phase)

    dist = -(cam_height - H_est * 0.85) / RD_y_final
    WX = dist * RD_x_final
    WZ = dist * RD_z_final

    # Calculate exact Gerstner waves and surface normals
    Height = np.zeros_like(WX)
    GradX = np.zeros_like(WX)
    GradZ = np.zeros_like(WX)

    for kx, kz, A, speed in gerstner_waves:
        phase = kx * WX + kz * WZ - speed * w
        sin_p = np.sin(phase)
        cos_p = np.cos(phase)
        Height += A * cos_p
        GradX -= kx * A * sin_p
        GradZ -= kz * A * sin_p

    NormLen = np.sqrt(GradX**2 + 1.0 + GradZ**2)
    Nx = -GradX / NormLen
    Ny = 1.0 / NormLen
    Nz = -GradZ / NormLen

    # Distance fog (top of screen blends into distant glowing mist)
    fog = np.clip(1.0 - np.exp(-(dist - nominal_dist.min()) * 0.035), 0.0, 1.0)

    # View vector V = -RD
    Vx = -RD_x_final
    Vy = -RD_y_final
    Vz = -RD_z_final

    # Fresnel reflection term (Schlick)
    NdotV = np.clip(Nx * Vx + Ny * Vy + Nz * Vz, 0.001, 1.0)
    fresnel = 0.04 + 0.96 * np.power(1.0 - NdotV, 5.0)

    # Blinn-Phong Specular for moonlight glitter trail
    Hx = L[0] + Vx
    Hy = L[1] + Vy
    Hz = L[2] + Vz
    H_len = np.sqrt(Hx**2 + Hy**2 + Hz**2)
    Hx /= H_len
    Hy /= H_len
    Hz /= H_len

    NdotH = np.clip(Nx * Hx + Ny * Hy + Nz * Hz, 0.0, 1.0)
    spec_tight = np.power(NdotH, 64.0) * 2.2
    spec_broad = np.power(NdotH, 14.0) * 0.45
    spec = (spec_tight + spec_broad) * (1.0 - fog * 0.45)

    # Subsurface scattering in wave crests (glowing Caribbean cyan/turquoise)
    sss = np.clip((Height + 0.20) / 0.45, 0.0, 1.0) * np.clip(Vy * 1.4, 0.0, 1.0)
    sss_r = sss * 0.0
    sss_g = sss * 75.0
    sss_b = sss * 115.0

    # Ocean Base Water Colors:
    # Deep trough: Deep oceanic sapphire #030818 (3, 8, 24)
    # Body: Rich electric blue #062b54 (6, 43, 84)
    # Crests: Translucent cyan #0088aa (0, 136, 170)
    depth_val = np.clip((Height + 0.28) / 0.56, 0.0, 1.0)
    water_r = (4.0 + depth_val * 6.0) * (1.0 - fog) + 12.0 * fog
    water_g = (12.0 + depth_val * 50.0) * (1.0 - fog) + 22.0 * fog
    water_b = (28.0 + depth_val * 88.0) * (1.0 - fog) + 48.0 * fog

    # Reflected Sky & Light
    sky_refl_r = 18.0 + 38.0 * fresnel
    sky_refl_g = 30.0 + 88.0 * fresnel
    sky_refl_b = 70.0 + 175.0 * fresnel

    # Combine Ocean Color
    ocean_r = water_r * (1.0 - fresnel * 0.65) + sky_refl_r * (fresnel * 0.65) + sss_r + spec * 210.0
    ocean_g = water_g * (1.0 - fresnel * 0.65) + sky_refl_g * (fresnel * 0.65) + sss_g + spec * 245.0
    ocean_b = water_b * (1.0 - fresnel * 0.65) + sky_refl_b * (fresnel * 0.65) + sss_b + spec * 255.0

    # Subtle vignette at canvas boundaries
    vignette = np.clip(1.0 - 0.35 * ((PX / 1.0)**6 + (PY / 1.0)**4), 0.0, 1.0)
    ocean_r *= vignette
    ocean_g *= vignette
    ocean_b *= vignette

    R = np.clip(ocean_r, 0, 255).astype(np.uint8)
    G = np.clip(ocean_g, 0, 255).astype(np.uint8)
    B = np.clip(ocean_b, 0, 255).astype(np.uint8)

    frame_img = Image.fromarray(np.dstack([R, G, B]))
    draw = ImageDraw.Draw(frame_img)

    # Clean, modern Discord Nitro border
    draw.rounded_rectangle([3, 3, W - 4, H - 4], radius=16, outline=(0, 242, 254, 75), width=1)
    draw.rounded_rectangle([5, 5, W - 6, H - 6], radius=14, outline=(88, 101, 242, 40), width=1)

    # Floating Glassmorphic Profile HUD (Discord / Apple Style)
    hud_x, hud_y = 36, 26
    hud_w, hud_h = W - 72, 74

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    # Translucent frosted glass allowing the 3D water to flow completely beneath
    d_over.rounded_rectangle([hud_x, hud_y, hud_x + hud_w, hud_y + hud_h], radius=14,
                             fill=(10, 16, 28, 165), outline=(0, 242, 254, 90), width=1)
    d_over.rounded_rectangle([hud_x + 1, hud_y + 1, hud_x + hud_w - 1, hud_y + hud_h - 1], radius=13,
                             outline=(255, 255, 255, 30), width=1)
    frame_img = Image.alpha_composite(frame_img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(frame_img)

    # Pulsing Emerald Quantum Dot
    pulse = 0.75 + 0.25 * math.sin(w)
    dot_r = 4.2 * pulse
    dot_x, dot_y = hud_x + 24, hud_y + 24
    draw.ellipse([dot_x - dot_r*1.8, dot_y - dot_r*1.8, dot_x + dot_r*1.8, dot_y + dot_r*1.8],
                 fill=(87, 242, 135, int(50 * pulse)))
    draw.ellipse([dot_x - 3.5, dot_y - 3.5, dot_x + 3.5, dot_y + 3.5], fill=(87, 242, 135, 255))

    # Name Title & Subtitle with proper spacing
    draw.text((dot_x + 16, dot_y - 12), "ANANT RAJ", font=font_title, fill=(255, 255, 255, 255))
    draw.text((dot_x + 205, dot_y - 4), "• R&D SYSTEMS & HARDWARE CONTROLS", font=font_subtitle, fill=(0, 242, 254, 235))
    draw.text((dot_x + 16, dot_y + 24), "Research. Understand. Design. Implement. Test. Improve.", font=font_mono, fill=(185, 210, 240, 225))

    # Right Telemetry Pill in HUD
    tel_x = hud_x + hud_w - 240
    draw.rounded_rectangle([tel_x, hud_y + 15, tel_x + 220, hud_y + 41], radius=8,
                           fill=(16, 24, 40, 200), outline=(88, 101, 242, 110), width=1)
    draw.text((tel_x + 14, hud_y + 21), "3D FLUID VFX ENGINE // LIVE", font=font_status, fill=(87, 242, 135, 245))

    # Bottom Glassmorphic Role Pills (Fluid flows completely beneath and behind them)
    badges = [
        ("NATIVE MACOS", (0, 242, 254)),
        ("VERIPACK AUDIT", (87, 242, 135)),
        ("AI SWARM FLEET", (157, 78, 221)),
        ("IIT BOMBAY NEC", (255, 170, 0)),
        ("ROBOTICS LAB", (0, 210, 255)),
    ]
    bx = hud_x
    by = H - 44
    for b_text, b_col in badges:
        bw = len(b_text) * 7.2 + 22
        draw.rounded_rectangle([bx, by, bx + bw, by + 22], radius=6,
                               fill=(10, 16, 28, 185), outline=(*b_col, 130), width=1)
        draw.text((bx + 11, by + 4), b_text, font=font_badge, fill=(255, 255, 255, 245))
        bx += bw + 10

    return frame_img.convert("RGB")

print("Rendering 36 seamless frames of full-canvas 3D fluid water...")
t0 = time.time()
frames = []
for frame_idx in range(NUM_FRAMES):
    t = frame_idx / NUM_FRAMES
    f = render_frame(t)
    frames.append(f)

output_gif = "/Users/anantraj/anant-rajj/assets/banner-3d-water.gif"
frames[0].save(
    output_gif,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=True
)

import os
sz = os.path.getsize(output_gif)
print(f"Full-Canvas 3D Fluid Ocean successfully generated in {(time.time() - t0):.1f}s! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
