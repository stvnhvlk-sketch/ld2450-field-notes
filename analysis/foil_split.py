#!/usr/bin/env python3
"""Reproduce every number in the README from frames.csv and attempts.json.

Usage: python analysis/foil_split.py [data/2026-10-31-foil-split]
Standard library only.
"""
import csv
import json
import math
import sys
from pathlib import Path

SETTLE_MM = 500          # settled = range stays within this of the split range
SINGLE_MOVE_MM = 500     # a "swing": lateral travel above this within SWING_WINDOW_S
SWING_WINDOW_S = 1.2


def load(folder):
    frames = {}
    with open(folder / "frames.csv", newline="") as f:
        for row in csv.DictReader(f):
            fr = frames.setdefault(int(row["frame"]), {"t": float(row["t_s"]), "s": {}})
            if row["valid"] == "1":
                fr["s"][int(row["slot"])] = (int(row["x_mm"]), int(row["y_mm"]),
                                             int(row["speed_cm_s"]), int(row["resolution_mm"]))
    attempts = json.loads((folder / "attempts.json").read_text())["attempts"]
    return [frames[k] for k in sorted(frames)], attempts


def rng(p):
    return math.hypot(p[0], p[1])


def bearing(p):
    return math.degrees(math.atan2(p[0], p[1]))


def sep(a, b):
    return math.dist(a[:2], b[:2])


def segments(frames):
    """Runs of consecutive frames with the same number of valid targets."""
    out = []
    for f in frames:
        n = len(f["s"])
        if out and out[-1][0] == n:
            out[-1][1].append(f)
        else:
            out.append([n, [f]])
    return out


def attempt_report(frames, a):
    fs = [f for f in frames if a["start_s"] <= f["t"] < a["end_s"]]
    segs = segments(fs)
    pairs = [s for n, s in segs if n == 2]
    print(f"\n## {a['id']} (nominal {a['nominal_range_m']} m; foil {a['foil_side']})")
    if pairs:
        first = pairs[0][0]
        split_range = sum(rng(p) for p in first["s"].values()) / 2
        end = first["t"]
    else:
        singles = [f for f in fs if len(f["s"]) == 1]
        split_range = sorted(rng(f["s"][0]) for f in singles)[len(singles) // 2]
        end = fs[-1]["t"]
    # settled: earliest time after which every single-target range stays near split_range
    settle = end
    for f in reversed([f for f in fs if f["t"] <= end]):
        if len(f["s"]) == 1 and abs(rng(next(iter(f["s"].values()))) - split_range) > SETTLE_MM:
            break
        settle = f["t"]
    pre = [f for f in fs if settle <= f["t"] < end and len(f["s"]) == 1]
    xs = [next(iter(f["s"].values()))[0] for f in pre] or [0]
    swings, i = 0, 0
    while i < len(pre):
        j = i
        while j < len(pre) and pre[j]["t"] - pre[i]["t"] < SWING_WINDOW_S:
            j += 1
        win = xs[i:j]
        if win and max(win) - min(win) > SINGLE_MOVE_MM:
            swings += 1
            i = j
        else:
            i += 1
    label = "until first split" if pairs else "no split; whole settled window"
    print(f"settled at t={settle:.1f} s, range {split_range:.0f} mm")
    print(f"single target before split ({label}): {end - settle:.1f} s, "
          f"lateral x {min(xs)}..{max(xs)} mm, swings >{SINGLE_MOVE_MM} mm in "
          f"{SWING_WINDOW_S} s: {swings}")
    for k, s in enumerate(pairs):
        d = [sep(f["s"][0], f["s"][1]) for f in s]
        p0, p1 = s[0]["s"][0], s[0]["s"][1]
        print(f"pair {k + 1}: t={s[0]['t']:.1f}-{s[-1]['t']:.1f} s ({s[-1]['t'] - s[0]['t']:.1f} s), "
              f"separation first {d[0]:.0f} / min {min(d):.0f} / last {d[-1]:.0f} mm, "
              f"at split: mean range {(rng(p0) + rng(p1)) / 2:.0f} mm, range diff {abs(rng(p0) - rng(p1)):.0f} mm, "
              f"bearing diff {abs(bearing(p0) - bearing(p1)):.1f} deg")


def global_report(frames):
    print("\n## Whole session")
    single = single_frozen = pair = one_frozen = both_frozen = frozen_speed0 = 0
    longest, run, max_step = 0, 0, 0.0
    for p, q in zip(frames, frames[1:]):
        n = len(q["s"])
        if n != len(p["s"]):
            run = 0
            continue
        if n == 1:
            single += 1
            (a,), (b,) = p["s"].values(), q["s"].values()
            single_frozen += a == b
            max_step = max(max_step, sep(a, b) / (q["t"] - p["t"]))
        elif n == 2:
            pair += 1
            f0 = p["s"][0] == q["s"][0]
            f1 = p["s"][1] == q["s"][1]
            one_frozen += f0 != f1
            both_frozen += f0 and f1
            if f0 != f1:
                frozen_speed0 += (q["s"][0] if f0 else q["s"][1])[2] == 0
        held = n >= 1 and any(p["s"].get(k) == v for k, v in q["s"].items())
        run = run + 1 if held else 0
        longest = max(longest, run)
    res = {v[3] for f in frames for v in f["s"].values()}
    valid = sum(len(f["s"]) for f in frames)
    dt = [(q["t"] - p["t"]) for p, q in zip(frames, frames[1:])]
    print(f"frames {len(frames)}, median interval {sorted(dt)[len(dt) // 2] * 1000:.0f} ms, "
          f"valid targets {valid}, resolution values {sorted(res)}")
    print(f"single target: identical consecutive reports {single_frozen}/{single} "
          f"({100 * single_frozen / single:.1f}%)")
    print(f"two targets: exactly one slot identical {one_frozen}/{pair} "
          f"({100 * one_frozen / pair:.0f}%), both identical {both_frozen}, "
          f"held reports with speed 0: {frozen_speed0}/{one_frozen}")
    print(f"longest identical-report run: {longest} frames")
    print(f"largest single-target step speed: {max_step / 1000:.1f} m/s")


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else
                  Path(__file__).resolve().parent.parent / "data" / "2026-10-31-foil-split")
    frames, attempts = load(folder)
    for a in attempts:
        attempt_report(frames, a)
    global_report(frames)


if __name__ == "__main__":
    main()
