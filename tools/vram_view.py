"""vram_view.py VRAM.bin OUT_PREFIX [x y w h]: PS1 VRAM (1024x512 16bpp) -> OUT_PREFIX_15.png (direct colour)
and OUT_PREFIX_4.png (each halfword as four 4bpp grey pixels, 4096 px wide), optionally cropped (VRAM halfword coords)."""
import sys

import numpy as np
from PIL import Image

if __name__ == "__main__":
    # PCSX-Redux nightly 2026-11 writes 2 MB; the first 1 MB is VRAM, the rest is 0xFFFF filler
    v = np.frombuffer(open(sys.argv[1], "rb").read()[:0x100000], "<u2").reshape(512, 1024)
    x, y, w, h = (int(a, 0) for a in sys.argv[3:7]) if len(sys.argv) > 6 else (0, 0, 1024, 512)
    v = v[y:y + h, x:x + w]
    rgb = np.stack([(v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3], -1).astype(np.uint8)
    Image.fromarray(rgb).save(sys.argv[2] + "_15.png")
    n4 = np.stack([(v >> s) & 15 for s in (0, 4, 8, 12)], -1).reshape(v.shape[0], -1) * 17
    Image.fromarray(n4.astype(np.uint8)).save(sys.argv[2] + "_4.png")
