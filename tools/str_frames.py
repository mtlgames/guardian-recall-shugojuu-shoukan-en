"""Sample frames from PS1 STR movies extracted by dumpsxiso (2336-byte form-2 sectors) with ffmpeg.

    python -X utf8 tools/str_frames.py OUTDIR FILE.STR.. [--every 5] [--width 128]

Each sector gets a 2352-byte sync/header prefix so ffmpeg's psxstr demuxer reads it; frames land in
OUTDIR/<stem>_NNN.png. Needs ffmpeg on PATH.
"""
import argparse
import os
import subprocess
import tempfile

SYNC = b"\x00" + b"\xff" * 10 + b"\x00" + b"\x00\x00\x00\x02"


def to_raw(src, dst):
    with open(src, "rb") as f, open(dst, "wb") as o:
        while len(s := f.read(2336)) == 2336:
            o.write(SYNC + s)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--every", type=float, default=5)
    ap.add_argument("--width", type=int, default=128)
    ap.add_argument("--prefix", default="")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.join(tempfile.gettempdir(), "str_frames.str")
    for f in a.files:
        to_raw(f, tmp)
        stem = a.prefix + os.path.splitext(os.path.basename(f))[0]
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "psxstr", "-i", tmp, "-vf",
                            f"fps=1/{a.every},scale={a.width}:-1", os.path.join(a.out, stem + "_%03d.png")])
        if r.returncode:
            print("ffmpeg failed:", f)
    os.remove(tmp)


if __name__ == "__main__":
    main()
