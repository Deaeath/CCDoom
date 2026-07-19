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


def resize(char_grid, src_w, src_h, dst_w, dst_h):
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
                row.append(max(non_space, key=non_space.get))
            else:
                row.append(' ')
        out.append(row)
    return out


def write_nfp(path, char_grid):
    with open(path, 'wb') as f:
        for row in char_grid:
            line = ''.join(row).rstrip()
            f.write(line.encode('ascii') + b'\r\n')


def convert(data, lumps, palette, lump_name, dst_w, dst_h, out_path):
    w, h, grid = read_patch(data, lumps, lump_name)
    chars = to_char_grid(w, h, grid, palette)
    resized = resize(chars, w, h, dst_w, dst_h)
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
        ("PISFA0", 5, 4, "heart_UNUSED"),  # placeholder, overwritten below
        ("STIMA0", 5, 4, "heart"),
        ("STIMA0", 10, 11, "bheart"),
        ("PISFA0", 3, 3, "fire"),
        ("PISFA0", 6, 9, "bfire"),
        ("M_DOOM", 56, 18, "logo"),
    ]
    os.makedirs(out_dir, exist_ok=True)
    for lump, w, h, outname in jobs:
        if outname == "heart_UNUSED":
            continue
        convert(data, lumps, palette, lump, w, h, os.path.join(out_dir, outname))
