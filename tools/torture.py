"""Glyph torture build: every printable ASCII char through the generic UI (ring > UNIT names, map70 evd), txd
(charfile profile cf.0042, the one file 1 shows) and DIC (dictionary dic.0001) renderers. Then run tac_unit, opt_charfile_page and
opt_dictionary_page (tools/debug/one.py / regen.py) and check every glyph.

    python -X utf8 tools/torture.py            # marker build with the overrides
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASCII = "".join(chr(c) for c in range(0x21, 0x7F) if chr(c) != "&")  # & starts txd markup


def overrides():
    names = json.loads((ROOT / "script/evd/map70.json").read_text(encoding="utf-8"))["strings"]
    chunks = [ASCII[i:i + 14] for i in range(0, len(ASCII), 14)]
    # the UNIT list shows every other map70 name (masters, not their guardians)
    qa = {names[2 * i]["id"]: c for i, c in enumerate(chunks)}
    lines = [ASCII[i:i + 19] for i in range(0, len(ASCII), 19)]
    qa["cf.0042"] = "&s(165,87)&c(7)&g(13,16)" + "&n()".join(lines)
    qa["dic.0001"] = "Aso&n()&n()" + "&n()".join(ASCII[i:i + 16] for i in range(0, len(ASCII), 16)) + "&n()a  b"
    return qa


if __name__ == "__main__":
    args = [sys.executable, "-X", "utf8", str(ROOT / "build.py"), "--marker"]
    for k, v in overrides().items():
        args += ["--qa", f"{k}={v}"]
    sys.exit(subprocess.run(args, cwd=ROOT).returncode)
