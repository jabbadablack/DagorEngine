#!/usr/bin/env python3
"""Writes the placeholder textures the renderer needs (stars, moon, strata_clouds_simple, the paint palette
assets_color_global_tex_palette) as TGA files here.

They are plain stand-ins so the game renders from its first build: replace them with real art (keep the names, the
renderer looks them up by name) and delete this script. Deterministic: the same files every run."""
import math
import os
import random
import struct

HERE = os.path.dirname(os.path.abspath(__file__))


def write_tga(name, w, h, pixel, gray=False):
  """pixel(x, y) -> (r, g, b, a) in 0..255; RLE compressed (packets end at rows), top-left origin;
  gray writes 8 bit grayscale (r only)"""
  cb = 1 if gray else 4
  with open(os.path.join(HERE, name + '.tga'), 'wb') as f:
    f.write(struct.pack('<BBBHHBHHHHBB', 0, 0, 11 if gray else 10, 0, 0, 0, 0, 0, w, h, cb * 8, 0x20 | (0 if gray else 8)))
    for y in range(h):
      px = []
      for x in range(w):
        r, g, b, a = pixel(x, y)
        px.append(bytes((r,)) if gray else bytes((b, g, r, a)))
      x, out = 0, bytearray()
      while x < w:
        run = 1
        while x + run < w and run < 128 and px[x + run] == px[x]:
          run += 1
        if run > 1:
          out += bytes((0x80 | (run - 1),)) + px[x]
          x += run
          continue
        start = x
        while x < w and x - start < 128 and (x + 1 >= w or px[x + 1] != px[x]):
          x += 1
        out += bytes((x - start - 1,)) + b''.join(px[start:x])
      f.write(out)


def stars():
  rnd = random.Random(1)
  w, h = 1024, 512
  sky = bytearray(w * h)
  for _ in range(4000):
    x, y = rnd.randrange(w), rnd.randrange(h)
    sky[y * w + x] = max(sky[y * w + x], int(255 * rnd.random() ** 3))
  write_tga('stars', w, h, lambda x, y: (sky[y * w + x],) * 3 + (255,), gray=True)


def moon():
  n = 256
  def pixel(x, y):
    d = math.hypot(x + 0.5 - n / 2, y + 0.5 - n / 2) / (n / 2)
    v = int(220 * max(0.0, min(1.0, (1.0 - d) * 12)))
    return (v, v, v, v)
  write_tga('moon', n, n, pixel)


def strata_clouds():
  n, cells = 512, 8
  rnd = random.Random(2)
  grid = [[rnd.random() for _ in range(cells)] for _ in range(cells)]
  def smooth(t):
    return t * t * (3 - 2 * t)
  def noise(x, y):  # tileable value noise
    gx, gy = x * cells / n, y * cells / n
    ix, iy = int(gx), int(gy)
    fx, fy = smooth(gx - ix), smooth(gy - iy)
    v = lambda i, j: grid[(iy + j) % cells][(ix + i) % cells]
    return (v(0, 0) * (1 - fx) + v(1, 0) * fx) * (1 - fy) + (v(0, 1) * (1 - fx) + v(1, 1) * fx) * fy
  write_tga('strata_clouds_simple', n, n, lambda x, y: (int(255 * noise(x, y)),) * 3 + (255,), gray=True)


def paint_palette():
  write_tga('assets_color_global_tex_palette', 64, 64, lambda x, y: (255, 255, 255, 255))  # white: no tint


if __name__ == '__main__':
  stars()
  moon()
  strata_clouds()
  paint_palette()
