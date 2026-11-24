"""Split vqa sheets (320x240 or 640x480 tiles), drop exact-duplicate and padding tiles, save packs of 4 (2x2)
unique tiles, so a reviewer reads each distinct frame once (boot/title frames repeat across opt_* and d2 sheets).
Packs use the first tile's size (later tiles are resized to it).
usage: python -X utf8 tools/vqa_uniq.py OUTPREFIX SHEET..   prints which tiles are in each pack and the duplicates."""
import hashlib, sys
from PIL import Image

out, sheets = sys.argv[1], sys.argv[2:]
seen, uniq = {}, []
for s in sheets:
    im = Image.open(s).convert("RGB")
    tw = 640 if im.size[0] % 642 == 0 and im.size[1] % 482 == 0 else 320
    th = tw * 3 // 4
    cols, rows = (im.size[0] + 1) // (tw + 2), (im.size[1] + 1) // (th + 2)
    for r in range(rows):
        for c in range(cols):
            t = im.crop((c * (tw + 2), r * (th + 2), c * (tw + 2) + tw, r * (th + 2) + th))
            cl = t.getcolors(4)
            if cl and all(col == (64, 0, 64) for _, col in cl):
                continue
            h = hashlib.sha1(t.tobytes()).hexdigest()
            name = f"{s.rsplit('/', 1)[-1][:-4]}#{r * cols + c}"
            if h in seen:
                print(f"  {name} = {seen[h]}")
                continue
            seen[h] = name
            uniq.append((name, t))
for i in range(0, len(uniq), 4):
    grp = uniq[i:i + 4]
    tw, th = grp[0][1].size
    page = Image.new("RGB", (2 * tw + 2, 2 * th + 2), (64, 0, 64))
    for j, (n, t) in enumerate(grp):
        page.paste(t.resize((tw, th)) if t.size != (tw, th) else t, ((j % 2) * (tw + 2), (j // 2) * (th + 2)))
    page.save(f"{out}_{i // 4:02d}.png")
    print(f"{out}_{i // 4:02d}.png: " + ", ".join(n for n, _ in grp))
