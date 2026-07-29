from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H = 1180, 610
LEFT_W = 420

BG_DARK = "#0A101F"
CHROME_DARK = "#22D3EE"
TEXT_DARK = "#E2E8F0"
MUTED_DARK = "#64748B"
ACCENT_DARK = "#10B981"

BG_LIGHT = "#F8FAFC"
CHROME_LIGHT = "#0891B2"
TEXT_LIGHT = "#0F172A"
MUTED_LIGHT = "#475569"
ACCENT_LIGHT = "#059669"

PHOTO = "Images/Akshat.jpeg"

ROWS = [
    ("Subject", "Akshat Kardak", "text"),
    ("Role", "Full-Stack Developer", "text"),
    ("Origin", "Mumbai | India", "text"),
    ("Edu", "CS Engineering | DMCE", "text"),
    ("Status", "Building | Learning | Shipping", "chrome"),
    ("SEP", "", ""),
    ("Core.Lang", "Python | JS/TS | C++", "text"),
    ("Frontend", "React | Next.js | Tailwind", "text"),
    ("Backend", "Node.js | Express | FastAPI", "text"),
    ("Database", "MongoDB | MySQL | SQLite", "text"),
    ("Infra", "Vercel | Netlify | Git", "text"),
    ("SEP", "", ""),
    ("Mail", "kardakakshat@gmail.com", "accent"),
    ("Portfolio", "akshat-portfolio-teal.vercel.app", "accent"),
    ("LinkedIn", "in/akshatkardak", "text"),
    ("GitHub", "AkshatKardak", "text"),
]

def load_font(size, bold=False):
    candidates = []
    if bold:
        candidates += [
            "C:/Windows/Fonts/consolab.ttf",
            "C:/Windows/Fonts/lucon.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        ]
    else:
        candidates += [
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/lucon.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()

def fit_portrait(img, target_w, target_h):
    return ImageOps.fit(
        img,
        (target_w, target_h),
        method=Image.LANCZOS,
        centering=(0.50, 0.24)
    )

def add_bottom_fade(base, bg_hex):
    bg = Image.new("RGB", base.size, bg_hex)
    mask = Image.new("L", base.size, 0)
    draw = ImageDraw.Draw(mask)
    w, h = base.size
    start = int(h * 0.72)
    for y in range(h):
        alpha = 0
        if y > start:
            alpha = int(((y - start) / (h - start)) * 255)
        draw.line((0, y, w, y), fill=max(0, min(255, alpha)))
    return Image.composite(bg, base, mask)

def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def draw_rows(draw, x0, right, start_y, colors, mono13):
    y = start_y
    row_h = 23
    for label, value, kind in ROWS:
        if label == "SEP":
            draw.line((x0, y, right, y), fill=colors["muted_div"], width=1)
            y += 12
            continue
        val_color = colors["text"] if kind == "text" else colors["chrome"] if kind == "chrome" else colors["accent"]
        draw.text((x0, y), label, fill=colors["muted"], font=mono13)
        value_w = text_width(draw, value, mono13)
        value_x = right - value_w
        label_w = text_width(draw, label, mono13)
        line_start = x0 + label_w + 14
        line_end = value_x - 12
        if line_end > line_start:
            step = 8
            dot_y = y + 10
            for xx in range(line_start, line_end, step):
                draw.line((xx, dot_y, xx + 2, dot_y), fill=colors["muted_dot"], width=1)
        draw.text((value_x, y), value, fill=val_color, font=mono13)
        y += row_h

def build_banner(mode="dark", photo_path=PHOTO):
    if mode == "dark":
        colors = {
            "bg": BG_DARK,
            "chrome": CHROME_DARK,
            "text": TEXT_DARK,
            "muted": MUTED_DARK,
            "accent": ACCENT_DARK,
            "top_overlay": (255, 255, 255, 14),
            "muted_dot": "#1E293B",
            "muted_div": "#162235",
            "frame": "#0D1526",
        }
    else:
        colors = {
            "bg": BG_LIGHT,
            "chrome": CHROME_LIGHT,
            "text": TEXT_LIGHT,
            "muted": MUTED_LIGHT,
            "accent": ACCENT_LIGHT,
            "top_overlay": (255, 255, 255, 18),
            "muted_dot": "#CBD5E1",
            "muted_div": "#D8E2EC",
            "frame": "#EFF6FF",
        }

    mono10 = load_font(10)
    mono11 = load_font(11)
    mono12 = load_font(12)
    mono13 = load_font(13)
    mono13b = load_font(13, bold=True)

    canvas = Image.new("RGB", (W, H), colors["bg"])
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, W, 30), fill=colors["chrome"])
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle((0, 0, W, 30), fill=colors["top_overlay"])
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    draw.ellipse((11, 10, 21, 20), fill="#EF4444")
    draw.ellipse((27, 10, 37, 20), fill="#F59E0B")
    draw.ellipse((43, 10, 53, 20), fill=colors["accent"])
    draw.text((68, 9), "profile.sh --live", fill=colors["muted"], font=mono11)

    draw.rectangle((0, 30, LEFT_W, H), fill=colors["frame"])

    photo = Image.open(photo_path).convert("RGB")
    photo = fit_portrait(photo, LEFT_W, H)
    photo = ImageOps.autocontrast(photo, cutoff=1)
    photo = photo.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=2))
    photo = add_bottom_fade(photo, colors["bg"])
    canvas.paste(photo, (0, 0))

    draw = ImageDraw.Draw(canvas)
    draw.text((14, 14), "VISUAL.MAP", fill=colors["chrome"], font=mono10)
    draw.line((LEFT_W, 30, LEFT_W, H), fill=colors["muted_div"], width=1)

    x0 = LEFT_W + 22
    right = W - 28

    draw.text((x0, 42), "SYSTEM.INFO", fill=colors["muted"], font=mono11)
    live_text = "● LIVE"
    live_w = text_width(draw, live_text, mono12)
    draw.text((right - live_w, 42), live_text, fill="#EF4444", font=mono12)

    pill_x1, pill_y1, pill_x2, pill_y2 = x0, 58, x0 + 190, 80
    draw.rounded_rectangle((pill_x1, pill_y1, pill_x2, pill_y2), radius=11, fill=colors["chrome"])
    pill_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pod = ImageDraw.Draw(pill_overlay)
    pod.rounded_rectangle((pill_x1, pill_y1, pill_x2, pill_y2), radius=11, fill=(255, 255, 255, 180))
    canvas = Image.blend(canvas.convert("RGBA"), pill_overlay, 0.15).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    draw.text((x0 + 10, 63), "@AkshatKardak", fill=colors["chrome"], font=mono13b)

    draw_rows(draw, x0, right, 108, colors, mono13)
    return canvas

if __name__ == "__main__":
    dark = build_banner("dark")
    light = build_banner("light")
    dark.save("githubanner_dark.png", format="PNG")
    light.save("githubanner_light.png", format="PNG")
    print("Saved githubanner_dark.png and githubanner_light.png")