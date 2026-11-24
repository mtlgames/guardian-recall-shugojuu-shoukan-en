"""tx03_png.py: decode one TX03 stream to a grey PNG (4bpp indices x17, or 8bpp raw with --8).
python -X utf8 tools/tx03_png.py FILE OFFSET OUT.png [--8]"""
import argparse
import struct

import numpy as np
from PIL import Image

import tx03

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("offset", type=lambda s: int(s, 0))
ap.add_argument("out")
ap.add_argument("--8", dest="b8", action="store_true")
a = ap.parse_args()
d, end = tx03.decompress(open(a.file, "rb").read(), a.offset)
w, h = struct.unpack_from("<hh", d)
b = np.frombuffer(d[4:], np.uint8).reshape(h, w)
px = b if a.b8 else np.stack([b & 15, b >> 4], -1).reshape(h, -1) * 17
Image.fromarray(px.astype(np.uint8)).save(a.out)
print(f"{w} bytes x {h} rows, stream {end - a.offset:#x}")
