"""gr_text.py: Guardian Recall script codec (guess, being verified).

Bytes: 0x0A newline; 0x81-0x9F/0xE0-0xEF lead a Shift-JIS pair; 0xA1-0xDF a single byte shown as hiragana
(half-width katakana code points re-read as hiragana); other bytes < 0x20 are control codes, printed as [XX].
Usage: python tools/gr_text.py FILE START LEN
"""
import sys
import unicodedata


def hw_to_hira(b):
    k = unicodedata.normalize("NFKC", bytes([b]).decode("cp932"))  # half-width kata -> full-width kata
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in k)


def decode(data):
    out, i = [], 0
    while i < len(data):
        b = data[i]
        if (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF) and i + 1 < len(data):
            try:
                out.append(data[i:i + 2].decode("cp932"))
            except UnicodeDecodeError:
                out.append(f"[{b:02X}{data[i + 1]:02X}]")
            i += 2
        elif 0xA1 <= b <= 0xDF:
            out.append(hw_to_hira(b))
            i += 1
        elif b == 0x0A:
            out.append("\n")
            i += 1
        elif 0x20 <= b < 0x7F:
            out.append(chr(b))
            i += 1
        else:
            out.append(f"[{b:02X}]")
            i += 1
    return "".join(out)


if __name__ == "__main__":
    f, start, n = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
    with open(f, "rb") as fh:
        fh.seek(start)
        print(decode(fh.read(n)))
