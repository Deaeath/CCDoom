# Provenance

Base game/engine: CCDoom by Xella (https://github.com/Xella37/CCDoom), MIT
licensed -- see LICENSE.

## HUD images (images/gun, bgun, gunf, bgunf, heart, bheart, fire, bfire, logo)

Converted from Freedoom (https://freedoom.github.io/), BSD-style licensed
original artwork -- see tools/COPYING-freedoom.txt. Freedoom is NOT id
Software's DOOM; it's a from-scratch free replacement asset set made
specifically to be reused like this, no id Software assets are involved.

Originals are kept in images_original/ for reference/rollback.

Source lumps used:
- gun / bgun     <- PISGA0 (pistol idle)
- gunf / bgunf   <- PISGB0 (pistol recoil)
- fire / bfire   <- PISFA0 (muzzle flash)
- heart / bheart <- STIMA0 (stimpack, standing in for the health icon)
- logo           <- M_DOOM (title wordmark)

To regenerate against a newer Freedoom release:
1. Download freedoom1.wad from https://github.com/freedoom/freedoom/releases
2. `python tools/freedoom_convert.py <path-to-freedoom1.wad> tools/converted_out`
3. Copy the results from tools/converted_out/ into images/

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
