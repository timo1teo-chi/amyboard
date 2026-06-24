import re
import os

# ----------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------

# The master file to append into (will be created if it doesn't exist)
MASTER_FILE = 'sketch_master.py'

# Channels to pull from source sketches and append to master.
# If a channel already exists in the master it will be skipped.
# Format: (source_sketch_file, channel_number)
SOURCES = [
    ('sketch_brass.py',   1),
    ('sketch_bass.py',    2),
    ('sketch_bells.py',   3),
]

SAVE_CC = 127
CC_MAP = {
    1:  ('lfo_amount',  'lfo_amount',   0.0,  1.0),
    5:  ('portamento',  'portamento',   0,    2000),
    7:  ('vca_level',   'amp',          0.0,  1.0),
    71: ('vcf_res',     'resonance',    0.0,  8.0),
    72: ('env_r',       'bp0_r',        10,   4000),
    73: ('env_a',       'bp0_a',        10,   4000),
    74: ('vcf_freq',    'filter_freq',  100,  8000),
    75: ('env_d',       'bp0_d',        10,   4000),
    91: ('chorus',      'chorus',       0,    2),
}

# ----------------------------------------------------------------

def extract_channel_block(filepath, channel):
    """Pull the patch block for a given channel out of a sketch.py file."""
    if not os.path.exists(filepath):
        print(f"  ERROR: {filepath} not found, skipping channel {channel}.")
        return None

    with open(filepath, 'r') as f:
        content = f.read()

    pattern = (
        rf'(# .+-> MIDI channel {channel}\n'
        rf'_p{channel} = .*\n'
        rf'_p{channel}\.set_synth\({channel}\)\n'
        rf'amy\.send\(synth={channel}.*\)\n'
        rf'_p{channel}\.init_AMY\(\))'
    )
    match = re.search(pattern, content)
    if not match:
        print(f"  WARNING: Could not find channel {channel} block in {filepath}.")
        return None

    return match.group(1)


def get_existing_channels(filepath):
    """Return a set of channel numbers already present in the master file."""
    if not os.path.exists(filepath):
        return set()
    with open(filepath, 'r') as f:
        content = f.read()
    found = re.findall(r'# --- Channel (\d+) ', content)
    return set(int(c) for c in found)


def get_master_patch_block(content):
    """Strip everything from the CC map onward so we can re-append it cleanly."""
    marker = "# Standard GM CC map"
    if marker in content:
        return content[:content.index(marker)].rstrip()
    # Also strip saved override block if present
    marker2 = "# --- SAVED CC OVERRIDES ---"
    if marker2 in content:
        return content[:content.index(marker2)].rstrip()
    return content.rstrip()


def cc_map_code():
    lines = ["# Standard GM CC map: cc_number -> (label, amy_param, min, max)"]
    lines.append("CC_MAP = {")
    for cc, (label, param, mn, mx) in CC_MAP.items():
        lines.append(f"    {cc}: ('{label}', '{param}', {mn}, {mx}),")
    lines.append("}")
    lines.append(f"SAVE_CC = {SAVE_CC}")
    return "\n".join(lines)


def midi_callback_code():
    return '''
# Tracks live CC overrides per channel so they can be saved
_overrides = {}

def _scale(cc_val, mn, mx):
    return mn + (cc_val / 127.0) * (mx - mn)

def _apply_cc(channel, cc, cc_val):
    if cc not in CC_MAP:
        return
    label, param, mn, mx = CC_MAP[cc]
    val = _scale(cc_val, mn, mx)
    if channel not in _overrides:
        _overrides[channel] = {}
    _overrides[channel][cc] = cc_val
    if param == 'filter_freq':
        amy.send(synth=channel, filter_freq=val)
    elif param == 'resonance':
        amy.send(synth=channel, resonance=val)
    elif param == 'amp':
        amy.send(synth=channel, amp=val)
    elif param == 'portamento':
        amy.send(synth=channel, portamento=int(val))
    elif param == 'chorus':
        amy.send(synth=channel, chorus=int(round(val)))
    elif param in ('bp0_a', 'bp0_d', 'bp0_r'):
        a = _overrides[channel].get('env_a_ms', 10)
        d = _overrides[channel].get('env_d_ms', 500)
        s = _overrides[channel].get('env_s', 0.7)
        r = _overrides[channel].get('env_r_ms', 200)
        if param == 'bp0_a':
            a = int(val); _overrides[channel]['env_a_ms'] = a
        elif param == 'bp0_d':
            d = int(val); _overrides[channel]['env_d_ms'] = d
        elif param == 'bp0_r':
            r = int(val); _overrides[channel]['env_r_ms'] = r
        amy.send(synth=channel, bp0=f'0,0,{a},1,{d},{s},{r},0')
    elif param == 'lfo_amount':
        amy.send(synth=channel, lfo_amount=val)

def _save_sketch():
    try:
        with open('/user/current/sketch.py', 'r') as f:
            original = f.read()
        marker = "# --- SAVED CC OVERRIDES ---"
        if marker in original:
            original = original[:original.index(marker)]
        lines = [marker]
        for channel, ccs in _overrides.items():
            for cc, val in ccs.items():
                lines.append(f"_apply_cc({channel}, {cc}, {val})")
        with open('/user/current/sketch.py', 'w') as f:
            f.write(original.rstrip() + "\\n\\n" + "\\n".join(lines) + "\\n")
        print("Saved!")
    except Exception as e:
        print("Save failed:", e)

def _midi_callback(is_sysex):
    if is_sysex:
        return
    import tulip
    msg = tulip.midi_in()
    while msg is not None and len(msg) > 0:
        if len(msg) >= 3:
            status = msg[0] & 0xF0
            channel = (msg[0] & 0x0F) + 1
            if status == 0xB0:
                cc = msg[1]
                val = msg[2]
                if cc == SAVE_CC and val > 0:
                    _save_sketch()
                else:
                    _apply_cc(channel, cc, val)
        msg = tulip.midi_in()

import tulip
tulip.midi_callback(_midi_callback)
'''


# ----------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------

print(f"Target master: {MASTER_FILE}")

# Find which channels are already in the master
existing_channels = get_existing_channels(MASTER_FILE)
if existing_channels:
    print(f"  Existing channels in master: {sorted(existing_channels)}")
else:
    print(f"  Master does not exist yet, will create it.")

# Load existing master content (patch blocks only, strip CC map/callbacks)
if os.path.exists(MASTER_FILE):
    with open(MASTER_FILE, 'r') as f:
        raw = f.read()
    master_patch_content = get_master_patch_block(raw)
else:
    master_patch_content = "import amy\nfrom amy import juno"

# Process sources
new_blocks = []
for source_file, channel in SOURCES:
    if channel in existing_channels:
        print(f"  SKIPPED: channel {channel} already in master.")
        continue
    block = extract_channel_block(source_file, channel)
    if block:
        new_blocks.append((channel, source_file, block))
        print(f"  OK: channel {channel} from {source_file}")

if not new_blocks:
    print("\nNothing new to add. Master is unchanged.")
    exit(0)

# Write updated master
with open(MASTER_FILE, 'w') as f:
    f.write(master_patch_content)
    f.write("\n\n")
    for channel, source_file, block in new_blocks:
        f.write(f"# --- Channel {channel} (from {source_file}) ---\n")
        f.write(block)
        f.write("\n\n")
    f.write(cc_map_code())
    f.write("\n\n")
    f.write(midi_callback_code())
    f.write("\ndef loop():\n    pass\n")

all_channels = sorted(existing_channels | {c for c, _, _ in new_blocks})
print(f"\nDone. Master now contains channels: {all_channels}")
print(f"Push with: mpremote connect COM6 resume fs cp {MASTER_FILE} :current/sketch.py")