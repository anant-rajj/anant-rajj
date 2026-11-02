import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 900, 360
NUM_FRAMES = 36
FPS = 20

try:
    font_header = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 15)
    font_title = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 15)
    font_mono = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 11)
    font_tiny = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 10)
    font_bold = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 12)
except Exception:
    font_header = ImageFont.load_default()
    font_title = ImageFont.load_default()
    font_mono = ImageFont.load_default()
    font_tiny = ImageFont.load_default()
    font_bold = ImageFont.load_default()

cards = [
    {
        "col": 0, "row": 0,
        "title": "VeriPack // Supply Chain Auditor",
        "role": "TEAM LEAD • HACK DAY SONIPAT P04",
        "tag": "PYTHON • AST • SHANNON ENTROPY",
        "color": (87, 242, 135),  # Emerald
        "metrics": [
            ("TEST SUITE", "42/42 PASSING", (87, 242, 135)),
            ("ZIP-SLIP DEFENSE", "Path.relative_to", (0, 242, 254)),
            ("PROVENANCE", "QWEN 2.5 VERIFIED", (255, 215, 0))
        ]
    },
    {
        "col": 1, "row": 0,
        "title": "mac-insomnia // Power CLI",
        "role": "OPEN SOURCE • NATIVE MACOS UTILITY",
        "tag": "IOKIT • IOPM ASSERTION • ZERO OVERHEAD",
        "color": (0, 242, 254),  # Cyan
        "metrics": [
            ("BINARY SIZE", "~24 KB DISK", (0, 242, 254)),
            ("MEMORY RSS", "< 8.0 MB RAM", (87, 242, 135)),
            ("DAEMON", "LID-CLOSED ACTIVE", (255, 170, 0))
        ]
    },
    {
        "col": 0, "row": 1,
        "title": "mac-lumitrack & keyglow",
        "role": "HARDWARE INTERACTION LAB",
        "tag": "PURE C / OBJ-C • SWIFT • MULTITOUCH",
        "color": (255, 107, 107),  # Coral
        "metrics": [
            ("LUMITRACK BIN", "~50 KB // 3.5MB RAM", (255, 107, 107)),
            ("KEYGLOW ENGINE", "45-60 FPS HARDWARE", (0, 242, 254)),
            ("CPU OVERHEAD", "< 0.2% IDLE", (87, 242, 135))
        ]
    },
    {
        "col": 1, "row": 1,
        "title": "ThermoX & Swarm Fleet",
        "role": "MODULAR HARDWARE & MULTI-AGENT DAG",
        "tag": "THERMAL CARTRIDGE • 6 DEPT SWARM",
        "color": (157, 78, 221),  # Violet
        "metrics": [
            ("THERMOX BOTTLE", "ISOLATED CORE", (255, 170, 0)),
            ("MULTI-MODEL", "CLAUDE • ASTRA • GEMINI", (157, 78, 221)),
            ("IIT BOMBAY NEC", "ADVANCED TRACK", (87, 242, 135))
        ]
    }
]

frames = []

for frame_idx in range(NUM_FRAMES):
    t = frame_idx / NUM_FRAMES
    w = 2 * math.pi * t

    img = Image.new("RGBA", (W, H), (11, 14, 23, 255))
    draw = ImageDraw.Draw(img)

    # Clean, subtle 3D card border
    draw.rounded_rectangle([3, 3, W - 4, H - 4], radius=16, outline=(88, 101, 242, 70), width=1)

    # Top Section Bar (Calm, steady, no strobing)
    draw.rounded_rectangle([18, 14, W - 18, 44], radius=8, fill=(15, 20, 32, 240), outline=(0, 242, 254, 60), width=1)
    
    # Gentle, slow pulse on status dot (serene breath, not strobe)
    pulse = 0.75 + 0.25 * math.sin(w)
    draw.ellipse([30, 25, 38, 33], fill=(87, 242, 135, int(255 * pulse)))
    draw.text((46, 21), "FEATURED SYSTEMS & HARDWARE SHOWCASE // VERIFIED TELEMETRY", font=font_mono, fill=(210, 230, 255, 240))
    draw.text((W - 130, 21), "STATUS: 100% OK", font=font_mono, fill=(87, 242, 135, 220))

    card_w = (W - 54) // 2
    card_h = (H - 74) // 2

    for c in cards:
        cx = 18 + c["col"] * (card_w + 18)
        cy = 54 + c["row"] * (card_h + 10)

        # 3D Glass Card Base with subtle bevel and depth
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=12,
                               fill=(14, 18, 30, 245), outline=(*c["color"], 70), width=1)
        # Inner subtle top bevel highlight
        draw.line([(cx + 12, cy + 1), (cx + card_w - 12, cy + 1)], fill=(255, 255, 255, 20), width=1)

        # Title & Role (Crisp, steady, zero distortion)
        draw.text((cx + 16, cy + 12), c["title"], font=font_title, fill=(255, 255, 255, 255))
        draw.text((cx + 16, cy + 32), c["role"], font=font_tiny, fill=(*c["color"], 230))
        draw.text((cx + 16, cy + 46), c["tag"], font=font_tiny, fill=(140, 160, 185, 200))

        # Thin clean separator line
        draw.line([(cx + 16, cy + 62), (cx + card_w - 16, cy + 62)], fill=(25, 35, 55, 200), width=1)

        # Metrics display with calm, elegant LED indicator
        my = cy + 70
        for m_label, m_val, m_col in c["metrics"]:
            # Gentle breathing LED
            led_a = int(190 + 55 * math.sin(w + my * 0.05))
            draw.ellipse([cx + 16, my + 3, cx + 22, my + 9], fill=(*m_col, led_a))
            draw.text((cx + 28, my), m_label, font=font_tiny, fill=(165, 185, 210, 225))

            # Value pill
            val_w = len(m_val) * 6.5 + 12
            vx = cx + card_w - val_w - 16
            draw.rounded_rectangle([vx, my - 2, vx + val_w, my + 13], radius=4,
                                   fill=(20, 27, 44, 230), outline=(*m_col, 80), width=1)
            draw.text((vx + 6, my), m_val, font=font_tiny, fill=(*m_col, 255))
            my += 21

    frames.append(img.convert("RGB"))

output_showcase = "/Users/anantraj/anant-rajj/assets/pinned-showcases.gif"
frames[0].save(
    output_showcase,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000 / FPS),
    loop=0,
    optimize=True
)

import os
sz = os.path.getsize(output_showcase)
print(f"Pinned Showcases GIF created! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
