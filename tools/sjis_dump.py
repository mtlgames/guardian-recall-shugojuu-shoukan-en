"""sjis_dump.py FILE [min_chars] [start] [end]: print each Shift-JIS run (offset, text), using sjis_survey's filter."""
import re
import sys
from pathlib import Path

import sjis_survey

if __name__ == "__main__":
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    lo = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0
    hi = int(sys.argv[4], 0) if len(sys.argv) > 4 else 1 << 40
    sjis_survey.RUN = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]){" + str(n).encode() + rb",}")
    for off, t in sjis_survey.runs(Path(sys.argv[1]).read_bytes(), n):
        if lo <= off < hi:
            print(f"{off:#09x} {t}")
