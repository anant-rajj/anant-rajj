import math
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 900, 310
NUM_FRAMES = 36  # Seamless loop
FPS = 20

# System Fonts
try:
    font_title = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 30)
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

# Camera & Projection
fov = 1.05
pitch = -0.17  # Tilted downward towards water
cam_height = 2.3

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

# Moonlight Key Light (soft moon on horizon)
L = np.array([0.05, 0.20, 0.98])
L = L / np.linalg.norm(L)

horizon_val = -0.010
is_ocean = RD_y_final < horizon_val
is_sky = ~is_ocean

nominal_dist = np.zeros_like(RD_y_final)
nominal_dist[is_ocean] = -cam_height / RD_y_final[is_ocean]

# Background stars
np.random.seed(42)
num_stars = 60
star_x = np.random.uniform(20, W - 20, num_stars)
star_y = np.random.uniform(8, H * 0.36, num_stars)
star_bright = np.random.uniform(130, 230, num_stars)

# Gerstner Waves: Calm, smooth, rolling oceanic swells (NO spiky harmonics)
gerstner_waves = [
    (0.38, 0.72, 0.16, 1),   # Primary rolling swell
    (-0.58, 0.62, 0.11, 1),  # Counter swell
    (0.80, 1.10, 0.055, 2),  # Cross wave
    (-1.10, 0.75, 0.040, 2), # Cross wave 2
    (1.60, 2.20, 0.018, 3),  # Gentle surface ripple
    (-2.20, 1.50, 0.012, 3), # Gentle surface ripple 2
]

frames = []
t0 = time.time()

for frame_idx in range(NUM_FRAMES):
    t = frame_idx / NUM_FRAMES
    w = 2 * math.pi * t

    # 1. World Intersection & Wave Height
    dist = nominal_dist.copy()
    WX = dist * RD_x_final
    WZ = dist * RD_z_final

    # 2-step geometric refinement
    H_est = np.zeros_like(WX)
    for kx, kz, A, speed in gerstner_waves:
        phase = kx * WX + kz * WZ - speed * w
        H_est += A * np.cos(phase)

    dist[is_ocean] = -(cam_height - H_est[is_ocean] * 0.85) / RD_y_final[is_ocean]
    dist = np.clip(dist, 1.0, 160.0)
    WX = dist * RD_x_final
    WZ = dist * RD_z_final

    # Compute surface height and analytical normals
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

    # Atmospheric distance fog
    fog = np.clip(1.0 - np.exp(-dist * 0.024), 0.0, 1.0)

    # View vector towards camera
    Vx = -RD_x_final
    Vy = -RD_y_final
    Vz = -RD_z_final

    # Fresnel reflection (Schlick)
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
    spec_tight = np.power(NdotH, 64.0) * 2.0
    spec_broad = np.power(NdotH, 14.0) * 0.4
    spec = (spec_tight + spec_broad) * (1.0 - fog * 0.55)

    # Subsurface scattering in crests
    sss = np.clip((Height + 0.14) / 0.32, 0.0, 1.0) * np.clip(Vy * 1.4, 0.0, 1.0)
    sss_r = sss * 0.0
    sss_g = sss * 65.0
    sss_b = sss * 95.0

    # Ocean Base Water Colors: Deep sapphire midnight navy with subtle cyan undertones
    depth_val = np.clip((Height + 0.22) / 0.44, 0.0, 1.0)
    water_r = (5.0 + depth_val * 6.0) * (1.0 - fog) + 12.0 * fog
    water_g = (12.0 + depth_val * 42.0) * (1.0 - fog) + 20.0 * fog
    water_b = (28.0 + depth_val * 75.0) * (1.0 - fog) + 42.0 * fog

    # Reflected Sky & Light
    sky_refl_r = 16.0 + 35.0 * fresnel
    sky_refl_g = 26.0 + 80.0 * fresnel
    sky_refl_b = 60.0 + 165.0 * fresnel

    ocean_r = np.clip(water_r * (1.0 - fresnel * 0.65) + sky_refl_r * (fresnel * 0.65) + sss_r + spec * 200.0, 0, 255)
    ocean_g = np.clip(water_g * (1.0 - fresnel * 0.65) + sky_refl_g * (fresnel * 0.65) + sss_g + spec * 235.0, 0, 255)
    ocean_b = np.clip(water_b * (1.0 - fresnel * 0.65) + sky_refl_b * (fresnel * 0.65) + sss_b + spec * 250.0, 0, 255)

    # 2. Sky Rendering (Deep twilight starry sky with moon halo)
    sky_factor = np.clip((PY + 0.10) / 1.10, 0.0, 1.0)
    sky_r = 8.0 + sky_factor * 8.0
    sky_g = 12.0 + sky_factor * 12.0
    sky_b = 26.0 + sky_factor * 30.0

    moon_dx = PX - 0.05
    moon_dy = PY - 0.17
    moon_d = np.sqrt(moon_dx**2 + moon_dy**2)
    moon_halo = np.clip(np.exp(-moon_d * 4.0), 0.0, 1.0)
    moon_core = np.clip(np.exp(-moon_d * 36.0), 0.0, 1.0)

    sky_r = np.clip(sky_r + moon_halo * 35.0 + moon_core * 180.0, 0, 255)
    sky_g = np.clip(sky_g + moon_halo * 60.0 + moon_core * 205.0, 0, 255)
    sky_b = np.clip(sky_b + moon_halo * 105.0 + moon_core * 235.0, 0, 255)

    # Assemble Frame
    R = np.where(is_ocean, ocean_r, sky_r).astype(np.uint8)
    G = np.where(is_ocean, ocean_g, sky_g).astype(np.uint8)
    B = np.where(is_ocean, ocean_b, sky_b).astype(np.uint8)

    frame_img = Image.fromarray(np.dstack([R, G, B]))
    draw = ImageDraw.Draw(frame_img)

    # Star twinkle
    for sx, sy, sb in zip(star_x, star_y, star_bright):
        twinkle = 0.75 + 0.25 * math.sin(w + sx * 0.12)
        val = int(sb * twinkle)
        draw.point((int(sx), int(sy)), fill=(val, val, min(255, int(val * 1.15))))

    # Outer Border
    draw.rounded_rectangle([3, 3, W - 4, H - 4], radius=16, outline=(0, 242, 254, 75), width=1)
    draw.rounded_rectangle([5, 5, W - 6, H - 6], radius=14, outline=(88, 101, 242, 40), width=1)

    # Top Glassmorphic HUD Pill
    hud_x, hud_y = 32, 22
    hud_w, hud_h = W - 64, 72

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    d_over.rounded_rectangle([hud_x, hud_y, hud_x + hud_w, hud_y + hud_h], radius=14,
                             fill=(10, 15, 26, 175), outline=(0, 242, 254, 80), width=1)
    frame_img = Image.alpha_composite(frame_img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(frame_img)

    # Pulsing Emerald Online Dot
    pulse = 0.75 + 0.25 * math.sin(w)
    dot_r = 4.2 * pulse
    dot_x, dot_y = hud_x + 22, hud_y + 23
    draw.ellipse([dot_x - dot_r*1.8, dot_y - dot_r*1.8, dot_x + dot_r*1.8, dot_y + dot_r*1.8],
                 fill=(87, 242, 135, int(50 * pulse)))
    draw.ellipse([dot_x - 3.5, dot_y - 3.5, dot_x + 3.5, dot_y + 3.5], fill=(87, 242, 135, 255))

    # Name Title & Subtitle with proper spacing
    draw.text((dot_x + 16, dot_y - 12), "ANANT RAJ", font=font_title, fill=(255, 255, 255, 255))
    draw.text((dot_x + 195, dot_y - 4), "• R&D SYSTEMS & HARDWARE CONTROLS", font=font_subtitle, fill=(0, 242, 254, 235))
    draw.text((dot_x + 16, dot_y + 23), "Research. Understand. Design. Implement. Test. Improve.", font=font_mono, fill=(180, 205, 235, 220))

    # Right Telemetry Pill
    tel_x = hud_x + hud_w - 235
    draw.rounded_rectangle([tel_x, hud_y + 14, tel_x + 215, hud_y + 40], radius=8,
                           fill=(16, 24, 40, 210), outline=(88, 101, 242, 110), width=1)
    draw.text((tel_x + 14, hud_y + 20), "3D OCEAN TELEMETRY // VERIFIED", font=font_status, fill=(87, 242, 135, 245))

    # Bottom Glassmorphic Role Pills
    badges = [
        ("NATIVE MACOS", (0, 242, 254)),
        ("VERIPACK AUDIT", (87, 242, 135)),
        ("AI SWARM FLEET", (157, 78, 221)),
        ("IIT BOMBAY NEC", (255, 170, 0)),
        ("ROBOTICS LAB", (0, 210, 255)),
    ]
    bx = hud_x
    by = H - 42
    for b_text, b_col in badges:
        bw = len(b_text) * 7.2 + 22
        draw.rounded_rectangle([bx, by, bx + bw, by + 22], radius=6,
                               fill=(10, 16, 28, 195), outline=(*b_col, 130), width=1)
        draw.text((bx + 11, by + 4), b_text, font=font_badge, fill=(255, 255, 255, 245))
        bx += bw + 10

    frames.append(frame_img.convert("RGB"))

print("Rendering 36 frames of 3D photorealistic ocean...")
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
print(f"Photorealistic 3D Ocean GIF successfully created in {(time.time() - t0):.1f}s! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
