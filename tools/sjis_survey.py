"""sjis_survey.py DIR [min_chars]: count Shift-JIS runs (with kana) per file, to find where text lives."""
import re
import sys
from pathlib import Path

# 2-byte SJIS chars (81-9F/E0-EF lead) plus ASCII digits/punct; a run must hold kana (82 9F-F1 hiragana, 83 40-96 katakana).
RUN = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]){%d,}")
KANA = re.compile(rb"\x82[\x9f-\xf1]|\x83[\x40-\x96]")


def runs(data, n):
    for m in RUN.finditer(data):
        b = m.group()
        if len(KANA.findall(b)) * 2 >= len(b) // 4:  # >= ~1/4 kana keeps sentences, drops pixel noise
            try:
                yield m.start(), b.decode("cp932")
            except UnicodeDecodeError:
                pass


if __name__ == "__main__":
    root = Path(sys.argv[1])
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    RUN = re.compile(RUN.pattern.replace(b"%d", str(n).encode()))
    for f in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.upper() not in (".XA", ".STR", ".VB")):
        hits = list(runs(f.read_bytes(), n))
        if hits:
            print(f"{len(hits):6d} {sum(len(t) for _, t in hits):8d}ch  {f.relative_to(root)}  e.g. {hits[0][0]:#x} {hits[0][1][:20]}")
