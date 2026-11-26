#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch watermark removal for flat-background graphics (icons/ai-images).

Detects a small semi-transparent grey text watermark (e.g. 豆包AI生成) in the
bottom-right corner via a pixel threshold on the dark-text mask, dilates the
mask, inpaints the ROI with OpenCV TELEA, and writes results to a `去水印/`
subdir WITHOUT overwriting the originals.

Run on this machine with the env prefix (see SKILL.md Environment pitfall):
    env -u PYTHONPATH python3 remove_watermark.py /path/to/dir

Usage: python3 remove_watermark.py <dir> [--glob '*.png'] [--xmin 0.30] [--ymin 0.68]
Adapt xmin/ymin if the watermark is not bottom-right (corner) or if the subject
fills more/less of the frame.
"""
import os, sys, glob
import cv2, numpy as np

def remove_from_file(path, outdir, xmin=0.30, ymin=0.68):
    img = cv2.imread(path)
    if img is None:
        return f"读取失败: {path}"
    h, w = img.shape[:2]
    y0, y1 = int(h * ymin), h
    x0, x1 = int(w * xmin), w
    roi = img[y0:y1, x0:x1]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    bg = np.median(gray)
    mask = (gray < bg - 8).astype(np.uint8) * 255
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2)
    n = int((mask > 0).sum())
    if n < 20:
        return f"{os.path.basename(path)}: 未检测到水印，跳过"
    repaired = cv2.inpaint(roi, mask, 3, cv2.INPAINT_TELEA)
    out = img.copy()
    out[y0:y1, x0:x1] = repaired
    os.makedirs(outdir, exist_ok=True)
    outp = os.path.join(outdir, os.path.basename(path))
    cv2.imwrite(outp, out)
    ys, xs = np.where(mask > 0)
    return f"{os.path.basename(path)}: 水印像素={n}, 范围 x{x0+xs.min()}-{x0+xs.max()} y{y0+ys.min()}-{y0+ys.max()} -> {os.path.basename(outp)}"

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    g = [a for a in sys.argv[1:] if a.startswith('--glob=')]
    rule = g[0].split('=', 1)[1] if g else '*.png'
    src = args[0] if args else '.'
    o = [a for a in sys.argv[1:] if a.startswith('--out=')]
    outdir = o[0].split('=', 1)[1] if o else os.path.join(src, '去水印')
    files = sorted(glob.glob(os.path.join(src, rule)))
    print(f"待处理 {len(files)} 个文件，模式 {rule}")
    for f in files:
        print(' ', remove_from_file(f, outdir))
    print("完成，输出目录:", outdir)

if __name__ == '__main__':
    main()
