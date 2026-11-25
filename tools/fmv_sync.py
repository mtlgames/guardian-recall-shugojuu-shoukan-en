"""FMV subtitles (D18): snap each line of gfx/fmv/<STEM>.tsv to the voice, not to Whisper's guess.

    python -X utf8 tools/fmv_sync.py [STEM..]             report the shifts (nothing written)
    python -X utf8 tools/fmv_sync.py [STEM..] --apply     write the new start/end into gfx/fmv
    python -X utf8 tools/fmv_sync.py STEM --plot OUT.png  waveform + speech + subtitle spans, for checking by eye

Whisper's line times can start in the silence or music before the voice. Speech segments come from Silero VAD
(bundled with faster-whisper; trained on speech, so music and effects mostly stay out) on the movie's audio. Per
line the new start is the voice onset, see sync() for the rules. Starts stay in order; ends follow the voice. Line
ids
(fmv.STEM.<start>) change with the start: batch files in work/tl are stale after --apply.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import fmv_asr  # noqa: E402
import fmv_subs  # noqa: E402

SR = 16000
DEBUG = "--debug" in sys.argv
LEAD, MIN_LEN, QUIET = 0.6, 0.3, 1.0    # s searched before a start; shortest line; gap/voice RMS to cut
FRESH = 0.3                             # s of VAD silence before an onset that may pull a start earlier
CLUSTER_GAP, BLIP, BLIP_GAP = 1.2, 0.6, 3.0   # sync2: pause inside one line; stray leading blip and its silence
BIG, COVER = 1.0, 0.85                  # a later move past BIG s must keep COVER of the text (_late_covers)


def speech(pcm, threshold=0.4):
    """[(start s, end s)] speech segments."""
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    opts = VadOptions(threshold=threshold, min_speech_duration_ms=120, min_silence_duration_ms=150,
                      speech_pad_ms=0)
    return [(s["start"] / SR, s["end"] / SR) for s in get_speech_timestamps(pcm, opts)]


def _rms(pcm, a, b):
    x = pcm[max(int(a * SR), 0):max(int(b * SR), int(a * SR) + 1)]
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


def _asr_ends(stem):
    """{start: uncapped end} of the Whisper drafts (fmv_subs.init capped the ends; the drafts keep Whisper's)."""
    out = {}
    for d in ("asr_novad", "asr"):                      # the VAD run wins where both have a start
        p = fmv_subs.ROOT / f"work/fmv/{d}/{stem}.tsv"
        if p.exists():
            out.update({f"{float(r['start']):.2f}": float(r["end"]) for r in fmv_subs._rows(p)})
    return out


_MODEL = []


def _late_covers(pcm, on, b, ja):
    """A move later than BIG s needs proof: Whisper on [on, b] alone hears >= COVER of the line's text. The skipped
    audio is often the line's own first words under music, missed by VAD (EP_B515 66.2 s いつか, M3215 60.3 s あんな)."""
    import difflib
    if not _MODEL:
        _MODEL.append(fmv_asr.model())
    segs, _ = _MODEL[0].transcribe(pcm[int((on - 0.05) * SR):int((b + 0.3) * SR)], language="ja", beam_size=5,
                                   vad_filter=False, condition_on_previous_text=False)
    clean = lambda s: "".join(c for c in s if c.isalnum())     # noqa: E731
    ja, late = clean(ja), clean("".join(s.text for s in segs))
    hit = sum(m.size for m in difflib.SequenceMatcher(None, ja, late, autojunk=False).get_matching_blocks())
    if DEBUG:
        print(f"   check {on:.2f}: {hit}/{len(ja)} [{late}]")
    return hit >= COVER * len(ja)


def _clusters(segs, gap=CLUSTER_GAP):
    out = []
    for s, e in segs:
        if out and s - out[-1][1] < gap:
            out[-1][1] = e
        else:
            out.append([s, e])
    return out


def sync(rows, segs, pcm, ends):
    """New (start, end) per row (gfx/fmv dicts in time order). Span = [start, Whisper's uncapped end]; its speech
    segments, grouped into clusters (pauses < CLUSTER_GAP), minus a short leading blip (< BLIP s, then > BLIP_GAP s
    of silence: Whisper anchors a line on a noise, M0415 90.1 s for a line spoken at 98.6 s). Start = the first
    cluster's onset when the audio before it is quieter than the voice (QUIET; else a voice VAD missed, kept: the PA
    over the siren, M0115 17.7 s); an earlier onset only for a fresh utterance (FRESH); a jump past BIG s only with
    _late_covers. End = the last cluster's end. Never into the line before or after. Checked against the RMS
    envelope (EP_A115, EP_B115): VAD onsets sit within 30 ms of the voice's rise, Whisper's starts ~0.35 s early."""
    out, prev, prev_end = [], -1.0, -1.0
    for k, r in enumerate(rows):
        a, b = float(r["start"]), float(r["end"])
        nxt = next((float(x["start"]) for x in rows[k + 1:] if x["en"].strip() != "-"), 1e9)   # "-" is not shown
        b_raw = max(ends.get(f"{a:.2f}", b), b)
        lo = max(a - LEAD, prev_end)
        whole = cl = _clusters([s for s in segs if s[0] >= lo and s[0] < b_raw])
        while len(cl) > 1 and cl[0][1] - cl[0][0] < BLIP and cl[1][0] - cl[0][1] > BLIP_GAP:
            cl = cl[1:]
        na, nb = a, b
        # blip stripped first; if that jump fails _late_covers, the blip was the line's first words: try it
        for c in ([cl, whole] if cl is not whole else [cl]) if r["en"].strip() != "-" and cl else []:
            on = c[0][0]
            before = max((e for s, e in segs if e <= on), default=-1.0)
            ratio = _rms(pcm, a, on) / max(_rms(pcm, on, c[0][1]), 1e-6)
            if ((on < a and on - before >= FRESH) or (on > a and ratio < QUIET)) and (
                    on - a <= BIG or _late_covers(pcm, on, b_raw, r["ja"])):
                na = on
                nb = min(max(c[-1][1], b, na + MIN_LEN), max(nxt, na + MIN_LEN))   # never shorter: reading time
                break
        if na > a:      # a short line before the next one leads its voice rather than flash (M4015 60.7 s "You and me.")
            na = max(a, min(na, nxt - max(fmv_subs.READ, len(r["en"]) / fmv_subs.CPS) - 0.05))
        if DEBUG and abs(na - a) > 0.07:
            print(f"   {a:7.2f}-{b:6.2f} (raw {b_raw:6.2f}) -> {na:7.2f}-{nb:6.2f}")
        na = round(max(na, prev + 0.05), 2)
        nb = round(max(nb, na + MIN_LEN), 2)
        out.append((na, nb))
        prev, prev_end = na, max(prev_end, nb if na != a else min(b, nb))
    return out


def plot(stem, pcm, segs, rows, new, path):
    from PIL import Image, ImageDraw
    px = 100                                    # pixels per second
    w, h = int(len(pcm) / SR * px) + 1, 120
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    env = np.abs(pcm[:len(pcm) // (SR // px) * (SR // px)]).reshape(-1, SR // px).max(1)
    for x, v in enumerate(env):
        d.line([(x, 40 - v * 38), (x, 40 + v * 38)], fill=(120, 120, 120))
    for s, e in segs:
        d.rectangle([s * px, 82, e * px, 90], fill=(0, 150, 0))           # speech
    for r, (na, nb) in zip(rows, new):
        d.rectangle([float(r["start"]) * px, 94, float(r["end"]) * px, 102], fill=(200, 60, 60))   # before
        d.rectangle([na * px, 106, nb * px, 114], fill=(40, 80, 220))     # after
    for t in range(0, int(len(pcm) / SR) + 1):
        d.text((t * px + 1, 0), str(t), fill="black")
    img.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stems", nargs="*")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--plot", default=None)
    ap.add_argument("--debug", action="store_true", help="print every move and every _late_covers check")
    a = ap.parse_args()
    src = fmv_asr.movies(a.stems or fmv_subs.stems())
    tot = later = earlier = 0
    for stem in a.stems or fmv_subs.stems():
        pcm = fmv_asr.audio(src[stem])
        segs = speech(pcm)
        rows = fmv_subs._rows(fmv_subs.SUBS / f"{stem}.tsv")
        new = sync(rows, segs, pcm, _asr_ends(stem))
        for r, (na, nb) in zip(rows, new):
            da = na - float(r["start"])
            tot += 1
            later += da > 0.07
            earlier += da < -0.07
            if abs(da) > 0.07 or abs(nb - float(r["end"])) > 0.3:
                print(f"{stem} {float(r['start']):7.2f}-{float(r['end']):7.2f} -> {na:7.2f}-{nb:7.2f} "
                      f"({da:+.2f}) {r['en'][:50]}")
        if a.plot:
            plot(stem, pcm, segs, rows, new, a.plot)
        if a.apply:
            for r, (na, nb) in zip(rows, new):
                r["start"], r["end"] = f"{na:.2f}", f"{nb:.2f}"
            fmv_subs._write(fmv_subs.SUBS / f"{stem}.tsv", rows)
    print(f"{tot} lines: {later} start later (silence cut), {earlier} start earlier")


if __name__ == "__main__":
    main()
