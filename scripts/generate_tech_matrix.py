import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 900, 160
NUM_FRAMES = 36
FPS = 20

try:
    font_mono = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 10)
    font_bold = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 12)
    font_header = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 13)
except Exception:
    font_mono = ImageFont.load_default()
    font_bold = ImageFont.load_default()
    font_header = ImageFont.load_default()

techs = [
    ("C / OBJECTIVE-C", "CoreBrightness • Multitouch", (0, 242, 254)),
    ("SWIFT", "Hardware Loop • Bezel HUD", (255, 107, 107)),
    ("PYTHON 3.12", "AST • Entropy • Tarball Guard", (87, 242, 135)),
    ("IOKIT / IOPM", "Kernel Power Assertions", (255, 170, 0)),
    ("AI SWARM FLEET", "Triad Debate • DAG Orchestrator", (157, 78, 221)),
    ("ROBOTICS & PWM", "Servo Kinematics • Microcontrollers", (0, 210, 255)),
    ("SECURITY AUDIT", "Zip-Slip Defense • Static Rules", (87, 242, 135)),
    ("ARM64 ASSEMBLY", "Apple Silicon M-Series Optimizations", (255, 215, 0))
]

frames = []

for frame_idx in range(NUM_FRAMES):
    t = frame_idx / NUM_FRAMES
    w1 = 2 * math.pi * t

    img = Image.new("RGBA", (W, H), (11, 14, 23, 255))
    draw = ImageDraw.Draw(img)

    # Frame border
    draw.rounded_rectangle([4, 4, W - 5, H - 5], radius=14, outline=(88, 101, 242, 90), width=1)

    # Header
    pulse_dot = 0.6 + 0.4 * math.sin(w1)
    draw.ellipse([20, 16, 26, 22], fill=(0, 242, 254, int(255 * pulse_dot)))
    draw.text((34, 13), "3D SYSTEMS CAPABILITY MATRIX // LOW-LEVEL & AI ARCHITECTURE", font=font_header, fill=(220, 235, 255, 250))
    
    # 2 rows of 4 columns
    cols = 4
    chip_w = (W - 36 - 3 * 12) // cols
    chip_h = 44

    for idx, (name, desc, col) in enumerate(techs):
        r = idx // cols
        c = idx % cols
        cx = 18 + c * (chip_w + 12)
        cy = 40 + r * (chip_h + 10)

        # Wave shimmer offset per chip
        shimmer = (t + idx * 0.12) % 1.0
        shimmer_glow = int(120 + 80 * math.sin(shimmer * 2 * math.pi))

        draw.rounded_rectangle([cx, cy, cx + chip_w, cy + chip_h], radius=8,
                               fill=(16, 22, 36, 220), outline=(*col, shimmer_glow), width=1)

        # Mini accent indicator line
        draw.line([(cx + 8, cy + chip_h - 4), (cx + 36, cy + chip_h - 4)], fill=(*col, 220), width=2)

        draw.text((cx + 10, cy + 7), name, font=font_bold, fill=(255, 255, 255, 255))
        draw.text((cx + 10, cy + 24), desc, font=font_mono, fill=(150, 175, 205, 210))

    frames.append(img.convert("RGB"))

output_matrix = "/Users/anantraj/anant-rajj/assets/tech-matrix-animated.gif"
frames[0].save(
    output_matrix,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=True
)

import os
sz = os.path.getsize(output_matrix)
print(f"Tech Matrix Animated GIF created! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
