import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps

# Set dimensions for high-res banner
W, H = 1200, 540

# Color Palette (GitSkins Cyber Dark Glassmorphism)
BG_DARK      = (8, 12, 20)        # #080C14
CARD_BG      = (15, 23, 42)       # #0F172A
CARD_BORDER  = (30, 41, 59)       # #1E293B
TEXT_MAIN    = (248, 250, 252)    # #F8FAFC
TEXT_MUTED   = (148, 163, 184)    # #94A3B8
CYAN_ACCENT  = (34, 211, 238)     # #22D3EE
PURPLE_ACCENT= (168, 85, 247)     # #A855F7
GREEN_ACCENT = (16, 185, 129)     # #10B981
PILL_BG      = (30, 41, 59, 180)  # semi-transparent slate

def load_font(size, bold=False):
    candidates = []
    if bold:
        candidates += [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/consolab.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        ]
    else:
        candidates += [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/consola.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_radial_glow(draw_img):
    # Add subtle gradient ambient glows behind card (downsampled for fast blur)
    w_small, h_small = W // 4, H // 4
    glow = Image.new("RGBA", (w_small, h_small), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    
    # Cyan top-left glow
    gdraw.ellipse((-25, -25, 125, 125), fill=(34, 211, 238, 35))
    # Purple bottom-right glow
    gdraw.ellipse((w_small-100, h_small-100, w_small+25, h_small+25), fill=(168, 85, 247, 30))
    
    glow = glow.filter(ImageFilter.GaussianBlur(15))
    glow = glow.resize((W, H), Image.BILINEAR)
    return Image.alpha_composite(draw_img.convert("RGBA"), glow)

def fit_avatar(photo_path, target_w, target_h):
    src = Image.open(photo_path).convert("RGB")
    # Top-anchored crop for headshot
    crop_h = int(src.height * 0.75)
    crop_w = int(crop_h * target_w / target_h)
    x0 = max(0, (src.width - crop_w) // 2)
    cropped = src.crop((x0, 0, x0 + crop_w, crop_h))
    resized = cropped.resize((target_w, target_h), Image.LANCZOS)
    resized = ImageEnhance.Contrast(resized).enhance(1.15)
    resized = ImageEnhance.Sharpness(resized).enhance(1.3)
    return resized

def generate_banner():
    # Base Image
    base = Image.new("RGBA", (W, H), BG_DARK + (255,))
    base = draw_radial_glow(base)
    
    # Main Container Box
    margin_x, margin_y = 30, 30
    card_w, card_h = W - 2*margin_x, H - 2*margin_y
    card_x1, card_y1 = margin_x, margin_y
    card_x2, card_y2 = card_x1 + card_w, card_y1 + card_h
    
    # Draw Glassmorphism Card
    card_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(card_layer)
    cdraw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=16, fill=CARD_BG + (230,), outline=CARD_BORDER + (255,), width=2)
    
    # IDE Header Bar
    bar_h = 42
    header_y2 = card_y1 + bar_h
    cdraw.rounded_rectangle([card_x1, card_y1, card_x2, header_y2], radius=16, fill=(15, 23, 42, 255))
    # Fill bottom corners of top header bar so it fits nicely
    cdraw.rectangle([card_x1, header_y2 - 12, card_x2, header_y2], fill=(15, 23, 42, 255))
    cdraw.line([card_x1, header_y2, card_x2, header_y2], fill=CARD_BORDER + (255,), width=1)
    
    # macOS Window Dots
    dots_x = card_x1 + 20
    dot_y = card_y1 + 15
    cdraw.ellipse([dots_x, dot_y, dots_x+12, dot_y+12], fill=(239, 68, 68))    # Red
    cdraw.ellipse([dots_x+20, dot_y, dots_x+32, dot_y+12], fill=(245, 158, 11))  # Yellow
    cdraw.ellipse([dots_x+40, dot_y, dots_x+52, dot_y+12], fill=(34, 197, 94))   # Green
    
    # Header Title Text
    f_mono12 = load_font(12, bold=False)
    f_mono13_bold = load_font(13, bold=True)
    header_title = "akshat.dev — profile.sh"
    cdraw.text((dots_x + 70, card_y1 + 12), header_title, fill=TEXT_MUTED + (255,), font=f_mono12)
    
    # LIVE badge in header
    live_w, live_h = 70, 22
    live_x = card_x2 - live_w - 20
    live_y = card_y1 + 10
    cdraw.rounded_rectangle([live_x, live_y, live_x+live_w, live_y+live_h], radius=11, fill=(239, 68, 68, 40), outline=(239, 68, 68, 200), width=1)
    cdraw.text((live_x + 12, live_y + 3), "* LIVE", fill=(248, 113, 113, 255), font=f_mono12)
    
    # Composite card layer onto base
    base = Image.alpha_composite(base, card_layer)
    draw = ImageDraw.Draw(base)
    
    # Left Avatar Section
    photo_path = os.path.join("Images", "Akshat.jpeg")
    avatar_w, avatar_h = 240, 310
    avatar_x = card_x1 + 35
    avatar_y = header_y2 + 35
    
    if os.path.exists(photo_path):
        avatar = fit_avatar(photo_path, avatar_w, avatar_h)
        # Create rounded avatar mask
        mask = Image.new("L", (avatar_w, avatar_h), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([0, 0, avatar_w, avatar_h], radius=16, fill=255)
        
        # Border Glow around avatar
        avatar_frame = Image.new("RGBA", (avatar_w+8, avatar_h+8), (0, 0, 0, 0))
        afdraw = ImageDraw.Draw(avatar_frame)
        afdraw.rounded_rectangle([0, 0, avatar_w+8, avatar_h+8], radius=20, outline=CYAN_ACCENT + (200,), width=3)
        base.paste(avatar_frame, (avatar_x-4, avatar_y-4), avatar_frame)
        
        # Paste avatar
        base.paste(avatar, (avatar_x, avatar_y), mask)
    
    # Handle Pill below Avatar
    handle_txt = "@AkshatKardak"
    f_handle = load_font(13, bold=True)
    pill_w = 140
    pill_x = avatar_x + (avatar_w - pill_w) // 2
    pill_y = avatar_y + avatar_h - 18
    
    pill_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(pill_layer)
    pdraw.rounded_rectangle([pill_x, pill_y, pill_x+pill_w, pill_y+28], radius=14, fill=(15, 23, 42, 240), outline=CYAN_ACCENT + (255,), width=2)
    pdraw.text((pill_x + 18, pill_y + 5), handle_txt, fill=CYAN_ACCENT + (255,), font=f_handle)
    base = Image.alpha_composite(base, pill_layer)
    draw = ImageDraw.Draw(base)
    
    # Right Main Content Section
    content_x = avatar_x + avatar_w + 45
    content_y = header_y2 + 30
    
    # Title: Akshat Kardak
    f_title = load_font(34, bold=True)
    draw.text((content_x, content_y), "Akshat Kardak", fill=TEXT_MAIN + (255,), font=f_title)
    
    # Subtitle (EXACT STRING AS REQUESTED)
    f_sub = load_font(17, bold=True)
    sub_y = content_y + 48
    draw.text((content_x, sub_y), "Full Stack Developer  |  MERN Stack  |  Mumbai, India", fill=CYAN_ACCENT + (255,), font=f_sub)
    
    # Status / Tagline Pill
    f_tag = load_font(13, bold=False)
    tag_y = sub_y + 36
    draw.rounded_rectangle([content_x, tag_y, content_x+480, tag_y+28], radius=8, fill=(30, 41, 59, 180), outline=(51, 65, 85, 255), width=1)
    draw.text((content_x + 12, tag_y + 5), "Building Scalable Web Apps & AI SaaS Platforms", fill=(226, 232, 240, 255), font=f_tag)
    
    # Separator Line
    sep_y = tag_y + 44
    draw.line([content_x, sep_y, card_x2 - 35, sep_y], fill=(30, 41, 59, 255), width=1)
    
    # Tech Stack Pills Row
    tech_y = sep_y + 16
    f_tech = load_font(12, bold=True)
    techs = [
        ("React", (97, 218, 251)),
        ("Next.js", (255, 255, 255)),
        ("Node.js", (104, 160, 99)),
        ("FastAPI", (0, 150, 136)),
        ("Python", (55, 118, 171)),
        ("MongoDB", (77, 179, 61)),
        ("TypeScript", (49, 120, 198)),
    ]
    curr_x = content_x
    for tech_name, tech_col in techs:
        bbox = draw.textbbox((0, 0), tech_name, font=f_tech)
        tw = bbox[2] - bbox[0]
        pw = tw + 22
        draw.rounded_rectangle([curr_x, tech_y, curr_x+pw, tech_y+26], radius=13, fill=(30, 41, 59, 200), outline=tech_col + (180,), width=1)
        draw.text((curr_x + 11, tech_y + 4), tech_name, fill=tech_col + (255,), font=f_tech)
        curr_x += pw + 10
        
    # Quick Spec Rows (Grid style)
    specs_y = tech_y + 44
    f_lbl = load_font(12, bold=True)
    f_val = load_font(12, bold=False)
    
    specs = [
        ("Education", "B.E. Computer Science — DMCE, Navi Mumbai"),
        ("Experience", "Web Dev Intern @ Mastek Ltd. & Employment Express"),
        ("Projects", "RentRide (AI Rental), PaisaMind (Finance OS), UnitedImpact"),
        ("Focus", "Full-Stack Architecture · System Design · Practical AI"),
    ]
    
    r_y = specs_y
    for label, val in specs:
        draw.text((content_x, r_y), label, fill=PURPLE_ACCENT + (255,), font=f_lbl)
        draw.text((content_x + 110, r_y), "→  " + val, fill=TEXT_MUTED + (255,), font=f_val)
        r_y += 24
        
    # Save output
    out_dir = "Images"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "githubanner_gitskins.png")
    base.convert("RGB").save(out_path, format="PNG", optimize=True)
    print("SUCCESS: Banner created at " + out_path)

if __name__ == "__main__":
    generate_banner()
