#!/usr/bin/env python3
"""Bakes fire/bfire directly onto gunf/bgunf so the game only ever draws one
image at one already-correct position (gunX,gunY), instead of positioning
the flash as a separate overlay -- eliminates the whole class of bug where
fire and gun disagree about coordinate space.

Usage: composite_flash.py <colossusdoom_dir>
"""
import sys, os

def load(path):
    with open(path, 'rb') as f:
        text = f.read().decode('ascii')
    rows = text.replace('\r\n', '\n').split('\n')
    return [list(r) for r in rows]

def save(path, grid):
    with open(path, 'wb') as f:
        for row in grid:
            line = ''.join(row).rstrip()
            f.write(line.encode('ascii') + b'\r\n')

def composite(base_path, overlay_path, out_path, offset_x, offset_y):
    base = load(base_path)
    overlay = load(overlay_path)
    for oy, row in enumerate(overlay):
        ty = oy + offset_y
        if ty < 0:
            continue
        while len(base) <= ty:
            base.append([])
        for ox, ch in enumerate(row):
            if ch == ' ' or ch == '':
                continue
            tx = ox + offset_x
            if tx < 0:
                continue
            while len(base[ty]) <= tx:
                base[ty].append(' ')
            base[ty][tx] = ch
    save(out_path, base)
    print("%s + %s -> %s" % (base_path, overlay_path, out_path))

if __name__ == '__main__':
    d = sys.argv[1]
    # flash sits just above/overlapping the top of the gun sprite, roughly
    # centered on it horizontally
    composite(os.path.join(d, "images/gunf"), os.path.join(d, "images/fire"),
               os.path.join(d, "images/gunf"), 4, -2)
    composite(os.path.join(d, "images/bgunf"), os.path.join(d, "images/bfire"),
               os.path.join(d, "images/bgunf"), 10, -6)
