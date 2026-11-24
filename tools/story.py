"""Story-pass chapter files (phase 9, references/translation.md §Review).

    python -X utf8 tools/story.py      -> work/qa/story/chapters/NN.txt for scenario 00-42 (synopsis chapters)

Rows in id order (= block order = story order): `>> id | speaker | JP` then the English body. The speaker line is
dropped from both sides (it is the speaker column); page breaks show as " ¦ ", line breaks as " / " in English.
Regenerate after every script edit, then `qa_gate.py init work/qa/story/manifest.tsv work/qa/story/chapters`.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import batches  # noqa: E402

def flat(text, sep):
    """One line: page breaks " ¦ ", line breaks sep (JP: none, the 　 indent dropped)."""
    text = text.replace("\n{wait}", "{wait}").replace("{wait}", " ¦ ").replace("\n　", sep).replace("\n", sep)
    return " ".join(text.split()).strip(" ¦")


OUT = batches.ROOT / "work/qa/story/chapters"
CHAPTERS = range(0, 43)  # 43-48 drafts/copies of 00/05, 49 alt scene, 50+ tutorials: reviewed per batch


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    names = batches.speakers()
    for n in CHAPTERS:
        doc = json.loads((batches.ROOT / f"script/scenario/{n:02d}.json").read_text(encoding="utf-8"))
        lines = []
        for e in doc["strings"]:
            name, body = batches.speaker_of(e)
            en = e.get("en") or ""
            if name and en.startswith(names.get(name, "\0") + "\n"):
                en = en.split("\n", 1)[1]
            sp = names.get(name, name) if name else "-"
            lines.append(f">> {e['id']} | {sp} | {flat(body, '')}\n   {flat(en, ' ')}")
        (OUT / f"{n:02d}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(OUT, len(CHAPTERS), "chapters")


if __name__ == "__main__":
    main()
