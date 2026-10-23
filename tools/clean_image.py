"""Turn a photographed or scanned crop into a clean flashcard image.

- tighten(): shrink a box to the ink inside it (never grows past the box)
- clean():   flatten uneven lighting, white paper, crisp dark lines, upscale
Light gray highlight boxes printed on the sheet are kept as light gray.
"""
import numpy as np
from PIL import Image, ImageFilter


def _paper_model(L):
    """Fit a quadratic surface to the bright (paper) pixels to remove lighting gradients."""
    h, w = L.shape
    ys, xs = np.mgrid[0:h, 0:w]
    xs = xs / w
    ys = ys / h
    mask = L > np.percentile(L, 60)
    A = np.stack([np.ones_like(xs), xs, ys, xs * xs, ys * ys, xs * ys], -1)
    coef, *_ = np.linalg.lstsq(A[mask], L[mask], rcond=None)
    return np.maximum(A @ coef, 1)


def clean(img, max_side=440, scale=3):
    """Return a cleaned grayscale PIL image."""
    g = img.convert("L").filter(ImageFilter.MedianFilter(3))
    L = np.asarray(g).astype(float)
    r = L / _paper_model(L)
    o = np.clip((r - 0.3) / (0.97 - 0.3), 0, 1)
    o = np.where(r > 0.97, 1.0, o ** 1.4)
    out = Image.fromarray((o * 255).astype("uint8"))
    s = min(scale, max_side / max(out.size))
    out = out.resize((max(1, round(out.width * s)), max(1, round(out.height * s))), Image.BICUBIC)
    return out.filter(ImageFilter.GaussianBlur(0.6))


def tighten(page, bbox, margin=0.04):
    """bbox is [x0, y0, x1, y1] normalized to the page. Returns a tighter normalized bbox."""
    W, H = page.size
    x0, y0, x1, y1 = [min(1, max(0, v)) for v in bbox]
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    box = (int(x0 * W), int(y0 * H), max(int(x0 * W) + 4, int(x1 * W)), max(int(y0 * H) + 4, int(y1 * H)))
    L = np.asarray(page.crop(box).convert("L")).astype(float)
    ink = (L / _paper_model(L)) < 0.55
    rows = np.where(ink.sum(1) >= 2)[0]
    cols = np.where(ink.sum(0) >= 2)[0]
    if len(rows) < 2 or len(cols) < 2:
        return [x0, y0, x1, y1]
    m = round(max(L.shape) * margin)
    t, b = max(0, rows[0] - m), min(L.shape[0] - 1, rows[-1] + m)
    l, r = max(0, cols[0] - m), min(L.shape[1] - 1, cols[-1] + m)
    return [(box[0] + l) / W, (box[1] + t) / H, (box[0] + r + 1) / W, (box[1] + b + 1) / H]


def crop_clean(page_path, bbox, out_path, do_tighten=True):
    """Crop bbox from a page image, tighten, clean and save as JPEG. Returns the final bbox."""
    page = Image.open(page_path).convert("RGB")
    bb = tighten(page, bbox) if do_tighten else bbox
    W, H = page.size
    crop = page.crop((round(bb[0] * W), round(bb[1] * H), round(bb[2] * W), round(bb[3] * H)))
    clean(crop).convert("RGB").save(out_path, "JPEG", quality=86)
    return bb
