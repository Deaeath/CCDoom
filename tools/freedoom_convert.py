#!/usr/bin/env python3
"""Converts specific Freedoom (BSD-licensed) sprite lumps into CC:Tweaked
paintutils .nfp images for use as HUD assets in ColossusCraft Doom.

Freedoom's assets are its own original artwork (not id Software's), made
explicitly to be freely reusable -- see freedoom_src/freedoom-0.13.0/COPYING.txt.

Doom "patch" format (used by all sprites here): int16 width, height,
leftoffset, topoffset, then `width` int32 column offsets, then per column a
list of posts: byte topdelta (0xFF ends the column), byte length, 1 pad byte,
`length` indexed-color bytes, 1 pad byte.

Usage: freedoom_convert.py <wad> <out_dir>
"""
import struct
import sys
import os

CC_PALETTE = [
    ("white",     0xF0, 0xF0, 0xF0),
    ("orange",    0xF2, 0xB2, 0x33),
    ("magenta",   0xE5, 0x7F, 0xD8),
    ("lightBlue", 0x99, 0xB2, 0xF2),
    ("yellow",    0xDE, 0xDE, 0x6C),
    ("lime",      0x7F, 0xCC, 0x19),
    ("pink",      0xF2, 0xB2, 0xCC),
    ("gray",      0x4C, 0x4C, 0x4C),
    ("lightGray", 0x99, 0x99, 0x99),
    ("cyan",      0x4C, 0x99, 0xB2),
    ("purple",    0xB2, 0x66, 0xE5),
    ("blue",      0x33, 0x66, 0xCC),
    ("brown",     0x7F, 0x66, 0x4C),
    ("green",     0x57, 0xA6, 0x4E),
    ("red",       0xCC, 0x4C, 0x4C),
    ("black",     0x11, 0x11, 0x11),
]
NFP_CHARS = "0123456789abcdef"


def read_wad(path):
    with open(path, 'rb') as f:
        data = f.read()
    ident, numlumps, infotableofs = struct.unpack_from('<4sii', data, 0)
    lumps = {}
    for i in range(numlumps):
        filepos, size, name = struct.unpack_from('<ii8s', data, infotableofs + i * 16)
        name = name.rstrip(b'\x00').decode('ascii', 'replace')
        lumps[name] = (filepos, size)
    return data, lumps


def read_palette(data, lumps):
    pos, size = lumps['PLAYPAL']
    pal = []
    for i in range(256):
        r, g, b = struct.unpack_from('<BBB', data, pos + i * 3)
        pal.append((r, g, b))
    return pal


def read_patch(data, lumps, name):
    pos, size = lumps[name]
    width, height, left, top = struct.unpack_from('<hhhh', data, pos)
    col_offsets = struct.unpack_from('<%di' % width, data, pos + 8)
    grid = [[None] * width for _ in range(height)]
    for x in range(width):
        offset = pos + col_offsets[x]
        while True:
            topdelta = data[offset]
            offset += 1
            if topdelta == 0xFF:
                break
            length = data[offset]
            offset += 1
            offset += 1  # padding byte
            for y in range(length):
                if topdelta + y < height:
                    grid[topdelta + y][x] = data[offset + y]
            offset += length
            offset += 1  # padding byte
    return width, height, grid


def nearest_cc_char(r, g, b):
    best_i, best_d = 0, None
    for i, (_, cr, cg, cb) in enumerate(CC_PALETTE):
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if best_d is None or d < best_d:
            best_d, best_i = d, i
    return NFP_CHARS[best_i]


def to_char_grid(width, height, grid, palette):
    out = [[' '] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            idx = grid[y][x]
            if idx is None:
                continue
            r, g, b = palette[idx]
            out[y][x] = nearest_cc_char(r, g, b)
    return out


_LUMA = {NFP_CHARS[i]: r + g + b for i, (_, r, g, b) in enumerate(CC_PALETTE)}


def resize(char_grid, src_w, src_h, dst_w, dst_h, prefer_bright=False):
    out = []
    for dy in range(dst_h):
        row = []
        y0 = dy * src_h // dst_h
        y1 = max(y0 + 1, (dy + 1) * src_h // dst_h)
        for dx in range(dst_w):
            x0 = dx * src_w // dst_w
            x1 = max(x0 + 1, (dx + 1) * src_w // dst_w)
            counts = {}
            for yy in range(y0, min(y1, src_h)):
                for xx in range(x0, min(x1, src_w)):
                    c = char_grid[yy][xx]
                    counts[c] = counts.get(c, 0) + 1
            # majority vote, but prefer non-space if it's at least a third present
            non_space = {c: n for c, n in counts.items() if c != ' '}
            if non_space and sum(non_space.values()) * 3 >= sum(counts.values()):
                if prefer_bright:
                    # small icons (muzzle flash) lose their bright core to
                    # majority-vote against dim anti-aliasing pixels -- pick
                    # the brightest color present instead of the most common one
                    row.append(max(non_space, key=lambda c: _LUMA[c]))
                else:
                    row.append(max(non_space, key=non_space.get))
            else:
                row.append(' ')
        out.append(row)
    return out


def center_horizontally(char_grid, width):
    # Bounding-box centering does nothing when content already touches both
    # edges (common once heavily downsampled) -- center on the brightness-
    # weighted centroid instead, so the visual "mass" of the sprite ends up
    # centered even if a few outlier pixels still touch an edge.
    total_weight, weighted_x = 0.0, 0.0
    for row in char_grid:
        for x, c in enumerate(row):
            if c != ' ':
                w = _LUMA.get(c, 1) + 1  # brighter pixels pull the centroid more
                weighted_x += x * w
                total_weight += w
    if total_weight == 0:
        return char_grid
    centroid = weighted_x / total_weight
    shift = round(width / 2.0 - 0.5 - centroid)
    if shift == 0:
        return char_grid
    out = []
    for row in char_grid:
        new_row = [' '] * width
        for x, c in enumerate(row):
            if c == ' ':
                continue
            nx = x + shift
            if 0 <= nx < width:
                new_row[nx] = c
        out.append(new_row)
    return out


def write_nfp(path, char_grid):
    with open(path, 'wb') as f:
        for row in char_grid:
            line = ''.join(row).rstrip()
            f.write(line.encode('ascii') + b'\r\n')


def convert(data, lumps, palette, lump_name, dst_w, dst_h, out_path, prefer_bright=False):
    w, h, grid = read_patch(data, lumps, lump_name)
    chars = to_char_grid(w, h, grid, palette)
    resized = resize(chars, w, h, dst_w, dst_h, prefer_bright=prefer_bright)
    resized = center_horizontally(resized, dst_w)
    write_nfp(out_path, resized)
    print("%s (%dx%d) -> %s (%dx%d)" % (lump_name, w, h, out_path, dst_w, dst_h))


if __name__ == '__main__':
    wad_path, out_dir = sys.argv[1], sys.argv[2]
    data, lumps = read_wad(wad_path)
    palette = read_palette(data, lumps)

    jobs = [
        ("PISGA0", 15, 10, "gun"),
        ("PISGA0", 32, 30, "bgun"),
        ("PISGB0", 15, 10, "gunf"),
        ("PISGB0", 32, 30, "bgunf"),
        ("STIMA0", 5, 4, "heart"),
        ("STIMA0", 10, 11, "bheart"),
        # NOTE: logo intentionally NOT generated here. User wants the
        # original CCDoom splash, not Freedoom's M_DOOM -- it's been
        # re-clobbered by batch copy loops three times already. There is no
        # "logo" output from this script anymore specifically so that
        # mistake becomes structurally impossible instead of relying on
        # remembering to skip it.
        ("POSSA1", 8, 14, "enemy1_near"),   # zombieman, billboard sprite
        ("POSSA1", 4, 6, "enemy1_far"),
        ("TROOA1", 9, 14, "enemy2_near"),   # imp, billboard sprite
        ("TROOA1", 4, 6, "enemy2_far"),
        ("STBAR", 51, 5, "statusbar"),      # classic Doom status bar background
        ("STBAR", 51, 10, "bstatusbar"),
        ("SPOSA1", 8, 14, "enemy3_near"),   # sergeant (shotgun guy), billboard sprite
        ("SPOSA1", 4, 6, "enemy3_far"),
        ("SARGA1", 10, 12, "enemy4_near"),  # demon/pinky, billboard sprite
        ("SARGA1", 5, 6, "enemy4_far"),
        ("HEADA1", 10, 10, "enemy5_near"),  # cacodemon, billboard sprite
        ("HEADA1", 5, 5, "enemy5_far"),
    ]
    for d in range(10):
        jobs.append(("STTNUM%d" % d, 3, 4, "digit%d" % d))
        jobs.append(("STTNUM%d" % d, 3, 8, "bdigit%d" % d))
    jobs.append(("STTPRCNT", 3, 4, "digitpct"))
    jobs.append(("STTPRCNT", 3, 8, "bdigitpct"))
    os.makedirs(out_dir, exist_ok=True)
    for lump, w, h, outname in jobs:
        if outname == "heart_UNUSED":
            continue
        bright = outname in ("fire", "bfire")
        convert(data, lumps, palette, lump, w, h, os.path.join(out_dir, outname), prefer_bright=bright)
