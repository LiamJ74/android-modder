---
name: asset-pipeline
description: Turn generated or source art into engine-ready Android assets — cut out backgrounds, fit to exact sprite sizes (nearest-neighbour for pixel art), pack texture atlases with a JSON map, emit drawable-mdpi..xxxhdpi screen densities, and compress to ETC2/ASTC. Use after fal-assets, or whenever a mod's art must match the game's exact size, atlas layout, screen density or texture format. Pure-Pillow operations plus SDK compressors; no device needed.
---

# Asset pipeline (mobile)

Get the art into exactly the shape the engine loads. Wrong size, wrong density or wrong format is the usual
reason a swapped asset looks off or doesn't show. All of this runs locally with `am sprite`.

## Measure the target first
From the game's own assets (studied during recon): the exact pixel size, the atlas cell size and coordinates,
the palette, and which **screen densities** the game ships (`res/drawable-mdpi` … `-xxxhdpi`) or the texture
format the engine expects (raw PNG, ETC2, ASTC).

## Operations
- **Cut out** a background to transparency (floods from the corners):
  `am sprite cutout art.png -t 24 -o art_cut.png`
- **Fit** to an exact size — nearest-neighbour for pixel art, Lanczos otherwise:
  `am sprite fit art_cut.png 64x64 --pixel -o frame.png`
- **Atlas** a folder of frames into one sheet + a JSON frame map (coords/cell/cols):
  `am sprite atlas frames/ -o atlas.png` (force a cell with `--cell 64x64`)
- **Screen densities** — emit every Android bucket from one source:
  `am sprite densities icon.png --base mdpi -o drawable` → `drawable-mdpi/…` through `drawable-xxxhdpi/…`
- **Compress** to the engine's texture format when it wants compressed input:
  `am sprite compress tex.png --format etc2` (etc2tool, from the SDK) or `--format astc` (astcenc)

## Recipes
- **libGDX / TexturePacker atlas:** keep each sprite at the original region size so the `.atlas` still matches;
  `am sprite fit` to that size, or rebuild the sheet with `am sprite atlas` and update the `.atlas` coords.
- **Android drawables (Java/Kotlin games):** swap a drawable at the **same name** in every `drawable-*` bucket;
  use `am sprite densities` so each bucket gets the right resolution.
- **Unity sprites:** match the imported texture's pixels-per-unit and size; swap inside the AssetBundle at the
  same dimensions.
- **Pixel art:** generate larger on a flat background, cut out, then one nearest-neighbour `fit` to the target —
  never scale a pixel sprite with a smooth filter.

## Rules
- These are **your** assets going in. Don't repackage the game's extracted art.
- Keep the `fal_manifest.jsonl` with the assets so credits stay accurate.
