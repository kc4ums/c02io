"""Check the placement in board.py and draw place.png (plain Python + matplotlib).

    python check_place.py          checks only
    python check_place.py png      checks, and writes place.png

- board.CRT matches the courtyards in the KiCad footprint files
- every courtyard is on the board, and no two courtyards overlap
- every part sits inside its isolated area; for the bridges (optos,
  isolators, converters, RS-485 chip), every pad is in the area of its net
mk_pcb.py's DRC checks the real courtyards again once the board is built.
"""
import os
import sys

import board
import fpgeom

ok = True


def check(cond, msg):
    global ok
    print(('  ok   ' if cond else '  FAIL ') + msg)
    ok &= bool(cond)


P = board.P_BY_REF
EPS = 0.01

# ---------------------------------------------------------------- courtyard table
if os.path.isdir(fpgeom.FPDIR):
    bad = [k for k, fp in board.FP.items() if fpgeom.courtyard(fp) != board.CRT[k]]
    check(not bad, 'board.CRT matches the footprint libraries %s' % bad)
else:
    print('  --   KiCad footprint library not found: CRT not re-checked')

# ---------------------------------------------------------------- board and overlaps
B = {r: board.box(r) for r in P}
off = [r for r, (x0, y0, x1, y1) in B.items()
       if x0 < -EPS or y0 < -EPS or x1 > board.BOARD_W + EPS or y1 > board.BOARD_H + EPS]
check(not off, 'every courtyard is on the %gx%g mm board %s' % (board.BOARD_W, board.BOARD_H, off))

refs = sorted(B, key=lambda r: B[r][0])
over = []
for i, a in enumerate(refs):
    ax0, ay0, ax1, ay1 = B[a]
    for b in refs[i + 1:]:
        bx0, by0, bx1, by1 = B[b]
        if bx0 >= ax1 - EPS:
            break
        if by0 < ay1 - EPS and ay0 < by1 - EPS:
            over.append((a, b))
check(not over, 'no courtyards overlap (%d pairs) %s' % (len(over), over[:12]))

# ---------------------------------------------------------------- isolation areas
AREA = board.net_areas()


def inside(pt_or_box, area):
    if len(pt_or_box) == 2:
        x, y = pt_or_box
        return any(r[0] - EPS <= x <= r[2] + EPS and r[1] - EPS <= y <= r[3] + EPS
                   for r in board.AREA_RECTS[area])
    x0, y0, x1, y1 = pt_or_box
    return any(r[0] - EPS <= x0 and x1 <= r[2] + EPS and r[1] - EPS <= y0 and y1 <= r[3] + EPS
               for r in board.AREA_RECTS[area])


PADS = {k: fpgeom.pads(fp) for k, fp in board.FP.items()} if os.path.isdir(fpgeom.FPDIR) else None


def pad_xy(ref, pad):
    p = P[ref]
    px, py = PADS[p['fp']][pad]
    dx, dy = board.rotate(px, py, p['rot'])
    return p['x'] + dx, p['y'] + dy


wrong_area, wrong_pad = [], []
for r, p in P.items():
    areas = {AREA.get(n) for n in p['pins'].values() if n} - {None}
    if r in board.BRIDGES:
        continue
    if not areas:
        continue                                  # mounting holes without a net
    if len(areas) > 1:
        areas.discard('PE')                       # J1 carries PE beside the 24 V input
    a = areas.pop() if len(areas) == 1 else None
    if a is None or not inside(B[r], a):
        wrong_area.append((r, a))
check(not wrong_area, 'every part lies inside its isolated area %s' % wrong_area[:12])
if PADS:
    for r in board.BRIDGES:
        for pad, net in P[r]['pins'].items():
            if net and pad in PADS[P[r]['fp']] and not inside(pad_xy(r, pad), AREA[net]):
                wrong_pad.append((r, pad, net, AREA[net]))
    check(not wrong_pad, 'every bridge pad is in the area of its net %s' % wrong_pad[:12])

# ---------------------------------------------------------------- picture
if len(sys.argv) > 1 and sys.argv[1] == 'png':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    COL = {'field': '#e8a33d', 'logic': '#4a7bd0', 'analog': '#3aa676', 'rs485': '#b45cc4',
           'PE': '#888888', None: '#999999'}
    fig, ax = plt.subplots(figsize=(board.BOARD_W / 12, board.BOARD_H / 12), dpi=110)
    ax.add_patch(Rectangle((0, 0), board.BOARD_W, board.BOARD_H, fill=False, lw=1.5, ec='black'))
    for a, rects in board.AREA_RECTS.items():
        if a == 'PE':
            continue
        for x0, y0, x1, y1 in rects:
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=COL[a], alpha=0.10, ec=COL[a], lw=0.8))
    for r, (x0, y0, x1, y1) in B.items():
        areas = {AREA.get(n) for n in P[r]['pins'].values() if n} - {None}
        a = areas.pop() if len(areas) == 1 else None
        bridge = r in board.BRIDGES
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc='white' if bridge else COL[a],
                               alpha=0.9 if bridge else 0.45, ec='black' if bridge else COL[a], lw=0.4))
        big = (x1 - x0) * (y1 - y0) > 30
        if big or r.startswith(('U', 'J', 'PS', 'X', 'SW', 'L')):
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, r, ha='center', va='center',
                    fontsize=6 if big else 3.5)
    for (a, b) in over:
        for r in (a, b):
            x0, y0, x1, y1 = B[r]
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec='red', lw=1.0))
    ax.set_xlim(-2, board.BOARD_W + 2)
    ax.set_ylim(board.BOARD_H + 2, -2)
    ax.set_aspect('equal')
    ax.set_xticks(range(0, int(board.BOARD_W) + 1, 10))
    ax.set_yticks(range(0, int(board.BOARD_H) + 1, 10))
    ax.tick_params(labelsize=5)
    ax.grid(lw=0.2, alpha=0.4)
    ax.set_title('C02IO placement, %g x %g mm: field (orange), logic (blue), analog (green), '
                 'RS-485 (purple); bridges white' % (board.BOARD_W, board.BOARD_H), fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'place.png'))
    print('wrote place.png')

print('ALL PASSED' if ok else 'FAILED')
sys.exit(0 if ok else 1)
