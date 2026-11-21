"""PS1 TIM -> PNG (4/8/16/24 bpp; CLUT 0 for paletted images, others side by side with --all-cluts).

    python -X utf8 tools/tim.py FILE.tim.. --out DIR [--all-cluts]
"""
import argparse
import os
import struct

from PIL import Image


def rgb15(c):
    return ((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3, 0 if c == 0 else 255)


def read(b):
    """(width, height, rows of pixel indices or RGBA, list of CLUTs or None, fb pos)."""
    magic, flags = struct.unpack_from("<II", b)
    assert magic == 0x10, "not a TIM"
    bpp = flags & 3
    p = 8
    cluts = None
    if flags & 8:
        n, cx, cy, cw, ch = struct.unpack_from("<I4H", b, p)
        raw = struct.unpack_from(f"<{cw * ch}H", b, p + 12)
        cluts = [[rgb15(c) for c in raw[i * cw:(i + 1) * cw]] for i in range(ch)]
        p += n
    n, x, y, w16, h = struct.unpack_from("<I4H", b, p)
    data = b[p + 12:p + n]
    if bpp == 0:
        w = w16 * 4
        px = [(data[i // 2] >> (4 * (i & 1))) & 15 for i in range(w * h)]
    elif bpp == 1:
        w = w16 * 2
        px = list(data[:w * h])
    elif bpp == 2:
        w = w16
        px = [rgb15(c) for c in struct.unpack_from(f"<{w * h}H", data)]
    else:
        w = w16 * 2 // 3
        px = [tuple(data[i * 3:i * 3 + 3]) + (255,) for i in range(w * h)]
    return w, h, px, cluts, (x, y)


def to_image(b, clut=0):
    w, h, px, cluts, _ = read(b)
    img = Image.new("RGBA", (w, h))
    if cluts is not None:
        pal = cluts[min(clut, len(cluts) - 1)]
        px = [pal[i] if i < len(pal) else (255, 0, 255, 255) for i in px]
    img.putdata(px)
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--all-cluts", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in a.files:
        b = open(f, "rb").read()
        try:
            _, _, _, cluts, _ = read(b)
            n = len(cluts) if (cluts and a.all_cluts) else 1
            imgs = [to_image(b, c) for c in range(n)]
        except Exception as e:  # noqa: BLE001 - report every skipped file
            print("skip", f, e)
            continue
        img = imgs[0]
        if n > 1:
            img = Image.new("RGBA", (img.width * n, img.height))
            for i, im in enumerate(imgs):
                img.paste(im, (i * im.width, 0))
        bg = Image.new("RGBA", img.size, (40, 40, 80, 255))
        bg.alpha_composite(img)
        bg.convert("RGB").save(os.path.join(a.out, os.path.basename(f) + ".png"))


if __name__ == "__main__":
    main()
