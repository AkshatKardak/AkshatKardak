import numpy as np
from scipy.cluster.vq import kmeans2
from scipy.optimize import linear_sum_assignment
from PIL import Image, ImageDraw, ImageFont
import json, random

random.seed(7)
np.random.seed(7)

GRID_W, GRID_H = 300, 340
N_BANDS = 94
N_TRAVELERS = 900

light_ink = np.load('light_ink.npy')
dark_ink = np.load('dark_ink.npy')

def rle_path(mask, cell=1):
    """Row-run-length encode a boolean mask into one SVG path 'd' string
    made of axis-aligned rectangle subpaths (h/v/h/z), crisp-edge friendly."""
    h, w = mask.shape
    parts = []
    for y in range(h):
        row = mask[y]
        x = 0
        while x < w:
            if row[x]:
                x0 = x
                while x < w and row[x]:
                    x += 1
                run = x - x0
                parts.append(f"M{x0} {y}h{run}v1h{-run}z")
            else:
                x += 1
    return "".join(parts)

def dots_from_mask(mask):
    ys, xs = np.nonzero(mask)
    return np.stack([xs, ys], axis=1).astype(np.float64)

def band_assign(mask, n_bands, sigma=4.0):
    """Cluster ink dots into n_bands groups using position + gaussian noise."""
    pts = dots_from_mask(mask)
    if len(pts) < n_bands:
        n_bands = max(1, len(pts) // 4)
    noisy = pts + np.random.normal(0, sigma, pts.shape)
    centroids, labels = kmeans2(noisy, n_bands, minit='++', seed=7)
    bands = []
    for b in range(n_bands):
        sel = labels == b
        if not sel.any():
            continue
        band_pts = pts[sel]
        bx = band_pts[:, 0].mean()
        by = band_pts[:, 1].mean()
        sub_mask = np.zeros_like(mask)
        xs = band_pts[:, 0].astype(int)
        ys = band_pts[:, 1].astype(int)
        sub_mask[ys, xs] = True
        path = rle_path(sub_mask)
        bands.append({"cx": round(bx, 2), "cy": round(by, 2), "path": path, "n": int(sel.sum())})
    return bands

def straight_boundary_metric(bands, grid_w, grid_h):
    pts = np.array([[b['cx'], b['cy']] for b in bands])
    if len(pts) < 3:
        return 0.0
    from scipy.spatial import cKDTree
    tree = cKDTree(pts)
    d, idx = tree.query(pts, k=2)
    axis_aligned = 0
    for i in range(len(pts)):
        j = idx[i, 1]
        dx = pts[j, 0] - pts[i, 0]
        dy = pts[j, 1] - pts[i, 1]
        ang = np.degrees(np.arctan2(abs(dy), abs(dx) + 1e-9))
        if ang < 5 or ang > 85:
            axis_aligned += 1
    return axis_aligned / len(pts)

light_bands = band_assign(light_ink, N_BANDS, sigma=4.0)
dark_bands = band_assign(dark_ink, N_BANDS, sigma=4.0)
print("light bands:", len(light_bands), "straight-boundary metric:",
      round(straight_boundary_metric(light_bands, GRID_W, GRID_H), 4))
print("dark bands:", len(dark_bands), "straight-boundary metric:",
      round(straight_boundary_metric(dark_bands, GRID_W, GRID_H), 4))

def make_intro_groups(mask, n_groups=60):
    """Scatter dots into n_groups interleaved across the whole portrait."""
    pts = dots_from_mask(mask)
    order = np.arange(len(pts))
    np.random.shuffle(order)
    groups = [[] for _ in range(n_groups)]
    for i, idx in enumerate(order):
        groups[i % n_groups].append(pts[idx])
    return [np.array(g) for g in groups]

def evenness_metric(groups, grid_w, grid_h, mask, cells=8):
    full_pts = dots_from_mask(mask)
    fcx = np.clip((full_pts[:, 0] / grid_w * cells).astype(int), 0, cells - 1)
    fcy = np.clip((full_pts[:, 1] / grid_h * cells).astype(int), 0, cells - 1)
    ink_cells = set(zip(fcx.tolist(), fcy.tolist()))
    denom = max(1, len(ink_cells))
    scores = []
    for g in groups:
        if len(g) == 0:
            continue
        cx = np.clip((g[:, 0] / grid_w * cells).astype(int), 0, cells - 1)
        cy = np.clip((g[:, 1] / grid_h * cells).astype(int), 0, cells - 1)
        touched = len(set(zip(cx.tolist(), cy.tolist())) & ink_cells)
        frac = touched / denom
        scores.append(1 - frac)
    return float(np.mean(scores))

intro_groups_light = make_intro_groups(light_ink, 60)
intro_groups_dark = make_intro_groups(dark_ink, 60)
print("intro evenness (light, want ~0.05):", round(evenness_metric(intro_groups_light, GRID_W, GRID_H, light_ink), 4))
print("intro evenness (dark, want ~0.05):", round(evenness_metric(intro_groups_dark, GRID_W, GRID_H, dark_ink), 4))

def groups_to_paths(groups, mask_shape):
    out = []
    for g in groups:
        m = np.zeros(mask_shape, dtype=bool)
        if len(g):
            xs = g[:, 0].astype(int)
            ys = g[:, 1].astype(int)
            m[ys, xs] = True
        out.append(rle_path(m))
    return out

intro_light_paths = groups_to_paths(intro_groups_light, light_ink.shape)
intro_dark_paths = groups_to_paths(intro_groups_dark, dark_ink.shape)

def render_text_dots(text, size=(300, 340), font_scale=0.62, n_target=900):
    img = Image.new('L', size, 0)
    d = ImageDraw.Draw(img)
    fpath = None
    import glob
    for cand in glob.glob('/usr/share/fonts/**/*Bold*.ttf', recursive=True) + \
                glob.glob('/usr/share/fonts/**/DejaVuSans-Bold.ttf', recursive=True):
        fpath = cand
        break
    fsize = int(size[1] * font_scale)
    font = ImageFont.truetype(fpath, fsize) if fpath else ImageFont.load_default()
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pos = ((size[0] - tw) / 2 - bbox[0], (size[1] - th) / 2 - bbox[1])
    d.text(pos, text, fill=255, font=font)
    arr = np.array(img) > 127
    pts = dots_from_mask(arr)
    if len(pts) > n_target:
        sel = np.random.choice(len(pts), n_target, replace=False)
        pts = pts[sel]
    return pts

def render_hex_dots(size=(300, 340), n_target=900):
    img = Image.new('L', size, 0)
    d = ImageDraw.Draw(img)
    cx, cy = size[0] / 2, size[1] / 2
    for ring_r, width in [(110, 6), (78, 5), (46, 4)]:
        pts_hex = []
        for k in range(6):
            ang = np.pi / 6 + k * np.pi / 3
            pts_hex.append((cx + ring_r * np.cos(ang), cy + ring_r * np.sin(ang)))
        d.polygon(pts_hex, outline=255, width=width)
    for k in range(6):
        ang = np.pi / 6 + k * np.pi / 3
        nx, ny = cx + 78 * np.cos(ang), cy + 78 * np.sin(ang)
        d.ellipse([nx - 7, ny - 7, nx + 7, ny + 7], fill=255)
    d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=255)
    arr = np.array(img) > 127
    pts = dots_from_mask(arr)
    if len(pts) > n_target:
        sel = np.random.choice(len(pts), n_target, replace=False)
        pts = pts[sel]
    return pts

logoA_pts = render_text_dots("AK", n_target=N_TRAVELERS)
logoB_pts = render_hex_dots(n_target=N_TRAVELERS)

n = min(len(logoA_pts), len(logoB_pts), N_TRAVELERS)
rngA = np.random.choice(len(logoA_pts), n, replace=False)
rngB = np.random.choice(len(logoB_pts), n, replace=False)
logoA_pts = logoA_pts[rngA]
logoB_pts = logoB_pts[rngB]

cost = ((logoA_pts[:, None, :] - logoB_pts[None, :, :]) ** 2).sum(axis=2)
row_ind, col_ind = linear_sum_assignment(cost)
logoB_matched = logoB_pts[col_ind]

logoA_centroid = logoA_pts.mean(axis=0)
logoB_centroid = logoB_matched.mean(axis=0)

print("travelers matched:", n)
print("logoA centroid:", logoA_centroid, "logoB centroid:", logoB_centroid)

data = {
    "grid": {"w": GRID_W, "h": GRID_H},
    "light": {
        "bands": light_bands,
        "introGroups": intro_light_paths,
        "fullPath": rle_path(light_ink),
    },
    "dark": {
        "bands": dark_bands,
        "introGroups": intro_dark_paths,
        "fullPath": rle_path(dark_ink),
    },
    "travelers": {
        "logoA": logoA_pts.round(2).tolist(),
        "logoB": logoB_matched.round(2).tolist(),
    },
    "logoACentroid": logoA_centroid.round(2).tolist(),
    "logoBCentroid": logoB_centroid.round(2).tolist(),
}

with open('portrait_data.json', 'w') as f:
    json.dump(data, f)

print("wrote portrait_data.json, size bytes:", len(json.dumps(data)))
