"""build.py: rebuild both discs into build/disc{1,2}/ (checks the dump against rom.sha1 first).

Pristine file trees are dumped once into work/iso/d<N>/ (dumpsxiso), copied to work/build/d<N>/, patched there and
repacked with mkpsxiso. With no patches the output is byte-identical to the dump (tests/test_identity.py)."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402

MKPSXISO = ROOT / "tools/mkpsxiso/mkpsxiso-2.30-win64"
DISCS = (1, 2)


def orig_cue(n):
    return ROOT / f"rom/Guardian Recall - Shugojuu Shoukan (Japan) (Disc {n}).cue"


def dump(n):
    """Pristine tree + layout.xml of disc n in work/iso/d<n>/ (made once)."""
    d = ROOT / f"work/iso/d{n}"
    if not (d / "layout.xml").is_file():
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
        subprocess.run([MKPSXISO / "dumpsxiso.exe", "-q", "-x", d / "tree", "-s", d / "layout.xml", orig_cue(n)],
                       check=True)
    return d


def patch(n, tree):
    """Write the translation into disc n's file tree. Nothing yet: phase 7 inserts text here."""


def build_disc(n, out_dir, patched=True):
    src = dump(n)
    work = ROOT / f"work/build/d{n}"
    shutil.rmtree(work, ignore_errors=True)
    # shortcut: full 0.7 GB copy per disc per build, fine at a few seconds; overlay only patched files if it drags
    shutil.copytree(src, work)
    if patched:
        patch(n, work / "tree")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"Guardian Recall - Shugojuu Shoukan (English) (Disc {n})"
    for old in out_dir.glob("*.bin"):
        old.unlink()
    for old in out_dir.glob("*.cue"):
        old.unlink()
    # relative -o/-c from cwd=out_dir keep the cue's FILE line a bare file name
    subprocess.run([MKPSXISO / "mkpsxiso.exe", "-q", "-y", "-o", f"{stem}.bin", "-c", f"{stem}.cue",
                    work / "layout.xml"], check=True, cwd=out_dir)
    return out_dir / f"{stem}.bin"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--identity", action="store_true", help="skip patching (output must equal the dump)")
    a = ap.parse_args()
    check_rom.check()
    for n in DISCS:
        print(build_disc(n, ROOT / f"build/disc{n}", patched=not a.identity))
