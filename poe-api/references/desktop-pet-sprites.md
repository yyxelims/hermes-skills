# Desktop Pet Sprites via Poe + PIL + tkinter

Full workflow for creating animated desktop pet sprites using Poe image generation,
PIL post-processing, and tkinter for Windows/macOS deployment.

## Pipeline Overview

```
Poe AI → generate sprite → PIL clean bg → crop → resize → PNG save → code animation → tkinter → PyInstaller .exe
```

## 1. Generate Base Sprites (Poe)

Use `gpt-image-1.5` for best results. Generate one image per character state.
Keep prompts consistent to maintain character identity across poses.

```
Prompt template: "cute chibi {animal} character, {pose/expression}, flat vector game sprite style, solid light blue background, centered, full body"

States needed:
- idle: "floating peacefully"
- happy: "happy smiling expression with open mouth"
- sleep: "sleeping, eyes closed curved lines, ZZZ bubbles"
```

Generated images are 1024x1024 RGB with light blue background (#75B9E9 range).

## 2. Clean + Process (PIL)

```python
from PIL import Image

def clean_sprite(path, target_size=250):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    px = img.load()

    # Remove sky-blue background (tolerance: ±40 per channel)
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 0 and 80 < r < 200 and 120 < g < 220 and 160 < b < 250:
                px[x, y] = (r, g, b, 0)

    # Crop to visible content
    bbox = img.getbbox()
    if bbox:
        pad = 10
        bbox = (max(0,bbox[0]-pad), max(0,bbox[1]-pad),
                min(w,bbox[2]+pad), min(h,bbox[3]+pad))
        img = img.crop(bbox)

    # Resize proportionally
    scale = target_size / max(img.size)
    if scale < 1:
        img = img.resize((int(img.width*scale), int(img.height*scale)),
                         Image.LANCZOS)

    # Center on transparent canvas
    canvas = Image.new("RGBA", (target_size, target_size), (0,0,0,0))
    cx = (target_size - img.width) // 2
    cy = (target_size - img.height) // 2
    canvas.paste(img, (cx, cy), img)
    return canvas
```

## 3. Derive Additional States

From 3 base sprites (idle, happy, sleep), derive the remaining states:

```python
# drag: rotate idle slightly
drag = idle.rotate(8, expand=True, fillcolor=(0,0,0,0))

# feed: copy happy
feed = happy.copy()

# wake: dim idle, then bright
dim = Image.blend(idle, Image.new("RGBA", size, (100,100,180,220)), 0.35)
```

## 4. Animation — PNG + Code, NOT GIF

**Avoid multi-frame GIFs.** PIL's GIF encoder silently merges identical
adjacent frames even with `optimize=False`. The `imageio` library works
but adds a dependency.

Instead, save one PNG per state and animate in code:

```python
# Idle bob
bob = math.sin(frame * 0.04) * 5 * scale
canvas.paste(sprite, (0, int(bob)), sprite)

# Sleep breathing
breath = 1 + math.sin(frame * 0.02) * 0.03
resized = sprite.resize((int(w*breath), int(h*breath)), Image.LANCZOS)

# Happy bounce
bounce = abs(math.sin(frame * 0.12)) * 10 * scale

# Wake fade-in
alpha = min(1.0, frame / 15)
enhanced = ImageEnhance.Brightness(sprite).enhance(0.4 + 0.6 * alpha)

# Drag tilt
tilted = sprite.rotate(5 * math.sin(frame * 0.08), expand=True,
                       fillcolor=(0,0,0,0))
```

## 5. Cross-Platform tkinter Transparency

```python
import platform
IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

root = Tk()
if IS_WIN:
    root.attributes("-transparentcolor", "#010101")
elif IS_MAC:
    root.attributes("-transparent", True)
    root.configure(bg="systemTransparent")
root.attributes("-topmost", True)
root.overrideredirect(True)

label = Label(root, bg="#010101" if IS_WIN else "systemTransparent")
```

## 6. PyInstaller Packaging for Windows

```batch
pyinstaller --onefile --noconsole --name BlubShark \
  --add-data "pet_frames;pet_frames" \
  --hidden-import PIL._tkinter_finder \
  shark_pet.py
```

The `pet_frames` directory must be included via `--add-data`.
In the Python code, resolve paths with:

```python
import sys, os
if getattr(sys, 'frozen', False):
    BASE = sys._MEIPASS
else:
    BASE = os.path.dirname(os.path.abspath(__file__))

def resource_path(*parts):
    return os.path.join(BASE, *parts)
```

## 7. Batch File Patterns

**Run script** (avoids `%VAR%` delayed expansion trap):
```batch
@echo off
chcp 65001 >nul
cd /d "%~dp0"
python script.py 2>nul || py script.py 2>nul
```

**Offline install** (local .whl, no internet needed):
```batch
python -m pip install "pillow-12.3.0-cp312-cp312-win_amd64.whl"
```

## Directory Structure

```
pet_folder/
├── shark_pet.py           # Main app
├── run.bat                # Windows launcher
├── install.bat            # Offline dependency install
├── 打包exe.bat             # PyInstaller build
├── pillow-*.whl           # Offline dependency
└── pet_frames/
    ├── common/
    │   ├── enter.png
    │   └── goodbye.png
    └── sets/
        └── shark/
            ├── idle.png
            ├── happy.png
            ├── sleep.png
            ├── drag.png    (derived)
            ├── feed.png    (derived)
            └── wake.png    (derived)
```
