# Provenance

Base game/engine: CCDoom by Xella (https://github.com/Xella37/CCDoom), MIT
licensed -- see LICENSE.

## HUD images (images/gun, bgun, gunf, bgunf, heart, bheart, logo)

Converted from Freedoom (https://freedoom.github.io/), BSD-style licensed
original artwork -- see tools/COPYING-freedoom.txt. Freedoom is NOT id
Software's DOOM; it's a from-scratch free replacement asset set made
specifically to be reused like this, no id Software assets are involved.

Originals are kept in images_original/ for reference/rollback.

Source lumps used:
- gun / bgun     <- PISGA0 (pistol idle)
- gunf / bgunf   <- PISGB0 (pistol recoil), with the muzzle flash (PISFA0)
  baked directly into it via tools/composite_flash.py -- see note below
- heart / bheart <- STIMA0 (stimpack, standing in for the health icon)
- logo           <- M_DOOM (title wordmark), but see note below

The muzzle flash was originally its own pair of images (fire/bfire) drawn
as a separately-positioned overlay, which turned into a long, painful
back-and-forth trying to get its on-screen position right (wrong
coordinate space, CDN caching masking pushed fixes, etc.). Composited it
directly onto gunf/bgunf instead -- gunX/gunY never had a position bug, so
drawing one baked-together image there sidesteps the problem entirely.
fire/bfire and the debug-HUD/center-marker code that came out of that saga
have all been removed; tools/composite_flash.py regenerates gunf/bgunf
from the plain PISGB0 conversion + PISFA0 if either needs redoing.

To regenerate against a newer Freedoom release:
1. Download freedoom1.wad from https://github.com/freedoom/freedoom/releases
2. `python tools/freedoom_convert.py <path-to-freedoom1.wad> tools/converted_out`
3. Copy the results from tools/converted_out/ into images/ -- EXCEPT `logo`.
   The user explicitly wants the original CCDoom splash, not the converted
   M_DOOM one; it's been accidentally re-clobbered by a blanket copy loop
   twice already. Skip it, or diff against images_original/logo first.
4. Re-run `python tools/composite_flash.py .` (from the colossusdoom/ dir)
   to re-bake the flash onto the freshly-converted gunf/bgunf.

3D models (models/*) are unmodified -- they're simple hand-authored Pine3D
polygon data, not sprites, so there's nothing from a WAD to convert them
from without rewriting Pine3D to support billboarded/textured sprites,
which is out of scope here.

## Modifications for ColossusCraft, 2026
- Rebranded title/credit/end-game text in Doom.lua.
- Fixed a corrupted line (563) that broke on load.
- Fixed models/* loading to use the script's own directory instead of the
  filesystem root (only mattered once installed into a subfolder).
- Added install.lua (sequential downloader, avoids GitHub burst rate-limits).
- Added cheat codes: I = god mode, K = clear enemies, N = full heal.
- Swapped HUD images for Freedoom-derived ones (see above).

The in-game online highscore board still posts to Xella's own
doom.pine3d.cc API (unrelated to any of the above) -- set
`submitScore = false` near the top of Doom.lua to disable it.
