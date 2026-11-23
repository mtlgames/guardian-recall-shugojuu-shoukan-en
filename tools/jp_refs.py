"""Referenced Japanese strings outside every text range (the extractor's blind spot).

For the EXE and every code overlay: each u32 word or lui pair that points at the start of a NUL-ended run of text
holding Japanese, where that address lies outside the image's IMAGES ranges. Exit 1 if any is not in KNOWN.
With --built (build.py runs it on every patched tree): every referenced Japanese string, in or out of a range,
except the `status: data` records (debug printf formats): what the player could still see.
Usage: python -X utf8 tools/jp_refs.py [--built] [TREE]   (default: the dump tree work/iso/d1/tree)
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import script_io as sio

ROOT = Path(__file__).resolve().parents[1]
OVL = 0x80166218
# overlays with no extracted text (docs/re/text.md): scanned at their load base
OTHER = {"title": ("DATA/TITLE.BIN", 0x80162F88), "title2": ("DATA/TITLE2.BIN", OVL), "map02": ("DATA/MAP02.BIN", OVL),
         "menu": ("DATA/MENU.BIN", OVL), "japan": ("DATA/JAPAN.BIN", OVL), "call02": ("DATA/CALL02.BIN", OVL),
         "rsel": ("DATA/RSEL.BIN", OVL), "gd": ("DATA/GD.BIN", OVL), "dic": ("DATA/DIC.BIN", OVL),
         "cf": ("DATA/CF.BIN", OVL), "rep": ("DATA/REP.BIN", OVL), "tu": ("DATA/TU.BIN", OVL)}
KANA = re.compile(r"[぀-ヿ一-鿿ｦ-ﾟ]")
# (image, file offset): reason it stays Japanese
KNOWN = {}


def hits(tree, built=False):
    """Referenced Japanese strings outside the ranges (dump), or anywhere but the `status: data` records (built
    tree: every string a pointer still reaches must be English)."""
    out = []
    imgs = {k: (f, b, r) for k, (f, b, r) in sio.IMAGES.items()}
    imgs.update({k: (f, b, []) for k, (f, b) in OTHER.items()})
    skip = {}
    if built:
        for p in (ROOT / "script/exe").glob("*.json"):
            skip[p.stem] = {s["off"] for s in json.loads(p.read_text(encoding="utf-8"))["strings"]
                            if s.get("status") == "data"}
    for key, (fn, base, ranges) in imgs.items():
        path = Path(tree) / fn
        if fn.startswith("SLPS"):
            path = next(Path(tree).glob("SLPS_*"))  # disc 2: SLPS_012.98
        img = path.read_bytes()
        for ram, rs in sio.refs(img, base).items():
            o = ram - base
            if not 0 <= o < len(img) or not img[o]:
                continue
            if (o in skip.get(key, ()) if built else any(a <= o < b for a, b in ranges)):
                continue
            if o and img[o - 1] and sio.TEXT_RUN.fullmatch(img[o - 1:o]):
                continue  # points into the middle of a run
            end = img.find(b"\0", o)
            r = img[o:end if end >= 0 else len(img)]
            # kana/kanji only: full-width Latin is the English card titles (D11 CARD_TITLES)
            if sio.TEXT_RUN.fullmatch(r) and len(KANA.findall(r.decode("cp932", "replace"))) >= 2:
                out.append((key, o, r.decode("cp932", "replace"), [f"{k}{a:08X}" for k, a in rs]))
    return out


def main():
    built = "--built" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--built"]
    tree = args[0] if args else ROOT / "work/iso/d1/tree"
    bad = 0
    for key, o, s, rs in hits(tree, built):
        known = KNOWN.get((key, o))
        bad += not known
        print(f"{'known' if known else 'NEW  '} {key} 0x{o:X} {s!r} refs {' '.join(rs[:4])}" + (f"  ({known})" if known else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
