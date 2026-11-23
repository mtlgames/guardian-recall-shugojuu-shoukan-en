import hashlib
from pathlib import Path

import pytest

import build

ROOT = Path(__file__).resolve().parents[1]
WANT = {ROOT / name.strip(): sha for sha, name in
        (l.split(None, 1) for l in (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines()
         if l.strip() and not l.startswith("#"))}


@pytest.mark.slow  # dumps and repacks 1.4 GB
@pytest.mark.skipif(not (ROOT / "rom").is_dir(), reason="no dump in rom/")
@pytest.mark.parametrize("n", build.DISCS)
def test_unpatched_rebuild_is_byte_identical(n, tmp_path):
    out = build.build_disc(n, tmp_path, patched=False)
    with open(out, "rb") as f:
        got = hashlib.file_digest(f, "sha1").hexdigest()
    assert got == WANT[build.orig_cue(n).with_suffix(".bin")]
