# AMYboard Patch Management

A toolkit for converting Juno-106 sysex patches and managing MicroPython sketch files
for two AMYboard synthesizers — one configured for lead sounds, one for strings/pads.

---

## Folder Structure

    amyboard/
    ├── scripts/
    │   ├── convert_patches.py    # Converts .syx files into a sketch.py
    │   └── merge_sketches.py     # Merges channels into a master sketch
    ├── patches/                  # Place your .syx files here (not tracked in git)
    ├── boards/
    │   ├── lead/
    │   │   └── sketch.py         # Active sketch for the lead AMYboard
    │   └── strings_pads/
    │       └── sketch.py         # Active sketch for the strings/pads AMYboard
    ├── templates/                # Edisyn Zero SL template files (.syx)
    └── README.md

---

## Setup — Windows

### 1 — Install the CH340K USB driver
Download and install from https://www.wch-ic.com/downloads/CH341SER_EXE.html

After plugging in the AMYboard, check Device Manager under Ports (COM & LPT) for the
COM port number (e.g. COM6).

### 2 — Install Python
Download from https://python.org/downloads. Check **Add Python to PATH** during installation.

### 3 — Install mpremote and amy
```
pip install mpremote
pip install amy
```

### 4 — Add Python Scripts to PATH
Find your Python scripts folder:
```
python -c "import sys; print(sys.executable)"
```
Add both the Python folder and its Scripts subfolder to your user PATH via
**Edit the system environment variables → Environment Variables → Path**.

### 5 — Configure Git
```
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

### 6 — Clone the repo
```
cd C:\Users\yourname\Documents
git clone https://github.com/yourusername/amyboard.git
```

### 7 — Connect to AMYboard
```
mpremote connect COM6 resume
```

### 8 — Push a sketch to the board
```
mpremote connect COM6 resume fs cp boards/lead/sketch.py :current/sketch.py
```
Then press RST on the board to reboot.

---

## Setup — Mac

### 1 — Install Xcode command line tools
Run in Terminal and click Install when prompted:
```
xcode-select --install
```
This installs Git and Python in one go.

### 2 — Install mpremote and amy
```
pip3 install mpremote
pip3 install amy
```

### 3 — Add mpremote to PATH
Find your Python user base:
```
python3 -m site --user-base
```
Then add the bin folder to your PATH (replace path with your actual output above):
```
echo 'export PATH="/Users/yourname/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 4 — Configure Git
```
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

### 5 — Clone the repo
```
cd ~/Documents
git clone https://github.com/yourusername/amyboard.git
```

### 6 — Find the AMYboard port
```
ls /dev/tty.*
```
Look for something like `/dev/tty.usbmodem1101`.

### 7 — Connect to AMYboard
```
mpremote connect /dev/tty.usbmodem1101 resume
```

### 8 — Push a sketch to the board
```
mpremote connect /dev/tty.usbmodem1101 resume fs cp boards/lead/sketch.py :current/sketch.py
```
Then press RST on the board to reboot.

---

## Scripts

### `scripts/convert_patches.py`

Reads Juno-106 single-patch `.syx` files from `patches/` and generates a `sketch.py`
ready to push to an AMYboard.

**Configure** `SELECTED_PATCHES` at the top of the script:

```python
SELECTED_PATCHES = [
    ('A13 Phaser Strings Str.syx', 1, 4),   # (filename, midi_channel, num_voices)
    ('A71 Organ 1 Ks.syx',         2, 4),
    ('A87 Italo Bells Bl.syx',     3, 4),
]
```

- `filename` — the `.syx` file in your `patches/` folder
- `midi_channel` — which MIDI channel (1–16) this patch responds to
- `num_voices` — polyphony (4 for pads/strings, 2 for bass, 1 for mono lead)

**Run it:**

```
python convert_patches.py    # Windows
python3 convert_patches.py   # Mac
```

Copy the output `sketch.py` to `boards/lead/` or `boards/strings_pads/` before pushing.

---

### `scripts/merge_sketches.py`

Pulls specific channels from existing sketch files and appends them into a master
sketch. Skips any channel that already exists in the master.

**Configure** `MASTER_FILE` and `SOURCES` at the top:

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
python merge_sketches.py    # Windows
python3 merge_sketches.py   # Mac
```

- Creates master from scratch if it doesn't exist
- Appends only new channels — existing ones are skipped
- CC map and MIDI callback always rewritten cleanly at the bottom

---

## CC Map

The same CC map applies to all channels simultaneously. Send **CC 127, value > 0**
on any channel to save live tweaks permanently to the board.

| CC  | Parameter     | Range        |
|-----|---------------|--------------|
| 1   | LFO amount    | 0.0 – 1.0    |
| 5   | Portamento    | 0 – 2000ms   |
| 7   | Volume        | 0.0 – 1.0    |
| 71  | Resonance     | 0.0 – 8.0    |
| 72  | Release       | 10 – 4000ms  |
| 73  | Attack        | 10 – 4000ms  |
| 74  | Filter cutoff | 100 – 8000Hz |
| 75  | Decay         | 10 – 4000ms  |
| 91  | Chorus        | 0 / 1 / 2    |
| 127 | Save to board | value > 0 triggers save |

---

## Zero SL Template Setup

Use **Edisyn** (free, Mac/Windows/Linux) to build and send templates to the Zero SL.
Download from https://github.com/eclab/edisyn/releases

Save all template files to `templates/` in the repo for version control.

Recommended Zero SL encoder layout for AMYboard sound design (all controls on MIDI channel 1):

| Control   | CC  | Label   | Notes                              |
|-----------|-----|---------|------------------------------------|
| Encoder 1 | 74  | Filter  |                                    |
| Encoder 2 | 71  | Reso    |                                    |
| Encoder 3 | 1   | LFO     |                                    |
| Encoder 4 | 91  | Chorus  |                                    |
| Encoder 5 | 73  | Attack  |                                    |
| Encoder 6 | 75  | Decay   |                                    |
| Encoder 7 | 72  | Release |                                    |
| Encoder 8 | 7   | Volume  |                                    |
| Fader 1   | 5   | Porta   |                                    |
| Button A1 | 127 | Save    | Momentary, Press 127, Release 0    |

Load one patch at a time on channel 1 to dial in, press Save to write to the board,
then move to the next patch.

---

## Supported Patch Formats

- **Juno-106 single patch dumps** — 24-byte `.syx` files with a 5-byte Roland header
- Bank dumps, Alpha Juno, Juno-6, Juno-60 — not currently supported

---

## Two Board Setup

| Board        | Folder                 | Purpose                            |
|--------------|------------------------|------------------------------------|
| Lead         | `boards/lead/`         | Lead lines, bass, mono sounds      |
| Strings/Pads | `boards/strings_pads/` | Pads, strings, polyphonic textures |

---

## Git Workflow

Always pull before starting work on either machine:
```
git pull
```

After any change to scripts, sketches or templates:
```
git add .
git commit -m "describe what changed"
git push
```

---

## Workflow Summary

1. Place `.syx` files in `patches/`
2. Edit `SELECTED_PATCHES` in `convert_patches.py`
3. Run `python convert_patches.py` → generates `sketch.py`
4. Copy `sketch.py` to `boards/lead/` or `boards/strings_pads/`
5. Push to board:
   - Windows: `mpremote connect COM6 resume fs cp boards/lead/sketch.py :current/sketch.py`
   - Mac: `mpremote connect /dev/tty.usbmodem1101 resume fs cp boards/lead/sketch.py :current/sketch.py`
6. Press RST on the board
7. Use Zero SL to dial in patch parameters via CC, press Save button (CC 127) to save
8. Commit: `git add . && git commit -m "describe what changed" && git push`
