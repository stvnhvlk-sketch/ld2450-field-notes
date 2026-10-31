# ld2450-field-notes

Measured behaviour of the HLK-LD2450 24 GHz radar module: target splitting,
merging, held reports and output fields. Raw frames, the method, and a script
that reproduces the measured numbers.

I'm collecting **data from other units, rooms and firmware versions**. The
protocol and a reply form are at the end. Measurements are what's useful here;
a reply without them is hard to use.

## Session 1 — one person, one foil reflector (2026-10-31)

**Setup.** One LD2450, firmware **V2.04.23101915**, read by a custom
ESP32-C6 firmware that logs every frame (all three target slots, one frame
every 89 ms). One person, and a crumpled sheet of aluminium foil on the end of
a plastic pipe held at arm's length as a second reflector. The sheet was
12 × 20 in before crumpling, about 8–10 × 16 in crumpled. The person started
far from the sensor and stood still at three ranges, moving the foil outward
until a second target appeared. Distances below are the module's own reported
positions, not tape measurements.

| Attempt | Foil side |
|---|---|
| A1, ~4.7 m | west of the person |
| A2, ~2.8–3.2 m | started west, moved to the east |
| A3, ~1.7 m | west throughout; partway through, rolled up to 11.5 × 10 in (measured) |

### What happened

**1. A single target "dances" before it splits.** With the person and the foil
at the same distance, the module reports *one* target that pauses for 1–3 s,
then slides sideways 0.6–2 m in 0.5–1 s, then back, at nearly constant range
(read from the frame timeline).
The speed field stays near zero during the slides, and the largest
frame-to-frame step was 3.3 m/s.

| Attempt | Single target before the first split | Sideways extent |
|---|---|---|
| A1 | 43 s, 15 swings | −1.0 to +0.9 m |
| A2 | 21 s, 2 swings | +0.1 to +1.5 m |
| A3 | **143 s, 43 swings, no split** | −0.9 to +1.6 m |

**2. It splits wide and merges narrow.**

| Range at split | Separation at split | Smallest separation still reported as two | Lasted | Range difference at split |
|---|---|---|---|---|
| 4.72 m | 1.21 m | 0.54 m | 26.3 s | 34 mm |
| 3.23 m | 0.95 m | 0.55 m | 2.2 s | 558 mm |
| 2.80 m | 1.38 m | 0.99 m | 15.2 s | 7 mm |
| 2.85 m | 1.19 m | 0.65 m | 4.5 s | 274 mm |
| ~1.7 m | never split | — | — | — |

Three of the four splits came with both targets at nearly the **same range**,
14.7–28.4° apart in bearing. The exception, the brief 0.95 m split, had a
558 mm range difference. "Keep people a metre apart" is about right for
splitting, but once split they stay separate down to about half that.

**3. While split, one slot holds and the other moves.** In **19%** of
consecutive frames with two targets (103 of 543), exactly one target repeated
bit-identical coordinates while the other moved; 101 of those held reports had
speed 0. **Both never held at the same time.** A lone target repeated in only
**0.3%** (11 of 3,350). The longest run of identical reports was 60 frames,
about 5.3 s.

**4. Reflector strength decides which return is reported.** At ~1.7 m, with the
foil rolled up smaller, the single target stayed on the foil rather than on the
person (the person's observation; not separately scored).

**5. The resolution field never changes.** Every one of the 4,450 valid targets
in this session reports a resolution of 360. Earlier captures on the same firmware
(not included here) show the same: about 27,700 targets, all 360. Filters that treat this
field as signal energy cannot work on this firmware.

### Developing theory (labelled as such)

Hi-Link describes the LD2450 as **one transmit, two receive (1T2R)** FMCW.
With two receive channels the radar can estimate **one bearing per range
cell**, about 0.6 m deep at a 250 MHz sweep. Two reflectors in the same cell
give one blended bearing, which shifts with their relative strength and with
millimetre movements (the wavelength is 12.5 mm). That would explain the
dance.

The second target must then be created inside the module. An internal tracker
that needs a wide gap to start a second track, keeps it down to a narrower
gap, and holds a track's last position when no new detection updates it would
explain all four observations, and the frozen targets many users report. It
may also explain why the one split with a 558 mm range difference (close to
one range cell) appeared at the smallest separation.

This is being tested with a model. It is not established. Its clearest
prediction: two reflectors at the **same bearing but more than about 0.6 m
apart in range** should split immediately, with no dance.

## Reproduce

```sh
python analysis/foil_split.py
```

Standard-library Python 3. It reads `data/2026-10-31-foil-split/` and prints
the numbers in the tables and in points 1, 3 and 5 for this session. `FORMAT.md` describes the frame columns;
`attempts.json` holds the three attempt windows and the reflector details.

## Contribute data

Especially from **other firmware versions** (V2.14 in particular), other rooms
and other units. Please use the
[replication form](../../issues/new?template=replication.yml).

**Protocol (about 10 minutes):**
1. Stand facing the sensor at a measured distance (try ~1.5 m, ~3 m, ~4.5 m).
2. Crumple a sheet of aluminium foil onto the end of a plastic (non-metal)
   pipe or stick and hold it at arm's length to one side, at the same distance
   from the sensor as you. Note the foil's size.
3. Slowly move the foil outward until a second target appears and stays. Note
   the distance between the two reported targets.
4. Slowly bring the foil back in until they merge. Note that distance.
5. Watch for a single target dancing before the split, and for one target
   freezing while the other moves after it.

Raw frame logs in any format are very welcome; they can be converted.

## License

Text and data: [CC BY 4.0](LICENSE-data). Code: [MIT](LICENSE).
