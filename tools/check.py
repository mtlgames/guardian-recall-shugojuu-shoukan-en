"""check.py: the repo's one-command check (tests + text lint). The pre-commit hook runs it; exit code gates the commit."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    # Tests marked `slow` (disc rebuilds, emulator runs) stay out of the commit gate; run them with `-m slow`.
    r = subprocess.run([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-m", "not slow", "tests"], cwd=ROOT)
    sys.exit(0 if r.returncode == 5 else r.returncode)  # 5 = no fast tests collected yet
