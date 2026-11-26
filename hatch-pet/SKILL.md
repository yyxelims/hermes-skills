---
name: hatch-pet
description: Create, repair, validate, preview, and package Codex-compatible animated pet spritesheets from character art, screenshots, generated images, or visual references. Use when a user wants to hatch a Codex pet, create a custom animated pet, or build a built-in pet asset with an 8x9 atlas, transparent unused cells, row-by-row animation prompts, QA contact sheets, preview videos, and pet.json packaging. Requires an image generator with text-prompt + reference-image grounding capabilities. Uses bundled deterministic scripts for spritesheet assembly.
version: 1.0.0
tags: [codex, pet, sprite, animation, pixel-art, image-generation]
---

# Hatch Pet (Hermes Edition)

Adapted from the OpenAI Codex "hatch-pet" skill for Hermes Agent. Original source: https://github.com/kjx-talesofai/claude-skill-codex-pet

## Overview

Create a Codex-compatible animated pet from a concept, one or more reference images, or both. This skill owns pet-specific prompt planning, animation rows, frame extraction, atlas geometry, QA, previews, and packaging. It delegates visual generation to whatever image generation tool is available in the current environment.

User-facing inputs are optional. If the user omits a pet name, infer one from the concept or reference filenames; if that is not possible, choose a short appropriate name. If the user omits a description, infer one from the concept or references. If the user omits reference images, generate the base pet from text first, then use that base as the canonical reference for every animation row.

## Prerequisites

- Python 3 with Pillow (`pip install Pillow`)
- An image generator: ComfyUI (via Hermes skill), GPT Image 2, or any tool that supports text-to-image + reference image grounding
- `ffmpeg` for preview video generation (optional but recommended)
- **China users:** see `references/china-network.md` for GitHub/HuggingFace mirror workarounds during model downloads.

### Pre-flight Checklist (MANDATORY — run before any pet workflow)

Before starting a pet run, always check what's available. Run this diagnostic:

```bash
# Check 1: ComfyUI server?
curl -s http://127.0.0.1:8188/system_stats 2>/dev/null && echo "ComfyUI: AVAILABLE" || echo "ComfyUI: NOT RUNNING"

# Check 2: comfy-cli installed?
command -v comfy 2>/dev/null && echo "comfy-cli: AVAILABLE" || echo "comfy-cli: NOT INSTALLED"

# Check 3: OPENAI_API_KEY (GPT Image fallback)?
[ -n "$OPENAI_API_KEY" ] && echo "OPENAI_API_KEY: SET" || echo "OPENAI_API_KEY: NOT SET"

# Check 4: ffmpeg?
command -v ffmpeg 2>/dev/null && echo "ffmpeg: AVAILABLE" || echo "ffmpeg: NOT INSTALLED"

# Check 5: Pillow?
python3 -c "from PIL import Image; print('Pillow: OK', Image.__version__)"
```

**Decision matrix based on results:**

| ComfyUI | comfy-cli | OPENAI_API_KEY | Action |
|---------|-----------|----------------|--------|
| Running | — | — | Proceed with ComfyUI path (best quality) |
| Not running | Installed | — | `comfy launch --background` to start it |
| Not running | Not installed | Set | Use GPT Image 2 fallback (fastest setup) |
| Not running | Not installed | Not set | **BLOCKED** — present options to user |

When blocked, present three options to the user:
- **A. Install ComfyUI locally** — run `comfyui` skill setup. ~30 min, needs ~20 GB disk. Free. See `references/china-network.md` for GFW workarounds during model downloads.
- **B. Use GPT Image 2** — user provides `OPENAI_API_KEY`. ~5 min, paid per API call.
- **C. Prepare prompts only** — run `prepare_pet_run.py` to generate all prompts and layout guides, then wait for image generator to be available.

Do NOT proceed past the checklist into image generation until one of the three paths is confirmed working.

## Required Image Generation Capabilities

The image generator used with this skill must support:

1. **Text-to-image generation** from detailed prompts.
2. **Reference image grounding** (attaching input images to guide output). Required for row-strip generation.
3. **PNG output** (or convertible to PNG).
4. **Reasonable prompt adherence** for precise layouts.

**Hermes-specific image generation options:**
- **ComfyUI** (recommended): Use the `comfyui` skill. Supports text-to-image and reference image grounding.
- **GPT Image 2**: Use `OPENAI_API_KEY` via the bundled `generate_pet_images.py` fallback script.
- **Any external tool**: Just produce a PNG file and pass it to `record_imagegen_result.py`.

## Hermes Image Generation Flow

In Hermes, use the `comfyui` skill for image generation. Before generating, load it:

```
skill_view(name='comfyui')
```

If ComfyUI is not available, use the fallback script:

```bash
python "$SKILL_DIR/scripts/generate_pet_images.py" \
  --run-dir /absolute/path/to/run \
  --model gpt-image-2 \
  --states all
```

This requires `OPENAI_API_KEY`.

## Generation Delegation

Use Hermes's available image generation tool for all visual generation. When invoking an image generator from this skill, pass the generated pet prompt as the authoritative visual spec.

Hard boundary: do not create, draw, tile, warp, mirror, or synthesize pet visuals with local Python/Pillow scripts, SVG, canvas, HTML/CSS, or other code-native art as a substitute for the image generator. For a normal pet run, expect up to 10 visual generation jobs: 1 base pet plus 9 row-strip jobs. The only exception is `running-left`, which may be derived by mirroring `running-right` only after `running-right` has been generated, visually inspected, and explicitly approved as safe to mirror.

Only the base job may be prompt-only. Every row-strip job must use the input images listed in `imagegen-jobs.json`, including the canonical base reference created after the base job is recorded.

## Hermes Subagent Row Generation

Hermes uses `delegate_task` for parallel subagent work. After the base job has been recorded and `references/canonical-base.png` exists, row-strip visual generation should use parallel subagents.

Default flow:
1. Parent runs `prepare_pet_run.py`.
2. Parent generates and records `base`.
3. Parent runs `pet_job_status.py`.
4. Parent delegates `idle` and `running-right` as subagents first (identity and gait checks).
5. Parent records the selected `idle` and `running-right` results.
6. Parent decides whether `running-left` is safe to derive by mirror; if not, delegates it as normal grounded row.
7. Parent delegates remaining non-derived row jobs in parallel (up to 3 at a time in Hermes).
8. Parent alone runs `record_imagegen_result.py`, `derive_running_left_from_running_right.py`, repair queueing, finalization, QA, and packaging.

Subagent handoff template for Hermes `delegate_task`:

```python
delegate_task(
    tasks=[{
        "goal": f"Generate the {row_id} row for hatch-pet run at {run_dir}",
        "context": f"""Read the prompt file at {prompt_file}.
Input images: {input_images_str}

Steps:
1. Use ComfyUI or available image tool to generate with the prompt + all reference images.
2. If output is a URL, download to local PNG.
3. Verify: exact frame count, same identity as base, green background, no detached effects.
4. Return the absolute path to the generated PNG and a one-sentence QA note.

DO NOT edit manifests, copy into decoded/, record results, mirror rows, finalize, repair, or package."""
    } for row_id, prompt_file, input_images_str in jobs],
    toolsets=['terminal', 'file', 'vision'],
    role='leaf'
)
```

## Codex Digital Pet Style

Default pet art should match the Codex app's built-in digital pets: small pixel-art-adjacent mascots with compact chibi proportions, chunky readable silhouettes, thick dark 1-2 px outlines, visible stepped/pixel edges, limited palettes, flat cel shading, simple expressive faces, and tiny limbs.

Do NOT generate polished illustration, painterly rendering, anime key art, 3D rendering, glossy app-icon treatment, realistic fur or material texture, soft gradients, high-detail antialiasing, or complex tiny accessories.

## Transparency And Effects

Pet rows are processed into transparent 192x208 cells. Every generated pixel must either belong to the pet sprite or be cleanly removable chroma-key background.

Allowed effects (must satisfy ALL conditions):
- State-relevant and helps explain the animation.
- Physically attached to, touching, or overlapping the pet silhouette.
- Inside the same frame slot as the pet.
- Opaque, hard-edged, pixel-style, non-chroma-key colors.
- Small enough to remain readable at 192x208.

Forbidden effects:
- Wave marks, motion arcs, speed lines, action streaks, afterimages, blur, smears
- Detached stars, sparkles, floating icons, falling tear drops, separated smoke clouds
- Cast shadows, drop shadows, glow, halo, aura, soft transparent effects
- Text, labels, frame numbers, visible grids, speech bubbles, UI panels
- Chroma-key-adjacent colors in the pet or effects
- Stray pixels, cropped body parts, overlapping poses

## Default Workflow

1. Prepare a pet run folder:

```bash
SKILL_DIR="$HOME/.hermes/skills/hatch-pet"
python "$SKILL_DIR/scripts/prepare_pet_run.py" \
  --pet-name "<Name>" \
  --description "<one sentence>" \
  --reference /absolute/path/to/reference.png \
  --output-dir /absolute/path/to/run \
  --pet-notes "<stable pet description>" \
  --style-notes "<style notes>" \
  --force
```

2. Check job status:

```bash
python "$SKILL_DIR/scripts/pet_job_status.py" --run-dir /absolute/path/to/run
```

3. For each ready job, invoke the image generator with the prompt and input images.

4. Record results:

```bash
python "$SKILL_DIR/scripts/record_imagegen_result.py" \
  --run-dir /absolute/path/to/run \
  --job-id <job-id> \
  --source /absolute/path/to/generated-output.png \
  --allow-synthetic-test-source
```

5. Handle running-left (mirror if safe):

```bash
python "$SKILL_DIR/scripts/derive_running_left_from_running_right.py" \
  --run-dir /absolute/path/to/run \
  --confirm-appropriate-mirror \
  --decision-note "<why mirroring preserves this pet's identity>"
```

6. Finalize:

```bash
python "$SKILL_DIR/scripts/finalize_pet_run.py" \
  --run-dir /absolute/path/to/run \
  --allow-synthetic-test-sources \
  --package-dir /absolute/path/to/output/pets/<pet-name>
```

Expected output in run directory:
```text
run/
  pet_request.json
  imagegen-jobs.json
  prompts/
  decoded/
  frames/frames-manifest.json
  final/spritesheet.png
  final/spritesheet.webp
  final/validation.json
  qa/contact-sheet.png
  qa/review.json
  qa/run-summary.json
  qa/videos/*.mp4
```

Packaged pet output:
```text
<package-dir>/
  pet.json
  spritesheet.webp
```

## Repair Workflow

If finalization stops because row QA failed:

```bash
python "$SKILL_DIR/scripts/queue_pet_repairs.py" --run-dir /absolute/path/to/run
```

Then re-generate only the failed rows.

## Acceptance Criteria

- Final atlas is PNG or WebP, 1536x1872, transparent-capable, 192x208 cells
- Used cells are non-empty, unused cells are fully transparent
- Atlas follows the row/frame counts in `references/animation-rows.md`
- Contact sheet and preview videos have been produced
- `qa/review.json` has no errors
- `pet.json` and `spritesheet.webp` are in the package directory

## Rules

- Use Hermes's available image generator as the primary generation layer.
- Keep reference images attached/visible for the image generator.
- Attach layout guide images to every row-strip job.
- Use `delegate_task` for row-strip visual generation after the parent records the base image.
- Generate every normal visual job with the image generator.
- Only the base job may be prompt-only; every row job must attach grounding images.
- Delegate `running-right` first, then mirror `running-left` only when safe.
- Never substitute locally drawn/code-generated row strips for missing image generator outputs.
- Never manually mutate `imagegen-jobs.json`.
- Use the chroma key stored in `pet_request.json`.
- Keep the pet's silhouette, face, materials, palette, and props consistent across all rows.
- Enforce transparency and effects rules in every prompt.
