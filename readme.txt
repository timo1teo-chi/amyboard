# AMYboard Patch Management

A toolkit for converting Juno-106 sysex patches and managing MicroPython sketch files
for two AMYboard synthesizers — one configured for lead sounds, one for strings/pads.

---

## Folder Structure

    amyboard/
    ├── scripts/
    │   ├── convert_patches.py    # Converts Juno-106 .syx files into a sketch.py
    │   └── merge_sketches.py     # Merges channels from multiple sketches into a master
    ├── patches/                  # Place your .syx files here (not tracked in git)
    ├── boards/
    │   ├── lead/
    │   │   └── sketch.py         # Active sketch for the lead AMYboard
    │   └── strings_pads/
    │       └── sketch.py         # Active sketch for the strings/pads AMYboard
    └── README.md

---

## Requirements

- Python 3.x with `mpremote` installed: `pip install mpremote`
- AMYboard connected via USB-C on COM6 (Windows)
- Juno-106 `.syx` patch files placed in the `patches/` folder

---

## Scripts

### `scripts/convert_patches.py`

Reads Juno-106 single-patch `.syx` files from the `patches/` folder and generates
a `sketch.py` ready to push to an AMYboard.

**Configuration** — edit these variables at the top of the script:

```python
SELECTED_PATCHES = [
    ('A13 Phaser Strings Str.syx', 1, 4),   # (filename, midi_channel, num_voices)
    ('A71 Organ 1 Ks.syx',         2, 4),
    ('A87 Italo Bells Bl.syx',     3, 4),
]
```

- `filename` — the `.syx` file in your `patches/` folder
- `midi_channel` — which MIDI channel (1–16) this patch responds to
- `num_voices` — polyphony (recommend 4 for pads/strings, 2 for bass, 1 for mono lead)

**Run it:**

```
cd scripts
python convert_patches.py
```

This writes a `sketch.py` to the current folder. Move or copy it to the appropriate
board folder (`boards/lead/` or `boards/strings_pads/`) before pushing.

**What it sets up:**

- Each selected patch loaded on its MIDI channel
- Standard GM CC map for live parameter control (see CC Map below)
- CC 127 save trigger — send CC 127 value > 0 to save live tweaks to the board

---

### `scripts/merge_sketches.py`

Pulls specific channels from existing sketch files and appends them into a master
sketch. Skips any channel that already exists in the master.

**Configuration** — edit these variables at the top of the script:

```python
MASTER_FILE = 'sketch_master.py'

SOURCES = [
    ('sketch_brass.py',  1),
    ('sketch_bass.py',   2),
    ('sketch_bells.py',  3),
]
```

**Run it:**

```
cd scripts
python merge_sketches.py
```

- If `MASTER_FILE` doesn't exist it will be created from scratch
- If it already exists, only new channels are appended — existing channels are skipped
- The CC map and MIDI callback are always rewritten cleanly at the bottom

---

## Pushing a Sketch to an AMYboard

```
mpremote connect COM6 resume fs cp boards/lead/sketch.py :current/sketch.py
```

Then press **RST** on the board to reboot and load the new sketch.

---

## CC Map

| CC | Parameter      | Range        |
|----|----------------|--------------|
| 1  | LFO amount     | 0.0 – 1.0    |
| 5  | Portamento     | 0 – 2000ms   |
| 7  | Volume         | 0.0 – 1.0    |
| 71 | Resonance      | 0.0 – 8.0    |
| 72 | Release        | 10 – 4000ms  |
| 73 | Attack         | 10 – 4000ms  |
| 74 | Filter cutoff  | 100 – 8000Hz |
| 75 | Decay          | 10 – 4000ms  |
| 91 | Chorus         | 0 / 1 / 2    |

**To save live tweaks permanently:** send **CC 127, value > 0** on any channel.

---

## Supported Patch Formats

- **Juno-106 single patch dumps** — 24-byte `.syx` files with a 5-byte Roland header
- Other formats (bank dumps, Alpha Juno, Juno-6, Juno-60) are not currently supported

---

## Two Board Setup

| Board        | Folder                 | Purpose                           |
|--------------|------------------------|-----------------------------------|
| Lead         | `boards/lead/`         | Lead lines, bass, mono sounds     |
| Strings/Pads | `boards/strings_pads/` | Pads, strings, polyphonic textures|

Update the COM port in the push command to match your board.

---

## Workflow Summary

1. Place `.syx` files in `patches/`
2. Edit `SELECTED_PATCHES` in `convert_patches.py`
3. Run `python convert_patches.py` → generates `sketch.py`
4. Copy `sketch.py` to `boards/lead/` or `boards/strings_pads/`
5. Push to board: `mpremote connect COM6 resume fs cp boards/lead/sketch.py :current/sketch.py`
6. Press RST on the board
7. Commit: `git add . && git commit -m "describe what changed"`