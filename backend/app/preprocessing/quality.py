import numpy as np
from PIL import Image
from typing import Dict, Any, List


def compute_laplacian_variance(gray: np.ndarray) -> float:
    """Computes blur metric via discrete 2D Laplacian kernel convolution variance."""
    # Discrete Laplacian kernel
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    # Simple valid convolution
    h, w = gray.shape
    if h < 5 or w < 5:
        return 200.0
    # Convolution with sub-sampling for speed
    step = 2
    sub = gray[::step, ::step].astype(np.float32)
    sh, sw = sub.shape
    if sh < 3 or sw < 3:
        return 200.0

    lap = (
        sub[0:-2, 1:-1] + sub[2:, 1:-1] +
        sub[1:-1, 0:-2] + sub[1:-1, 2:] -
        4.0 * sub[1:-1, 1:-1]
    )
    var = float(np.var(lap))
    return round(var, 2)


def compute_contrast(gray: np.ndarray) -> float:
    """RMS contrast (standard deviation of normalized pixel intensities)."""
    std = float(np.std(gray))
    # Normalized between 0.0 and 1.0 (std of 0-255 is max ~127)
    return round(min(1.0, std / 64.0), 3)


def compute_fade_score(gray: np.ndarray) -> float:
    """
    Measures text fading: ratio of weak/washed-out grey pixels (160-220)
    relative to crisp dark text (<100). Higher = more faded.
    """
    dark_text = np.sum(gray < 100)
    faded_text = np.sum((gray >= 150) & (gray <= 215))
    if dark_text + faded_text == 0:
        return 0.0
    fade_ratio = faded_text / float(dark_text + faded_text + 1e-5)
    return round(float(fade_ratio), 3)


def compute_noise_score(gray: np.ndarray) -> float:
    """Estimates high-frequency noise variance via difference from median filter."""
    h, w = gray.shape
    if h < 10 or w < 10:
        return 0.0
    # Quick 3x3 box blur difference
    sub = gray[::2, ::2].astype(np.float32)
    blurred = (
        sub[:-2, :-2] + sub[:-2, 1:-1] + sub[:-2, 2:] +
        sub[1:-1, :-2] + sub[1:-1, 1:-1] + sub[1:-1, 2:] +
        sub[2:, :-2] + sub[2:, 1:-1] + sub[2:, 2:]
    ) / 9.0
    diff = sub[1:-1, 1:-1] - blurred
    noise_var = float(np.var(diff))
    # Normalized 0.0 to 1.0
    return round(min(1.0, noise_var / 150.0), 3)


def estimate_skew_angle(gray: np.ndarray) -> float:
    """
    Estimates skew angle by horizontal projection profile variance across small angle range (-5 to +5 deg).
    """
    # Downsample for speed
    thumb = Image.fromarray(gray).resize((300, 400), Image.BILINEAR)
    arr = np.array(thumb, dtype=np.float32)
    # Binary text edges
    edges = (arr < 140).astype(np.float32)

    best_angle = 0.0
    max_var = -1.0
    for angle in np.linspace(-4.0, 4.0, 17):
        rotated = Image.fromarray(edges).rotate(float(angle), resample=Image.NEAREST)
        proj = np.sum(np.array(rotated), axis=1)
        var = float(np.var(proj))
        if var > max_var:
            max_var = var
            best_angle = float(angle)

    return round(best_angle, 2)


def compute_stain_coverage(gray: np.ndarray) -> float:
    """Detects irregular medium-dark patches indicative of liquid/tea/water stains."""
    # Stains typically fall in 140-195 range with spatial clustering
    stained_pixels = np.sum((gray >= 130) & (gray <= 185))
    total_pixels = gray.size
    return round(float(stained_pixels / max(1, total_pixels)), 3)


def analyze_page_quality(img: Image.Image, grid_rows: int = 4, grid_cols: int = 4) -> Dict[str, Any]:
    """
    Computes whole-page and tile-level damage and degradation quality metrics:
    - blur (Laplacian variance)
    - contrast
    - fade score
    - noise
    - skew angle
    - stain coverage
    - tile_metrics: list of local quality scores per bbox
    """
    gray_img = img.convert("L")
    w, h = gray_img.size
    gray_arr = np.array(gray_img, dtype=np.uint8)

    # Page-level metrics
    page_blur = compute_laplacian_variance(gray_arr)
    page_contrast = compute_contrast(gray_arr)
    page_fade = compute_fade_score(gray_arr)
    page_noise = compute_noise_score(gray_arr)
    page_skew = estimate_skew_angle(gray_arr)
    page_stain = compute_stain_coverage(gray_arr)

    # Grid of tiles for local damage assessment under bboxes
    tile_metrics: List[Dict[str, Any]] = []
    tile_h = h // grid_rows
    tile_w = w // grid_cols

    for r in range(grid_rows):
        for c in range(grid_cols):
            y1 = r * tile_h
            y2 = min((r + 1) * tile_h, h)
            x1 = c * tile_w
            x2 = min((c + 1) * tile_w, w)

            tile_crop = gray_arr[y1:y2, x1:x2]
            t_blur = compute_laplacian_variance(tile_crop)
            t_fade = compute_fade_score(tile_crop)
            t_stain = compute_stain_coverage(tile_crop)

            # Check if tile has torn/missing area (e.g. corner near white/empty)
            t_tear = 0.0
            if (r == 0 or r == grid_rows - 1) and (c == 0 or c == grid_cols - 1):
                # Check variance / border discontinuity
                if np.mean(tile_crop) > 248.0 or np.var(tile_crop) < 15.0:
                    t_tear = 0.35

            tile_metrics.append({
                "row": r,
                "col": c,
                # Normalized bbox [ymin, xmin, ymax, xmax]
                "bbox": [round(y1 / h, 4), round(x1 / w, 4), round(y2 / h, 4), round(x2 / w, 4)],
                "blur": t_blur,
                "fade": t_fade,
                "stain": t_stain,
                "tear": t_tear
            })

    raw_dpi = img.info.get("dpi")
    dpi_val = 150.0
    if raw_dpi is not None:
        try:
            dpi_first = raw_dpi[0] if isinstance(raw_dpi, (tuple, list)) else raw_dpi
            dpi_val = float(dpi_first)
        except Exception:
            dpi_val = 150.0

    raw_res = {
        "width": int(w),
        "height": int(h),
        "dpi": float(dpi_val),
        "blur_score": float(page_blur),
        "contrast_score": float(page_contrast),
        "fade_score": float(page_fade),
        "noise_score": float(page_noise),
        "skew_angle": float(page_skew),
        "stain_coverage": float(page_stain),
        "tile_metrics": tile_metrics
    }
    return sanitize_for_json(raw_res)


def sanitize_for_json(obj: Any) -> Any:
    """Recursively converts non-serializable objects (IFDRational, numpy types) to native Python primitives."""
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        val = float(obj)
        return 0.0 if (np.isnan(val) or np.isinf(val)) else val
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, "numerator") and hasattr(obj, "denominator"):
        return float(obj.numerator) / float(obj.denominator) if obj.denominator != 0 else 0.0
    elif isinstance(obj, (str, bool)) or obj is None:
        return obj
    return str(obj)
