"""Check the generated schematic with KiCad (plain Python; calls kicad-cli).

    python check_sch.py

- ERC: no errors or warnings
- the schematic's netlist, exported by KiCad, joins exactly the same pins as
  board.py (every net, pin for pin), and has every part with its footprint
"""
import os
import re
import subprocess
import sys

import board

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
SCH = os.path.join(HERE, 'c02io.kicad_sch')
ok = True


def check(cond, msg):
    global ok
    print(('  ok   ' if cond else '  FAIL ') + msg)
    ok &= bool(cond)


# ---------------------------------------------------------------- ERC
rpt = os.path.join(HERE, 'erc.txt')
subprocess.run([CLI, 'sch', 'erc', '--output', rpt, SCH], cwd=HERE, capture_output=True)
text = open(rpt, encoding='utf-8', errors='replace').read()
m = re.search(r'\*\* ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)', text)
kinds = sorted(set(re.findall(r'^\[(\w+)\]', text, re.M)))
check(m and m.group(1) == '0', 'ERC: %s %s (erc.txt)' % (m.group(0).replace('\n', ' ') if m else text[-200:], kinds))

# ---------------------------------------------------------------- netlist
net_file = os.path.join(HERE, 'c02io_sch.net')
subprocess.run([CLI, 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '--output', net_file, SCH],
               cwd=HERE, capture_output=True)
s = open(net_file, encoding='utf-8').read()
os.remove(net_file)

def parse(text):
    """Minimal s-expression reader: nested lists of strings."""
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack = [[]]
    for t in tokens:
        if t == '(':
            stack.append([])
        elif t == ')':
            e = stack.pop()
            stack[-1].append(e)
        else:
            stack[-1].append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return stack[0][0]


def find(e, key):
    return [x for x in e if isinstance(x, list) and x and x[0] == key]


tree = parse(s)
comps = {}
for c in find(find(tree, 'components')[0], 'comp'):
    fp = find(c, 'footprint')
    comps[find(c, 'ref')[0][1]] = fp[0][1] if fp else ''
want_fp = {p['ref']: board.FP[p['fp']] for p in board.PARTS}
check(comps == want_fp, 'every part in the schematic, with the board footprint (%d parts)' % len(comps))

sch = {}
for n in find(find(tree, 'nets')[0], 'net'):
    name = find(n, 'name')[0][1]
    nodes = frozenset((find(x, 'ref')[0][1], find(x, 'pin')[0][1]) for x in find(n, 'node'))
    if name.startswith('unconnected-') or not nodes:
        continue
    sch[name.lstrip('/')] = nodes
brd = {n: frozenset(v) for n, v in board.nets().items()}
missing = sorted(set(brd) - set(sch))
extra = sorted(set(sch) - set(brd))
diff = sorted(n for n in set(brd) & set(sch) if brd[n] != sch[n])
check(not missing and not extra and not diff,
      'schematic nets = board.py nets, pin for pin (%d nets) missing %s extra %s different %s'
      % (len(sch), missing[:5], extra[:5], diff[:5]))

print('ALL PASSED' if ok else 'FAILED')
sys.exit(0 if ok else 1)
