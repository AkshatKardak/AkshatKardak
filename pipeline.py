"""
Portrait -> dithered dot-grid pipeline.

Produces two binary 300x340 grids:
- light_grid: ink where the photo is DARK (normal halftone, bg kept)
- dark_grid: ink where the SUBJECT is LIGHT (bg segmented out, hard-cleared)
"""
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from scipy import ndimage
import json

GRID_W, GRID_H = 300, 340

# ---------- 1. crop head+shoulders ----------
def crop_head_shoulders(img, fx, fy, fw, fh):
    face_cx = fx + fw / 2
    crop_h = int(fh * 1.35 / 0.32)
    crop_w = int(crop_h * GRID_W / GRID_H)
    top_of_head = fy - 0.3 * fh
    crop_top = int(top_of_head - 0.12 * crop_h)
    crop_bottom = crop_top + crop_h
    crop_left = int(face_cx - crop_w / 2)
    crop_right = crop_left + crop_w
    return img.crop((crop_left, crop_top, crop_right, crop_bottom))

# ---------- 2. preprocess ----------
def preprocess(img):
    img = img.resize((GRID_W, GRID_H), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = img.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    return img

# ---------- 3. background segmentation (for dark mode) ----------
def segment_subject(rgb_arr):
    h, w, _ = rgb_arr.shape
    patches = [
        rgb_arr[0:12, 0:12], rgb_arr[0:12, w-12:w],
        rgb_arr[h-12:h, 0:12], rgb_arr[h-12:h, w-12:w],
    ]
    samples = np.concatenate([p.reshape(-1, 3) for p in patches], axis=0)
    bg_colour = np.median(samples, axis=0)

    dist = np.sqrt(((rgb_arr.astype(np.float32) - bg_colour) ** 2).sum(axis=2))
    thresh = max(28.0, np.percentile(dist, 15) * 1.8)
    subject_mask = dist > thresh

    subject_mask = ndimage.binary_closing(subject_mask, structure=np.ones((5, 5)), iterations=2)
    subject_mask = ndimage.binary_fill_holes(subject_mask)
    labeled, n = ndimage.label(subject_mask)
    if n > 0:
        sizes = ndimage.sum(subject_mask, labeled, range(1, n + 1))
        largest = np.argmax(sizes) + 1
        subject_mask = labeled == largest
    subject_mask = ndimage.binary_erosion(subject_mask, structure=np.ones((3, 3)), iterations=1)
    return subject_mask

# ---------- 4. serpentine Floyd-Steinberg dithering ----------
def floyd_steinberg_serpentine(gray):
    """gray: float array (h,w) in [0,255]. Returns binary array: 1 = ink (dark)."""
    h, w = gray.shape
    buf = gray.astype(np.float64).copy()
    ink = np.zeros((h, w), dtype=np.uint8)
    for y in range(h):
        left_to_right = (y % 2 == 0)
        xs = range(w) if left_to_right else range(w - 1, -1, -1)
        xdir = 1 if left_to_right else -1
        for x in xs:
            old = buf[y, x]
            new = 0.0 if old < 128 else 255.0
            ink[y, x] = 1 if new == 0.0 else 0
            err = old - new
            if left_to_right:
                if x + 1 < w:
                    buf[y, x + 1] += err * 7 / 16
                if y + 1 < h:
                    if x - 1 >= 0:
                        buf[y + 1, x - 1] += err * 3 / 16
                    buf[y + 1, x] += err * 5 / 16
                    if x + 1 < w:
                        buf[y + 1, x + 1] += err * 1 / 16
            else:
                if x - 1 >= 0:
                    buf[y, x - 1] += err * 7 / 16
                if y + 1 < h:
                    if x + 1 < w:
                        buf[y + 1, x + 1] += err * 3 / 16
                    buf[y + 1, x] += err * 5 / 16
                    if x - 1 >= 0:
                        buf[y + 1, x - 1] += err * 1 / 16
    return ink

# ---------- 5. run-length encode rows into path runs ----------
def rows_to_runs(ink):
    """Return list of (y, x_start, run_len) for contiguous 1s per row."""
    h, w = ink.shape
    runs = []
    for y in range(h):
        row = ink[y]
        x = 0
        while x < w:
            if row[x]:
                x0 = x
                while x < w and row[x]:
                    x += 1
                runs.append((y, x0, x - x0))
            else:
                x += 1
    return runs

def main():
    src = Image.open('akshat.jpeg').convert('RGB')
    fx, fy, fw, fh = 493, 311, 207, 207
    cropped = crop_head_shoulders(src, fx, fy, fw, fh)
    proc = preprocess(cropped)
    proc.save('processed_300x340.png')

    rgb_arr = np.array(proc)
    gray = np.array(proc.convert('L')).astype(np.float64)

    light_ink = floyd_steinberg_serpentine(gray.copy())

    subject_mask = segment_subject(rgb_arr)
    inv_gray = 255.0 - gray
    dark_ink_full = floyd_steinberg_serpentine(inv_gray.copy())
    dark_ink = dark_ink_full * subject_mask.astype(np.uint8)

    print("light ink count:", int(light_ink.sum()))
    print("dark ink count:", int(dark_ink.sum()))
    print("subject mask px:", int(subject_mask.sum()), "/", subject_mask.size)

    np.save('light_ink.npy', light_ink)
    np.save('dark_ink.npy', dark_ink)
    np.save('subject_mask.npy', subject_mask)

    Image.fromarray(((1 - light_ink) * 255).astype(np.uint8)).save('preview_light.png')
    Image.fromarray((dark_ink * 255).astype(np.uint8)).save('preview_dark.png')
    Image.fromarray((subject_mask * 255).astype(np.uint8)).save('preview_mask.png')

if __name__ == '__main__':
    main()
