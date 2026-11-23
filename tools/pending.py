"""List the ids in tools/exe_pending.txt with their Japanese, English, English px and JP px (phase 7, D13).

    python -X utf8 tools/pending.py [PREFIX]      # e.g. exe.a63 ; sorted by id
"""
import sys

import font
import windows


def main(argv=None):
    pre = (argv if argv is not None else sys.argv[1:]) or [""]
    pend = set(windows._pending)
    glyphs = font.load_glyphs()
    for s in windows.records():
        if s["id"] in pend and s["id"].startswith(pre[0]):
            en = s.get("en", "")
            w = max(font.width(line, glyphs) for line in en.split("\n"))
            print(f"{s['id']}\t{windows.jp_px(s['jp'])}\t{w}\t{s['jp']!r}\t{en!r}")


if __name__ == "__main__":
    main()
