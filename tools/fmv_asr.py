"""Transcribe the voiced STR movies (FMV subtitles, D18) with faster-whisper large-v3.

    python -X utf8 tools/fmv_asr.py [STEM..] [--force]     -> work/fmv/asr/<STEM>.tsv (start, end, ja)

One-off step: the transcript is a draft that gfx/fmv/<STEM>.tsv is edited from (names fixed from glossary.md, lines
split or merged by ear), so a re-run never touches gfx/. GPU: CUDA DLLs from
`pip install --target work/cuda nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"`; without them it runs on the CPU.
Audio comes out of the movie with ffmpeg (str_frames.to_raw: psxstr demuxer), mono 16 kHz.
"""
import argparse
import csv
import glob
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import str_frames  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "work/fmv/asr"
SKIP = {"STAFF", "XING"}        # credits (G15) and the publisher logo
# names and terms the movies say, so whisper writes them the way glossary.md has them
PROMPT = ("天城美由紀、炎真由、大地裕子、周防ちかな、神門一門、守護獣、召喚、荏狗覇菟、龍鬼妃、天闘衆、聖ゆかり、海原美里、"
          "西苑寺麗子、北斗めぐみ、南城知美、東聡美、半澤由美、武神。")


def movies(names=()):
    out = {}
    for d in ("d1", "d2"):
        for p in sorted((ROOT / f"work/iso/{d}/tree/STR").glob("*.STR")):   # build.py's pristine dump
            if p.stem not in SKIP and (not names or p.stem in names):
                out.setdefault(p.stem, p)          # OP_* and XING are per disc; the rest are on one disc only
    return out


def audio(path):
    raw = OUT / "tmp.raw"
    str_frames.to_raw(path, raw)
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-f", "psxstr", "-i", str(raw), "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    raw.unlink()
    return np.frombuffer(pcm, "<i2").astype(np.float32) / 32768


def model():
    for d in glob.glob(str(ROOT / "work/cuda/nvidia/*/bin")):
        os.add_dll_directory(d)
        os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]
    from faster_whisper import WhisperModel
    try:
        return WhisperModel("large-v3", device="cuda", compute_type="float16")
    except Exception:  # noqa: BLE001 - no CUDA: slow but works
        return WhisperModel("large-v3", device="cpu", compute_type="int8")


def transcribe(m, pcm, vad=True):
    segs, _ = m.transcribe(pcm, language="ja", beam_size=5, vad_filter=vad, word_timestamps=True,
                           initial_prompt=PROMPT, condition_on_previous_text=False)
    rows = []
    for s in segs:
        w = [x for x in (s.words or []) if x.word.strip()]
        # word times are tighter than the segment's (which can run on through music)
        a, b = (w[0].start, w[-1].end) if w else (s.start, s.end)
        rows.append((f"{a:.2f}", f"{b:.2f}", s.text.strip()))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stems", nargs="*")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-vad", action="store_true",
                    help="-> work/fmv/asr_novad/: VAD drops short shouts over music (SYO01, M20B15); no VAD can "
                         "hallucinate over music, so diff it against the VAD run by hand")
    a = ap.parse_args()
    out = OUT.with_name("asr_novad") if a.no_vad else OUT
    out.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    m = None
    for stem, path in movies(a.stems).items():
        dst = out / f"{stem}.tsv"
        if dst.exists() and not a.force:
            continue
        m = m or model()
        rows = transcribe(m, audio(path), not a.no_vad)
        with open(dst, "w", encoding="utf-8", newline="") as f:
            csv.writer(f, delimiter="\t", lineterminator="\n").writerows([("start", "end", "ja"), *rows])
        print(stem, len(rows), "lines")


if __name__ == "__main__":
    main()
