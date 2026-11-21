"""tx03_sweep.py FILE OUTDIR [--bpp 4|8]: decode every TX03 stream in FILE, save each as a grey PNG named by offset,
and print an index (offset, w, h, packed size) plus every stream that failed to decode, with the reason."""
import argparse
import os
import struct

import numpy as np
from PIL import Image

import tx03


def to_img(out, bpp):
    w, h = struct.unpack_from("<hh", out)
    a = np.frombuffer(out[4:4 + w * h], np.uint8).reshape(h, w)
    if bpp == 4:
        a = np.stack([a & 15, a >> 4], -1).reshape(h, w * 2) * 17
    return Image.fromarray(a.astype(np.uint8))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("outdir")
    ap.add_argument("--bpp", type=int, default=4)
    a = ap.parse_args()
    d = open(a.file, "rb").read()
    os.makedirs(a.outdir, exist_ok=True)
    i, ok = d.find(b"TX03"), 0
    while i >= 0:
        try:
            out, end = tx03.decompress(d, i)
            w, h = struct.unpack_from("<hh", out)
            if not (0 < w <= 2048 and 0 < h <= 1024):
                raise ValueError(f"size {w}x{h}")
            to_img(out, a.bpp).save(os.path.join(a.outdir, f"{i:08x}.png"))
            print(f"{i:#09x}\t{w}\t{h}\t{end - i:#x}")
            ok += 1
        except Exception as e:  # report, never drop silently
            print(f"{i:#09x}\tFAIL\t{type(e).__name__}: {e}")
        i = d.find(b"TX03", i + 4)
    print(f"# decoded {ok}")
