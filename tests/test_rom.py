import pytest
from pathlib import Path

import check_rom

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.slow  # hashes 1.4 GB; the build checks it anyway
@pytest.mark.skipif(not (ROOT / "rom").is_dir(), reason="no dump in rom/")
def test_dump_matches_rom_sha1():
    check_rom.check()  # sys.exit on mismatch fails the test
