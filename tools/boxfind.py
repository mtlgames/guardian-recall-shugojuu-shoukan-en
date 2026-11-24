"""Find the ACTION/system message boxes (1-px light grey border) in a 320x240 shot and print inkbox rects per text
row: python tools/boxfind.py SHOT.png [--rows N] [--line 14]. Border = horizontal run >= 60 px of grey 120-170 with
R~G~B, closed by vertical runs at both ends. Prints `x,y,w,h` of the inside (1 px in), then one rect per text row
when --rows is given (rows of --line px from the top inset)."""
import argparse

from PIL import Image


def grey(p, lo=120, hi=170):  # border = (139,139,139); white text (>= 200) never matches
    r, g, b = p[:3]
    return lo <= r <= hi and abs(r - g) < 12 and abs(g - b) < 12


def boxes(img):
    w, h = img.size
    px = img.load()
    found = []
    for y in range(h):
        x = 0
        while x < w:
            if grey(px[x, y]):
                x0 = x
                while x < w and grey(px[x, y]):
                    x += 1
                if x - x0 >= 60:
                    x1 = x - 1
                    y1 = y + 1  # bottom border: same run further down, with both side columns grey between
                    while y1 < h and grey(px[x0, y1]) and grey(px[x1, y1]):
                        y1 += 1
                    if y1 - y >= 10 and all(grey(px[x0 + k, y1 - 1]) for k in range(0, x1 - x0, 4)):
                        found.append((x0, y, x1, y1 - 1))
            x += 1
    return found


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("png")
    ap.add_argument("--rows", type=int, default=0)
    ap.add_argument("--line", type=int, default=14)
    ap.add_argument("--top", type=int, default=3, help="first text row's offset below the inside top")
    a = ap.parse_args()
    img = Image.open(a.png).convert("RGB")
    px = img.load()
    for x0, y0, x1, y1 in boxes(img):
        print(f"box {x0 + 1},{y0 + 1},{x1 - x0 - 1},{y1 - y0 - 1}")
        for r in range(a.rows):
            print(f"  row{r} {x0 + 1},{y0 + a.top + r * a.line},{x1 - x0 - 1},{a.line}")
        # text bands: rows holding white ink (>= 200), merged across gaps of 1 row
        ink = [y for y in range(y0 + 1, y1) if any(min(px[x, y]) >= 200 for x in range(x0 + 1, x1))]
        bands = []
        for y in ink:
            if bands and y - bands[-1][1] <= 2:
                bands[-1][1] = y
            else:
                bands.append([y, y])
        print("  text " + " ".join(f"{x0 + 1},{b0},{x1 - x0 - 1},{b1 - b0 + 1}" for b0, b1 in bands))
