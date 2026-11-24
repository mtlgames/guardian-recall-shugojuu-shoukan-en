"""Release gate + package (references/pipeline.md §Release). Never publishes anything.

    python -X utf8 tools/release.py [--force]

Stops at the first failure: check.py -> build.py (plain: no --qa/--marker, so no debug text) -> smoke (disc 1) ->
tools/jp_scan.py -> qa_gate check on every work/qa/**/manifest.tsv (each records the build its tour ran on, so a
build nobody toured fails here: re-run the tour, `qa_gate init --build`, verdicts) -> textcover -> docs/polish.md all
ticked -> no template placeholder in README.md -> xdelta3 per disc (-B image size), re-applied to the original and
compared -> release/<SLUG>_v<VERSION>.zip (patches + README.txt, stored). Refuses to overwrite an existing
version's zip without --force.
"""
import hashlib
import re
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

PY = [sys.executable, "-X", "utf8"]
S = Path(SKILL) / "scripts"
VERSION = "1.0"
SLUG = "Guardian_Recall_Shugojuu_Shoukan_EN"
XDELTA = ROOT / "tools/xdelta/xdelta3-3.1.0-x86_64.exe"
ORIG = "rom/Guardian Recall - Shugojuu Shoukan (Japan) (Disc {}).bin"
BUILT = "build/disc{0}/Guardian Recall - Shugojuu Shoukan (English) (Disc {0}).bin"
PLACEHOLDER = re.compile(r"<(Game title|platform|publisher|year|repo|file|size|sha1|game|ext)>|<[A-Z][a-z]+ / ")


def run(cmd, **kw):
    print(">", " ".join(str(c) for c in cmd[2:5]), flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=ROOT, **kw)
    if r.returncode:
        sys.exit(f"release gate failed (exit {r.returncode}): {' '.join(map(str, cmd))}")
    return r


def sums(path):
    crc, md5, sha1 = 0, hashlib.md5(), hashlib.sha1()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 24):
            crc = zlib.crc32(chunk, crc)
            md5.update(chunk)
            sha1.update(chunk)
    return {"size": Path(path).stat().st_size, "crc": f"{crc:08X}", "md5": md5.hexdigest(), "sha1": sha1.hexdigest()}


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        sys.exit(__doc__)
    rel = ROOT / "release"
    zpath = rel / f"{SLUG}_v{VERSION}.zip"
    if zpath.exists() and "--force" not in sys.argv:
        sys.exit(f"{zpath} exists: bump VERSION or pass --force")
    run(PY + [ROOT / "tools/check.py"])
    run(PY + [ROOT / "build.py"])
    run(PY + [S / "emu.py", ROOT / BUILT.format(1).replace(".bin", ".cue"), "--out", ROOT / "work/qa/smoke",
              "--route", ROOT / "tools/routes/boot.txt", "--smoke"])
    run(PY + [ROOT / "tools/jp_scan.py"])
    manifests = sorted(p for p in (ROOT / "work/qa").rglob("manifest.tsv"))
    assert manifests, "no QA manifests"
    for m in manifests:
        run(PY + [S / "qa_gate.py", "check", m, m.parent / "verdicts"])
    run(PY + [S / "textcover.py", ROOT / "work/qa/cover", ROOT / "build/strings.tsv",
              "--waive", ROOT / "docs/text_unshown.tsv"])
    open_lines = [ln for ln in (ROOT / "docs/polish.md").read_text(encoding="utf-8").splitlines()
                  if ln.lstrip().startswith("- [ ]")]
    if open_lines:
        sys.exit(f"docs/polish.md: {len(open_lines)} unticked lines, first: {open_lines[0]}")
    hit = PLACEHOLDER.search((ROOT / "README.md").read_text(encoding="utf-8"))
    if hit:
        sys.exit(f"README.md: template placeholder {hit.group()!r}")
    rel.mkdir(exist_ok=True)
    info, patches = {}, []
    for n in (1, 2):
        orig, built = ROOT / ORIG.format(n), ROOT / BUILT.format(n)
        patch = rel / f"{SLUG}_v{VERSION}_Disc{n}.xdelta"
        back = ROOT / f"work/reapplied_d{n}.bin"
        patch.unlink(missing_ok=True)
        size = max(orig.stat().st_size, built.stat().st_size)
        run([XDELTA, "-e", "-9", "-f", "-B", str(size), "-s", orig, built, patch])
        run([XDELTA, "-d", "-f", "-s", orig, patch, back])
        b, a = sums(built), sums(back)
        back.unlink()
        if a != b:
            sys.exit(f"disc {n}: re-applied patch differs from the build")
        info[n] = (sums(orig), b)
        patches.append(patch)
        print(f"disc {n}: patch {patch.stat().st_size} bytes, re-applied = build (sha1 {b['sha1']})")
    fields = {"version": VERSION, "slug_d1": patches[0].name}
    for n, (o, b) in info.items():
        fields.update({f"o{n}{k}": v for k, v in o.items()} | {f"p{n}{k}": v for k, v in b.items()})
    readme = (ROOT / "docs/release-readme.txt").read_text(encoding="utf-8").format(**fields)
    rd = rel / "README.txt"
    rd.write_text(readme, encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as zf:
        for p in patches + [rd]:
            zf.write(p, p.name)
    with zipfile.ZipFile(zpath) as zf:
        assert sorted(zf.namelist()) == sorted(p.name for p in patches + [rd]), zf.namelist()
    print("release:", zpath, sums(zpath)["sha1"])


if __name__ == "__main__":
    main()
