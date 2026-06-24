import os

SELECTED_PATCHES = [
    ('A13 Phaser Strings Str.syx', 1, 4),
    ('A71 Organ 1 Ks.syx',         2, 4),
    ('A87 Italo Bells Bl.syx',     3, 4),
]

# Standard GM CC number -> (label, amy_param, min_val, max_val)
# min/max define the range CC 0-127 maps to for that parameter
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

SAVE_CC = 127

# ----------------------------------------------------------------

def cc_map_code():
    lines = []
    lines.append("# Standard GM CC map: cc_number -> (label, amy_param, min, max)")
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

    # Store override for save
    if channel not in _overrides:
        _overrides[channel] = {}
    _overrides[channel][cc] = cc_val

    # Apply to AMY
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
        # Rebuild envelope: attack, decay, sustain, release
        # Pull current or default values
        a = _overrides[channel].get('env_a_ms', 10)
        d = _overrides[channel].get('env_d_ms', 500)
        s = _overrides[channel].get('env_s', 0.7)
        r = _overrides[channel].get('env_r_ms', 200)
        if param == 'bp0_a':
            a = int(val)
            _overrides[channel]['env_a_ms'] = a
        elif param == 'bp0_d':
            d = int(val)
            _overrides[channel]['env_d_ms'] = d
        elif param == 'bp0_r':
            r = int(val)
            _overrides[channel]['env_r_ms'] = r
        amy.send(synth=channel, bp0=f'0,0,{a},1,{d},{s},{r},0')
    elif param == 'lfo_amount':
        amy.send(synth=channel, lfo_amount=val)

def _save_sketch():
    import os
    try:
        with open('/user/current/sketch.py', 'r') as f:
            original = f.read()
        # Strip any previously saved override block
        marker = "# --- SAVED CC OVERRIDES ---"
        if marker in original:
            original = original[:original.index(marker)]
        # Append current overrides
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
            channel = (msg[0] & 0x0F) + 1  # MIDI channels are 0-indexed in the byte
            if status == 0xB0:  # CC message
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

patches = []
for filename, channel, voices in SELECTED_PATCHES:
    data = open(filename, 'rb').read()
    payload = data[5:23]
    name = filename.replace('.syx', '')
    bytevals = ', '.join(str(b) for b in payload)
    patches.append((name, channel, voices, bytevals))

with open('sketch.py', 'w') as f:
    f.write("import amy\n")
    f.write("from amy import juno\n\n")

    # Patch setup
    for name, channel, voices, bytevals in patches:
        f.write(f'# {name} -> MIDI channel {channel}\n')
        f.write(f'_p{channel} = juno.JunoPatch.from_sysex(bytes([{bytevals}]), name="{name}")\n')
        f.write(f'_p{channel}.set_synth({channel})\n')
        f.write(f'amy.send(synth={channel}, num_voices={voices}, oscs_per_voice=6)\n')
        f.write(f'_p{channel}.init_AMY()\n\n')

    # CC map
    f.write(cc_map_code())
    f.write("\n\n")

    # MIDI callback and save function
    f.write(midi_callback_code())

    f.write("\ndef loop():\n    pass\n")

print("sketch.py written.")