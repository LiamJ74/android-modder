---
name: fal-assets
description: Generate original art, textures, icons and sound effects for an Android game mod with fal (fal.ai), sized and styled for mobile. Use when a mod needs new sprites, item/skill icons, tile textures, UI art or SFX. Covers matching the game's look, generating with `am fal` (every call logged to fal_manifest.jsonl for credit), and handing off to the asset-pipeline skill for conversion. Generated assets are the user's to ship; game assets are never redistributed.
---

# fal assets (mobile)

Make **original** art and audio that fit the game, then convert it to exactly what the engine loads. You own fal
output (under each model's license) — so it's shippable, unlike the game's own assets.

## Setup
- `FAL_KEY` in the environment (fal.ai). The fal MCP server, if configured for your agent, is an alternative to
  the REST path below.
- Decide the target first: pixel size, palette, outline, perspective (top-down? side? isometric?), and the
  screen density the art must end up at.

## Study the game's assets first
Pull a few of the game's own assets (on your owned copy) just to **measure** them — tile size, sprite
dimensions, atlas cell, palette, UI scale. You're matching a style, not copying files.

## Generate
- Image / icon: `am fal image "<prompt>" -o assets --size 512x512`
- Tiling texture: `am fal texture "<prompt>" -o assets` (adds "seamless tileable" to the prompt)
- Sound effect: `am fal sfx "<prompt>" --seconds 3 -o assets`
- Any model: `am fal run <model-id> -p prompt="..." -p key=value -o assets`

Every call appends to `assets/fal_manifest.jsonl` (model, prompt, params, output files) — that's your credits
list for the README.

## Prompting for mobile game art
- Ask for a **flat background or transparency** so cutout is clean: "on a plain white background", "centered,
  full body, game asset".
- For **icons**, ask for a consistent frame: same lighting, same angle, same margin, so a set looks uniform.
- For a **sprite set** across angles/frames, generate one strong concept, then keep consistency by reusing it as
  reference where the model supports it.
- Keep a consistent **palette** matching the game; name it in the prompt.

## Hand off
Send everything to the **asset-pipeline** skill: cut out, fit to the engine's exact size, pack atlases, emit
screen densities, and compress to ETC2/ASTC where needed.

## Rules
- Generate original assets; never launder the game's own art through a model.
- Credit fal and the models in the README ("Art/audio generated with fal (fal.ai) using <models>" — from
  `fal_manifest.jsonl`). Disclose AI use honestly.
