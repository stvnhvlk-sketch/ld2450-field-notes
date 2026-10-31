# Data format

Each session folder under `data/` holds:

- `frames.csv` — every LD2450 report frame, one row per target slot (three
  rows per frame).
- `attempts.json` — the session's attempt windows, with the setup details
  for each.

## frames.csv

| Column | Unit | Meaning |
|---|---|---|
| `t_s` | s | Arrival time of the frame, from the first recorded frame |
| `frame` | — | Frame number from 0; consecutive numbers mean no frame was lost |
| `slot` | — | Module target slot 0, 1 or 2 |
| `valid` | 0/1 | 1 if the module reported a target in this slot |
| `x_mm` | mm | Lateral position in the module's frame, as reported |
| `y_mm` | mm | Distance along the module's boresight, as reported |
| `speed_cm_s` | cm/s | Speed field as reported. It is **radial** speed (along the line to the sensor), so purely sideways motion reads 0 |
| `resolution_mm` | mm | Resolution field as reported (always 360 on V2.04.23101915) |

Invalid slots carry zeros. Coordinates and speed are decoded from the module's
signed-magnitude encoding and are otherwise unprocessed: no smoothing,
filtering or coordinate transform. Range is `hypot(x, y)`; bearing is
`atan2(x, y)` from boresight.

The module reports about every 89 ms (11.2 Hz) on this firmware, not 10 Hz.
