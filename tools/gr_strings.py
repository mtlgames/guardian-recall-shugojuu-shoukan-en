"""gr_strings.py FILE.. [--min N]: NUL-terminated strings in the game's encoding (SJIS + half-width-as-hiragana).

A string = >= N chars of SJIS pairs / 0xA1-0xDF / \\n / [01] / printable ASCII, holding at least one SJIS pair or
half-width byte, ending at 0x00. Prints FILE OFFSET LEN TEXT. Most hits in code are real strings; noise is short.
"""
import argparse
import re

from gr_text import decode

STR = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\xa1-\xdf]|[\x0a\x01\x20-\x7e])+(?=\x00)")


def strings(data, n=3):
    for m in STR.finditer(data):
        b = m.group()
        if len(re.findall(rb"[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]", b)) * 2 + len(re.findall(rb"[\xa1-\xdf]", b)) < 2 * n:
            continue
        try:
            t = decode(b)
        except Exception:
            continue
        yield m.start(), len(b), t


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--min", type=int, default=3)
    a = ap.parse_args()
    for f in a.files:
        d = open(f, "rb").read()
        for off, n, t in strings(d, a.min):
            print(f"{f}\t{off:#07x}\t{n}\t{t!r}")
