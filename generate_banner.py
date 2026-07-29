#!/usr/bin/env python3
"""
GitHub Profile Banner Generator
Reads Images/Akshat.jpeg → produces Images/githubanner_dark.png + Images/githubanner_light.png

Install deps:  pip install Pillow
Run:           python generate_banner.py
"""
import os
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont

W, H = 1180, 610
LEFT_W = int(W * 0.38)
PORTRAIT_W = LEFT_W - 16
PORTRAIT_H = H - 60

COL_BG_DARK    = (10, 16, 31)
COL_BG_LIGHT   = (245, 245, 250)
COL_PORT_DARK  = (167, 139, 250)
COL_PORT_LIGHT = (124, 58, 237)
COL_CHROME     = (34, 211, 238)
COL_CHROME2    = (8, 145, 178)


def prep_portrait():
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images", "Akshat.jpeg")
    src = Image.open(src_path).convert("RGB")
    # Top-anchored cover crop – keeps head + shoulders visible
    crop_h = int(src.height * 0.70)
    crop_w = int(crop_h * PORTRAIT_W / PORTRAIT_H)
    x0 = (src.width - crop_w) // 2
    cropped = src.crop((x0, 0, x0 + crop_w, crop_h))
    portrait = cropped.resize((PORTRAIT_W, PORTRAIT_H), Image.LANCZOS)
    portrait = ImageEnhance.Contrast(portrait).enhance(1.3)
    portrait = portrait.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=3))
    return portrait


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def build_banner(portrait_rgb, dark=True):
    bg_col     = COL_BG_DARK if dark else COL_BG_LIGHT
    frame_col  = COL_PORT_DARK if dark else COL_PORT_LIGHT
    text_col   = (220, 220, 235) if dark else (20, 20, 40)
    muted_col  = (120, 120, 160) if dark else (100, 100, 130)
    chrome     = COL_CHROME if dark else COL_CHROME2
    border_col = (40, 50, 80) if dark else (200, 195, 230)

    MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    MONO_R = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    f_title = _font(MONO_B, 13)
    f_sm    = _font(MONO_R, 12)
    f_lbl   = _font(MONO_B, 11)
    f_val   = _font(MONO_R, 11)
    f_big   = _font(MONO_B, 15)
    f_xs    = _font(MONO_R, 10)

    canvas = Image.new("RGB", (W, H), bg_col)
    draw   = ImageDraw.Draw(canvas)

    # Outer terminal border
    draw.rounded_rectangle([4, 4, W-4, H-4], radius=12, outline=border_col, width=2)

    # Title bar
    bar_h = 36
    draw.rounded_rectangle([5, 5, W-5, bar_h+5], radius=10, fill=border_col)
    for i, c in enumerate([(239,68,68), (251,191,36), (34,197,94)]):
        draw.ellipse([18+i*22, 14, 32+i*22, 28], fill=c)
    title_text = "profile.sh --live"
    tw = draw.textlength(title_text, font=f_title)
    draw.text(((W - tw) / 2, 12), title_text, fill=text_col, font=f_title)

    panel_y0, panel_y1 = bar_h + 10, H - 10

    # Left panel
    draw.rectangle([8, panel_y0, LEFT_W-4, panel_y1],
                   fill=((18, 24, 45) if dark else (235, 230, 250)))
    draw.text((18, panel_y0+10), "VISUAL.MAP", fill=frame_col, font=f_lbl)

    pw_avail = LEFT_W - 16
    ph_avail = panel_y1 - (panel_y0 + 32) - 32
    pw_fit   = min(PORTRAIT_W, pw_avail)
    ph_fit   = min(PORTRAIT_H, ph_avail)
    portrait_fit = portrait_rgb.resize((pw_fit, ph_fit), Image.LANCZOS)
    px = 8 + (pw_avail - pw_fit) // 2
    py = panel_y0 + 32

    draw.rectangle([px-3, py-3, px+pw_fit+3, py+ph_fit+3], outline=frame_col, width=2)
    draw.rectangle([px-1, py-1, px+pw_fit+1, py+ph_fit+1], outline=muted_col, width=1)
    canvas.paste(portrait_fit, (px, py))

    handle_txt = "@AkshatKardak"
    pill_w = int(draw.textlength(handle_txt, font=f_sm)) + 20
    pill_x = 8 + (pw_avail - pill_w) // 2
    pill_y = py + ph_fit + 8
    if pill_y + 22 < panel_y1:
        draw.rounded_rectangle([pill_x, pill_y, pill_x+pill_w, pill_y+20],
                                radius=10, fill=frame_col)
        draw.text((pill_x+10, pill_y+4), handle_txt, fill=(255, 255, 255), font=f_xs)

    # Right panel
    rx0 = LEFT_W + 4
    draw.rectangle([rx0, panel_y0, W-8, panel_y1],
                   fill=((13, 20, 38) if dark else (250, 248, 255)))
    draw.text((rx0+14, panel_y0+8), "SYSTEM.INFO", fill=chrome, font=f_big)

    # LIVE badge
    live_x = W - 80
    draw.rounded_rectangle([live_x, panel_y0+8, live_x+56, panel_y0+26], radius=9, fill=(239,68,68))
    draw.text((live_x+6, panel_y0+11), "\u25cf LIVE", fill=(255, 255, 255), font=f_xs)
    draw.line([rx0+14, panel_y0+34, W-14, panel_y0+34], fill=border_col, width=1)

    rows = [
        ("Subject",   "Akshat Kardak"),
        ("Role",      "Full-Stack Developer"),
        ("Origin",    "Mumbai, India"),
        ("Education", "DMCE / CS Engineering"),
        ("Status",    "Building \u00b7 Learning \u00b7 Shipping"),
        ("ToolChain", "VS Code \u00b7 Git \u00b7 Arduino \u00b7 ESP-IDF"),
        ("Languages", "Python \u00b7 JS/TS \u00b7 C++"),
        ("Frontend",  "React \u00b7 Next.js \u00b7 Tailwind"),
        ("Backend",   "Node.js \u00b7 Express \u00b7 FastAPI"),
        ("Database",  "MongoDB \u00b7 MySQL \u00b7 SQLite"),
        ("Infra",     "Vercel \u00b7 Netlify \u00b7 Render"),
        ("GitHub",    "github.com/AkshatKardak"),
        ("LinkedIn",  "linkedin.com/in/akshatkardak"),
    ]

    row_x = rx0 + 14
    row_y = panel_y0 + 44
    row_h = 33
    max_lbl_w = 72

    for label, value in rows:
        if row_y + row_h > panel_y1 - 6:
            break
        draw.text((row_x, row_y+2), label, fill=muted_col, font=f_lbl)
        lbl_end   = row_x + max_lbl_w
        val_start = W - 14 - int(draw.textlength(value, font=f_val))
        dot_x = lbl_end + 4
        while dot_x + 4 < val_start - 4:
            draw.ellipse([dot_x, row_y+8, dot_x+2, row_y+10], fill=muted_col)
            dot_x += 7
        val_color = chrome if label in ("Role", "Status") else text_col
        draw.text((val_start, row_y+2), value, fill=val_color, font=f_val)
        draw.line([row_x, row_y+row_h-2, W-14, row_y+row_h-2], fill=border_col, width=1)
        row_y += row_h

    return canvas


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images")
    os.makedirs(out_dir, exist_ok=True)
    portrait = prep_portrait()
    build_banner(portrait, dark=True ).save(os.path.join(out_dir, "githubanner_dark.png"),  optimize=True)
    build_banner(portrait, dark=False).save(os.path.join(out_dir, "githubanner_light.png"), optimize=True)
    print("\u2705 Banners generated:")
    print("   Images/githubanner_dark.png")
    print("   Images/githubanner_light.png")
