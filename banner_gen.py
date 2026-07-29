from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
from scipy import ndimage
import os, random

os.makedirs("output", exist_ok=True)
img = Image.open("images/Akshat.jpeg").convert("RGB")
w, h = img.size

# Crop head+shoulders
portrait_raw = img.crop((int(w*0.1), 0, int(w*0.9), int(h*0.72)))
portrait_raw = portrait_raw.resize((300, 340), Image.LANCZOS)
portrait_raw = ImageOps.autocontrast(portrait_raw, cutoff=1)
portrait_raw = ImageEnhance.Contrast(portrait_raw).enhance(1.3)
portrait_raw = portrait_raw.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
portrait_gray = portrait_raw.convert("L")

# Background segmentation
rgb = np.array(portrait_raw)
bg_ref = rgb[:20, :20].mean(axis=(0, 1))
diff = np.sqrt(np.sum((rgb.astype(float) - bg_ref) ** 2, axis=2))
bg_mask = diff < 60
bg_mask = ndimage.binary_closing(bg_mask, iterations=3)
bg_mask = ndimage.binary_fill_holes(bg_mask)
subject_mask = ~bg_mask
labeled, nf = ndimage.label(subject_mask)
if nf > 1:
    sizes = ndimage.sum(subject_mask, labeled, range(1, nf+1))
    subject_mask = labeled == (np.argmax(sizes)+1)

def floyd_steinberg(gray_img, mask=None):
    arr = np.array(gray_img, dtype=float)
    h, w = arr.shape
    dots = []
    for y in range(h):
        xs = range(w) if y%2==0 else range(w-1,-1,-1)
        for x in xs:
            old = arr[y,x]; new = 255.0 if old>127 else 0.0
            arr[y,x] = new; err = old - new
            if y%2==0:
                if x+1<w: arr[y,x+1]+=err*7/16
                if y+1<h:
                    if x-1>=0: arr[y+1,x-1]+=err*3/16
                    arr[y+1,x]+=err*5/16
                    if x+1<w: arr[y+1,x+1]+=err*1/16
            else:
                if x-1>=0: arr[y,x-1]+=err*7/16
                if y+1<h:
                    if x+1<w: arr[y+1,x+1]+=err*3/16
                    arr[y+1,x]+=err*5/16
                    if x-1>=0: arr[y+1,x-1]+=err*1/16
            if new==0 and (mask is None or mask[y,x]):
                dots.append((x,y))
    return dots

np.random.seed(42)
dots_dark = floyd_steinberg(portrait_gray, subject_mask)
dots_light = floyd_steinberg(portrait_gray, None)
print(f"Dark: {len(dots_dark)} dots, Light: {len(dots_light)} dots")

def compact_path(dots, ox, oy, sx, sy):
    return "".join(f"M{int(x*sx+ox)},{int(y*sy+oy)}h1v1h-1z" for x,y in dots)

def make_groups(dots, n=60):
    arr = np.array(dots)
    idx = np.random.permutation(len(arr))
    g = [[] for _ in range(n)]
    for i,di in enumerate(idx): g[i%n].append(tuple(arr[di]))
    return g

def build_svg(dots, groups, mode="dark"):
    W,H = 1180,610
    BG="#0d1117" if mode=="dark" else "#f0f6fc"
    DOT="#36BCF7" if mode=="dark" else "#1a3a5c"
    BORDER="#30363d" if mode=="dark" else "#d0d7de"
    T1="#c9d1d9" if mode=="dark" else "#24292f"
    T2="#8b949e" if mode=="dark" else "#57606a"
    CYAN="#36BCF7" if mode=="dark" else "#0969da"
    GREEN="#7ee787" if mode=="dark" else "#1a7f37"
    ORANGE="#ff9e64" if mode=="dark" else "#bc4c00"
    PURPLE="#bb9af7" if mode=="dark" else "#8250df"
    PANEL="#0d1117" if mode=="dark" else "#ffffff"

    pw,ph,pxf,pyf = 415,570,18,(H-570)//2
    sx,sy = pw/300,ph/340
    ox,oy = pxf+12,pyf+30

    full = compact_path(dots,ox,oy,sx,sy)
    intro_parts = []
    for i,grp in enumerate(groups):
        if not grp: continue
        gd = compact_path(grp,ox,oy,sx,sy)
        b = 0.4+(i/len(groups))*1.6
        intro_parts.append(
            f'<path d="{gd}" fill="{DOT}" shape-rendering="crispEdges" opacity="0">'
            f'<animate attributeName="opacity" values="0;1" dur="0.5s" begin="{b:.2f}s" fill="freeze"/>'
            f'</path>'
        )

    panel_x = pxf+pw+28; panel_w = W-panel_x-16; panel_y=14; panel_h=H-28
    rows = [
        ("Subject","Akshat Kardak",CYAN,"bold"),
        ("Role","Full-Stack Developer",T1,"normal"),
        ("Origin","Mumbai, India",T1,"normal"),
        ("Education","CS Eng · DMCE Navi Mumbai",T1,"normal"),
        ("Status","Building · Learning · Shipping",GREEN,"normal"),
        None,
        ("Core.Lang","JS · TS · Python · Java",ORANGE,"normal"),
        ("Core.Frontend","React · Next.js · Tailwind",ORANGE,"normal"),
        ("Core.Backend","Node.js · Express · FastAPI",ORANGE,"normal"),
        ("Core.Database","MongoDB · MySQL · Firebase",ORANGE,"normal"),
        ("Core.Infra","Vercel · Netlify · GitHub",ORANGE,"normal"),
        None,
        ("Grid.GitHub","AkshatKardak",PURPLE,"normal"),
        ("Grid.Portfolio","akshat-portfolio-teal.vercel.app",PURPLE,"normal"),
        ("Grid.LinkedIn","in/akshatkardak",PURPLE,"normal"),
        ("Grid.Mail","kardakakshat@gmail.com",T2,"normal"),
    ]
    row_y0=panel_y+105; rsp=27; rsvg=[]
    for i,row in enumerate(rows):
        ry=row_y0+i*rsp
        if row is None:
            rsvg.append(f'<line x1="{panel_x+8}" y1="{ry-4}" x2="{panel_x+panel_w-8}" y2="{ry-4}" stroke="{BORDER}" stroke-width="1" stroke-dasharray="3,4"/>')
            continue
        label,value,color,fw = row
        lx=panel_x+10; vx=panel_x+panel_w-10
        ll=len(label)*7.2+lx+8; vr=vx-len(value)*6.5
        leader=f'<line x1="{ll}" y1="{ry-2}" x2="{vr}" y2="{ry-2}" stroke="{BORDER}" stroke-width="1" stroke-dasharray="2,5"/>' if vr>ll+10 else ""
        rsvg.append(f'{leader}<text x="{lx}" y="{ry}" fill="{T2}" font-family="\'Courier New\',monospace" font-size="12">{label}</text>'
                    f'<text x="{vx}" y="{ry}" fill="{color}" font-family="\'Courier New\',monospace" font-size="12" font-weight="{fw}" text-anchor="end">{value}</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="{BG}" rx="6"/>
  <defs><pattern id="dg" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.5" fill="{BORDER}" opacity="0.4"/></pattern></defs>
  <rect width="{W}" height="{H}" fill="url(#dg)" rx="6"/>
  <rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="{panel_h}" fill="{PANEL}" stroke="{BORDER}" stroke-width="1" rx="4"/>
  <rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="32" fill="{BORDER}" rx="4"/>
  <circle cx="{panel_x+16}" cy="{panel_y+16}" r="5" fill="#ff5f57"/>
  <circle cx="{panel_x+32}" cy="{panel_y+16}" r="5" fill="#febc2e"/>
  <circle cx="{panel_x+48}" cy="{panel_y+16}" r="5" fill="#28c840"/>
  <text x="{panel_x+panel_w//2}" y="{panel_y+21}" fill="{T2}" font-family="'Courier New',monospace" font-size="12" text-anchor="middle">profile.sh --live</text>
  <rect x="{panel_x+panel_w-78}" y="{panel_y+42}" width="62" height="18" rx="9" fill="#ff3e3e"/>
  <text x="{panel_x+panel_w-47}" y="{panel_y+55}" fill="white" font-family="'Courier New',monospace" font-size="10" font-weight="bold" text-anchor="middle">&#9679; LIVE</text>
  <rect x="{panel_x+panel_w-162}" y="{panel_y+42}" width="76" height="18" rx="9" fill="{CYAN}" opacity="0.15"/>
  <text x="{panel_x+panel_w-124}" y="{panel_y+55}" fill="{CYAN}" font-family="'Courier New',monospace" font-size="9.5" text-anchor="middle" font-weight="bold">@AkshatKardak</text>
  <text x="{panel_x+10}" y="{panel_y+88}" fill="{CYAN}" font-family="'Courier New',monospace" font-size="13" font-weight="bold">SYSTEM.INFO</text>
  <line x1="{panel_x+10}" y1="{panel_y+93}" x2="{panel_x+panel_w-10}" y2="{panel_y+93}" stroke="{BORDER}" stroke-width="1"/>
  {"".join(rsvg)}
  <rect x="{pxf}" y="{pyf}" width="{pw}" height="{ph}" fill="none" stroke="{BORDER}" stroke-width="1" rx="3"/>
  <rect x="{pxf}" y="{pyf}" width="{pw}" height="22" fill="{BORDER}" rx="3"/>
  <text x="{pxf+pw//2}" y="{pyf+15}" fill="{T2}" font-family="'Courier New',monospace" font-size="9" text-anchor="middle">[ VISUAL.MAP ]</text>
  <path d="{full}" fill="{DOT}" shape-rendering="crispEdges" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.05s" begin="2.05s" fill="freeze"/>
  </path>
  {"".join(intro_parts)}
  <text x="12" y="{H-8}" fill="{T2}" font-family="'Courier New',monospace" font-size="9" opacity="0.5">Mumbai, IN · Full-Stack Developer · MERN · AI Integration</text>
  <text x="{W-12}" y="{H-8}" fill="{T2}" font-family="'Courier New',monospace" font-size="9" text-anchor="end" opacity="0.5">github.com/AkshatKardak</text>
</svg>'''

ig_dark = make_groups(dots_dark); ig_light = make_groups(dots_light)
dark_svg = build_svg(dots_dark, ig_dark, "dark")
light_svg = build_svg(dots_light, ig_light, "light")

with open("output/githubanner_dark.svg","w") as f: f.write(dark_svg)
with open("output/githubanner_light.svg","w") as f: f.write(light_svg)
print(f"Done! Dark: {len(dark_svg)//1024}KB, Light: {len(light_svg)//1024}KB")