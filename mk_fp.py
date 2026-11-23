"""Write the project footprints into c02io.pretty (plain Python).

    python mk_fp.py

Both are Mornsun isolated DC-DC converters, drawn from the top-view
"Recommended Layout" in their datasheets (origin = body centre):
  Mornsun_URB_YMD-6WR3_THT   URB_YMD-6WR3 (2026.09.18-B/7) p.6: 25.40 mm square,
                             pins 1/2 at x -10.16, y -/+2.54; pin 5 at (10.16, -10.16),
                             pin 3 at (10.16, 10.16); pin 4 absent. 1.0 mm pins, 1.5 mm holes.
  Mornsun_B05_XT-1WR3_SMD    B05_XT-1WR3 (2022.01.08-A/5) p.4: 13.2 x 8.5 mm body;
                             pins 1, 2, 4 (bottom row) and 8, 5 (top row) on a 2.54 mm
                             grid, 7.62 mm from 1 to 4; pads 1.0 x 2.1 mm, 12.2 mm
                             between the outer pad edges.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, 'c02io.pretty')


def line(x1, y1, x2, y2, layer, w):
    return '\t(fp_line (start %g %g) (end %g %g) (stroke (width %g) (type solid)) (layer "%s"))\n' % (
        x1, y1, x2, y2, w, layer)


def rect(x1, y1, x2, y2, layer, w):
    return '\t(fp_rect (start %g %g) (end %g %g) (stroke (width %g) (type solid)) (fill no) (layer "%s"))\n' % (
        x1, y1, x2, y2, w, layer)


def texts(ref_y, val_y):
    eff = '(effects (font (size 1 1) (thickness 0.15)))'
    return ('\t(property "Reference" "REF**" (at 0 %g 0) (layer "F.SilkS") %s)\n' % (ref_y, eff)
            + '\t(property "Value" "VAL**" (at 0 %g 0) (layer "F.Fab") %s)\n' % (val_y, eff)
            + '\t(fp_text user "${REFERENCE}" (at 0 0 0) (layer "F.Fab") %s)\n' % eff)


def write(name, descr, attr, body, pads):
    s = ('(footprint "%s"\n\t(version 20240108)\n\t(generator "mk_fp.py")\n\t(layer "F.Cu")\n'
         '\t(descr "%s")\n\t(attr %s)\n' % (name, descr, attr)) + body + pads + ')\n'
    os.makedirs(LIB, exist_ok=True)
    with open(os.path.join(LIB, name + '.kicad_mod'), 'w', newline='\n') as f:
        f.write(s)
    print('wrote', name)


# ---------------------------------------------------------------- URB_YMD-6WR3
h = 12.7                                     # half of 25.40
body = texts(-h - 1.5, h + 1.5)
body += rect(-h, -h, h, h, 'F.Fab', 0.1)
body += rect(-h - 0.12, -h - 0.12, h + 0.12, h + 0.12, 'F.SilkS', 0.12)
body += line(-h - 0.8, -4.5, -h - 0.8, -0.6, 'F.SilkS', 0.12)          # pin-1 mark
body += rect(-h - 0.5, -h - 0.5, h + 0.5, h + 0.5, 'F.CrtYd', 0.05)
pads = ''
for num, x, y in ((1, -10.16, -2.54), (2, -10.16, 2.54), (3, 10.16, 10.16), (5, 10.16, -10.16)):
    shape = 'rect' if num == 1 else 'circle'
    pads += ('\t(pad "%d" thru_hole %s (at %g %g) (size 2.5 2.5) (drill 1.5) (layers "*.Cu" "*.Mask"))\n'
             % (num, shape, x, y))
write('Mornsun_URB_YMD-6WR3_THT',
      'Mornsun URB_YMD-6WR3 6 W isolated DC-DC, 25.4 mm square DIP; pin 4 absent',
      'through_hole', body, pads)

# ---------------------------------------------------------------- B05_XT-1WR3
bx, by = 6.6, 4.25                           # half of 13.2 x 8.5
py = (12.2 - 2.1) / 2                        # pad centre row: 5.05
body = texts(-py - 2.2, py + 2.2)
body += rect(-bx, -by, bx, by, 'F.Fab', 0.1)
body += line(-bx - 0.12, -by - 0.12, bx + 0.12, -by - 0.12, 'F.SilkS', 0.12)
body += line(-bx - 0.12, by + 0.12, bx + 0.12, by + 0.12, 'F.SilkS', 0.12)
body += line(-bx - 0.12, -by - 0.12, -bx - 0.12, by + 0.12, 'F.SilkS', 0.12)
body += line(bx + 0.12, -by - 0.12, bx + 0.12, by + 0.12, 'F.SilkS', 0.12)
body += line(-5.0, py + 1.5, -2.6, py + 1.5, 'F.SilkS', 0.12)            # pin-1 mark
body += rect(-bx - 0.5, -py - 1.55, bx + 0.5, py + 1.55, 'F.CrtYd', 0.05)
pads = ''
for num, x, y in ((1, -3.81, py), (2, -1.27, py), (4, 3.81, py), (5, 3.81, -py), (8, -3.81, -py)):
    pads += ('\t(pad "%d" smd rect (at %g %g) (size 1 2.1) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
             % (num, x, y))
write('Mornsun_B05_XT-1WR3_SMD',
      'Mornsun B05_XT-1WR3 1 W isolated DC-DC, SMD; pins 3, 6, 7 absent; pin 8 NC',
      'smd', body, pads)


# ---------------------------------------------------------------- vendor footprints
# From Raspberry Pi's CM5 IO board, revision 2, KiCad files (RP-008099-DD-1,
# vendor/cm5io). Copied unchanged except: the CM5 courtyard covers the whole
# 55 x 40 mm module (on 1.5 mm connectors nothing fits under it; the original
# outlines only the two connectors), and the 3D model paths are dropped.
#   Raspberry-Pi-5-Compute-Module   origin on mounting hole MH (0, 0); holes at
#       (0, 0), (0, -48), (33, 0), (33, -48), 2.7 mm NPTH; module outline
#       x -3.5 .. 36.5, y -51.5 .. 3.5; connector 1-100 at x -0.5, 101-200 at x 33.5
#   TRJG0926HENL                    TRXCOM gigabit MagJack used on the CM5 IO board
import re as _re

VENDOR = os.path.join(HERE, 'vendor', 'cm5io')


def _drop(s, kind, pred):
    """Remove every top-level (kind ...) element whose text satisfies pred."""
    out, i = [], 0
    for m in _re.finditer(r'\n\t\(%s\b' % kind, s):
        if m.start() < i:
            continue
        depth, j = 0, m.start() + 1
        while True:
            depth += s[j] == '('
            depth -= s[j] == ')'
            j += 1
            if depth == 0:
                break
        if pred(s[m.start():j]):
            out.append(s[i:m.start()])
            i = j
    return ''.join(out) + s[i:]


for _name, _crt in (('Raspberry-Pi-5-Compute-Module', (-3.75, -51.75, 36.75, 3.75)),
                    ('TRJG0926HENL', None)):
    _s = open(os.path.join(VENDOR, _name + '.kicad_mod'), encoding='utf-8').read()
    _s = _drop(_s, 'model', lambda e: True)
    if _crt:
        _s = _drop(_s, 'fp_line', lambda e: '"F.CrtYd"' in e)
        _s = _drop(_s, 'fp_rect', lambda e: '"F.CrtYd"' in e)
        _s = _s.rstrip()[:-1] + rect(*_crt, 'F.CrtYd', 0.05) + ')\n'
    with open(os.path.join(LIB, _name + '.kicad_mod'), 'w', newline='\n') as _f:
        _f.write(_s)
    print('wrote', _name, '(from vendor/cm5io)')
