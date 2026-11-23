"""Courtyards of the footprints in board.FP, read from the KiCad libraries.

    python fpgeom.py          print the CRT table for board.py

check_place.py uses this to confirm board.CRT still matches the libraries.
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FPDIR = r'C:\Program Files\KiCad\10.0\share\kicad\footprints'


def fp_path(fp):
    lib, name = fp.split(':')
    d = os.path.join(HERE, 'c02io.pretty') if lib == 'c02io' else os.path.join(FPDIR, lib + '.pretty')
    return os.path.join(d, name + '.kicad_mod')


def elements(s, kinds):
    """Yield the text of each top-level (kind ...) element, parentheses balanced."""
    for m in re.finditer(r'\((%s)\b' % '|'.join(kinds), s):
        depth, i = 0, m.start()
        while True:
            c = s[i]
            depth += c == '('
            depth -= c == ')'
            i += 1
            if depth == 0:
                break
        yield m.group(1), s[m.start():i]


def courtyard(fp):
    """(xmin, ymin, xmax, ymax) of the F.CrtYd graphics, footprint at rotation 0."""
    s = open(fp_path(fp), encoding='utf-8').read()
    xs, ys = [], []
    for kind, e in elements(s, ('fp_line', 'fp_rect', 'fp_poly', 'fp_circle', 'fp_arc')):
        if '(layer "F.CrtYd")' not in e:
            continue
        pts = [(float(x), float(y)) for x, y in
               re.findall(r'\((?:start|end|xy|mid|center) ([-\d.]+) ([-\d.]+)\)', e)]
        if kind == 'fp_circle':
            (cx, cy), (ex, ey) = pts[0], pts[1]
            r = math.hypot(ex - cx, ey - cy)
            pts = [(cx - r, cy - r), (cx + r, cy + r)]
        xs += [p[0] for p in pts]
        ys += [p[1] for p in pts]
    return (round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2))


def pads(fp):
    """{pad number: (x, y)} at rotation 0 (first occurrence of each number)."""
    s = open(fp_path(fp), encoding='utf-8').read()
    out = {}
    for _, e in elements(s, ('pad',)):
        m = re.match(r'\(pad "([^"]*)" \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+)', e)
        if m and m.group(1) and m.group(1) not in out:
            out[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return out


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    import board
    print('CRT = {')
    for k in sorted(board.FP):
        print("    %r: %r," % (k, courtyard(board.FP[k])))
    print('}')
