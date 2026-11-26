---
name: image-watermark-removal
description: "Use when user asks to 去水印. OpenCV inpaint + pixel-verify."
version: 1.0.0
author: Hermes Agent
---

# Image Watermark Removal (去水印)

Remove a watermark from an image using OpenCV inpaint. Verified workflow for the common case: a small semi-transparent grey text watermark (e.g. "豆包AI生成") in a corner of a flat-background graphic/icon.

## When to use
- User gives an image and says 去水印 / remove watermark / clean this up.
- Watermark is text or a small logo on a near-flat background (icons, AI-generated graphics, screenshots, product cards).
- Ready-to-run batch script: `scripts/remove_watermark.py` (usage: `env -u PYTHONPATH python3 remove_watermark.py <dir>`).

## Key facts learned
- Most Chinese AI image generators (豆包/即梦/Kimi etc.) stamp a small semi-transparent grey text like "豆包AI生成" in the bottom-right corner. Background is usually off-white/light grey, NOT pure white.
- The watermark sits on the background, **not** on the main subject (the logo/icon), so inpainting just fills with surrounding background — no subject data lost.
- **cv2 works in anaconda3 but not in the default python3 on this machine** — see Environment pitfall below.

## Workflow

### 1. Locate the watermark (vision)
Use `vision_analyze` on the image: ask where the watermark is, its color, opacity, and whether it overlaps the subject. This confirms the region and that the background is flat.

### 2. Crop-and-inspect the region (get exact bounds)
Locate the watermark precisely by pixel analysis, not by eyeballing, so you can verify removal later:
```python
import cv2, numpy as np
img = cv2.imread(path)
h, w = img.shape[:2]
# Only inspect the region that does NOT contain the subject (e.g. bottom-right for corner watermarks)
roi = img[int(h*0.68):h, int(w*0.30):w]
gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
bg = np.median(gray)
mask = (gray < bg - 8).astype(np.uint8)*255   # pixels darker than background = watermark text
print(int((mask>0).sum()))                      # >0 means watermark found
```

### 3. Inpaint (the actual removal)
```python
import cv2, numpy as np, os
mask = cv2.dilate(mask, np.ones((3,3), np.uint8), iterations=2)  # cover text edges
repaired = cv2.inpaint(roi, mask, 3, cv2.INPAINT_TELEA)
out = img.copy()
out[y0:y1, x0:x1] = repaired
cv2.imwrite(outfile, out)   # NEVER overwrite the original; write to a subdir like 去水印/
```

### 4. VERIFY with pixel scan, not just vision (critical)
A vision model will often **falsely report leftover text** because the subject's anti-aliased edge (e.g. a green circle against white) looks greyish and gets misread. Never trust vision alone.

Confirm with a pixel scan of the watermark region only — but make the region **exclude the subject by enough margin**:
```python
# subject occupies ~x[95:545] y[95:545] in a 640x640 image; watermark is bottom-right OUTSIDE that
roi = gray[520:640, 480:640]     # pure-background corner
resid = (roi < 250)              # any pixel darker than near-white
print(int(resid.sum()))           # 0 (or ~1) = clean
```
If the region you scan includes part of the subject, the scan returns hundreds of "residual" pixels that are actually subject edges — widen the working region, don't trust the number.

## Environment pitfall (running cv2 scripts on this machine)
The default `python3` points to anaconda3 (3.12) but `PYTHONPATH` is polluted toward the hermes venv's numpy (3.11), so `import cv2`/`import numpy` fail with a binary mismatch (`No module named 'numpy._core._multiarray_umath'`). Run cv2/numpy scripts with:
```bash
env -u PYTHONPATH python3 script.py
```
This uses anaconda3's clean cv2 (4.10) + numpy (1.26).

## Pitfalls
1. **Never overwrite the source image.** Write results to a `去水印/` (or similar) subdir; keep originals intact.
2. **ALWAYS do a pixel-level residual scan** after the fix (step 4). Vision alone gives false positives on subject edges.
3. **Scan region must exclude the subject.** Include the subject in the scan and you'll get a misleading non-zero "residual" count.
4. **Only the watermark region gets inpainted.** Restrict `inpaint` input to the ROI, not the whole image, so the subject is untouched.
5. **Multi-image batch:** loop over files; one script handles all. Verify each with the pixel scan.
6. Clean up temp inspection scripts (`_*.py`, `_*.png`) after the job so the user's folder isn't littered.

## Deliver
Return the cleaned files with a table (subject / watermark removed / background clean / subject intact), state that originals are unmodified, and give the output directory path.
