import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 900, 380
NUM_FRAMES = 36
FPS = 20

try:
    font_header = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 16)
    font_title = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 15)
    font_mono = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 11)
    font_tiny = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 9)
    font_bold = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 12)
except Exception:
    font_header = ImageFont.load_default()
    font_title = ImageFont.load_default()
    font_mono = ImageFont.load_default()
    font_tiny = ImageFont.load_default()
    font_bold = ImageFont.load_default()

frames = []

# Projects definition
cards = [
    {
        "col": 0, "row": 0,
        "title": "VeriPack // Supply Chain Auditor",
        "role": "TEAM LEAD • HACK DAY SONIPAT P04",
        "tag": "PYTHON • AST • SHANNON ENTROPY",
        "color": (87, 242, 135),  # Discord Emerald Green
        "accent": (0, 255, 136),
        "metrics": [
            ("TEST SUITE", "42/42 PASSING", (87, 242, 135)),
            ("ZIP-SLIP GUARD", "Path.relative_to", (0, 242, 254)),
            ("PROVENANCE", "QWEN 2.5 VERIFIED", (255, 215, 0))
        ]
    },
    {
        "col": 1, "row": 0,
        "title": "mac-insomnia // Power CLI",
        "role": "OPEN SOURCE • NATIVE MACOS UTILITY",
        "tag": "C / PYTHON • IOKIT • IOPM ASSERTION",
        "color": (0, 242, 254),  # Cyan
        "accent": (88, 101, 242),
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
        "accent": (255, 170, 0),
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
        "accent": (0, 242, 254),
        "metrics": [
            ("THERMOX BOTTLE", "ISOLATED CORE", (255, 170, 0)),
            ("MULTI-MODEL", "CLAUDE • ASTRA • GEMINI", (157, 78, 221)),
            ("IIT BOMBAY NEC", "ADVANCED TRACK", (87, 242, 135))
        ]
    }
]

for frame_idx in range(NUM_FRAMES):
    t = frame_idx / NUM_FRAMES
    w1 = 2 * math.pi * t
    w2 = 4 * math.pi * t

    img = Image.new("RGBA", (W, H), (11, 14, 23, 255))
    draw = ImageDraw.Draw(img)

    # Subtle background fluid grid lines (animating waves)
    for gy in range(40, H, 30):
        wave_y = gy + 3 * math.sin(w1 + gy * 0.05)
        draw.line([(0, wave_y), (W, wave_y)], fill=(18, 26, 42, 80), width=1)

    # Outer border with cyber glow
    draw.rounded_rectangle([4, 4, W - 5, H - 5], radius=16, outline=(88, 101, 242, 100), width=1)

    # Top Section Bar
    draw.rounded_rectangle([18, 14, W - 18, 44], radius=8, fill=(16, 21, 35, 230), outline=(0, 242, 254, 80), width=1)
    
    pulse_dot = 0.6 + 0.4 * math.sin(w1)
    draw.ellipse([30, 25, 38, 33], fill=(87, 242, 135, int(255 * pulse_dot)))
    draw.text((46, 21), "FEATURED SYSTEMS & HARDWARE SHOWCASE // ACTIVE TELEMETRY", font=font_mono, fill=(200, 225, 255, 240))
    
    # Animated clock/cycle indicator
    cycle_pct = int(t * 100)
    draw.text((W - 140, 21), f"CYCLE: {cycle_pct:02d}% ⟳", font=font_mono, fill=(0, 242, 254, 220))

    card_w = (W - 54) // 2
    card_h = (H - 74) // 2

    for c in cards:
        cx = 18 + c["col"] * (card_w + 18)
        cy = 56 + c["row"] * (card_h + 12)

        # Card base background
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=12,
                               fill=(15, 20, 32, 235), outline=(*c["color"], 90), width=1)

        # Animated scanline effect across each card
        scan_offset = (t + c["col"] * 0.25 + c["row"] * 0.5) % 1.0
        scan_y = cy + int(scan_offset * card_h)
        draw.line([(cx + 4, scan_y), (cx + card_w - 4, scan_y)],
                  fill=(*c["accent"], int(140 * math.sin(scan_offset * math.pi))), width=1)

        # Card Title & Role
        draw.text((cx + 14, cy + 12), c["title"], font=font_title, fill=(255, 255, 255, 255))
        draw.text((cx + 14, cy + 32), c["role"], font=font_tiny, fill=(*c["color"], 230))
        draw.text((cx + 14, cy + 46), c["tag"], font=font_tiny, fill=(140, 160, 185, 200))

        # Divider inside card
        draw.line([(cx + 14, cy + 62), (cx + card_w - 14, cy + 62)], fill=(30, 42, 65, 180), width=1)

        # Metrics display with animated mini pulse LEDs
        my = cy + 70
        for m_label, m_val, m_col in c["metrics"]:
            # Mini pulsing status LED
            led_a = int(180 + 75 * math.sin(w2 + my * 0.1))
            draw.ellipse([cx + 14, my + 3, cx + 20, my + 9], fill=(*m_col, led_a))
            draw.text((cx + 26, my), m_label, font=font_tiny, fill=(160, 180, 205, 220))
            
            # Value box right-aligned
            val_w = len(m_val) * 6.5 + 12
            vx = cx + card_w - val_w - 14
            draw.rounded_rectangle([vx, my - 2, vx + val_w, my + 13], radius=4,
                                   fill=(20, 28, 45, 220), outline=(*m_col, 100), width=1)
            draw.text((vx + 6, my), m_val, font=font_tiny, fill=(*m_col, 255))
            my += 22

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
print(f"Pinned Showcases Animated GIF created! Size: {sz / (1024*1024):.2f} MB ({sz} bytes)")
