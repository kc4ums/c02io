"""Check the C02IO design in board.py (plain Python, no KiCad needed).

    python check_board.py

- every net joins two or more pins; every chip lists all its pins
- power and ground on each chip's datasheet pins, and a decoupling capacitor
- the CPU's address and data buses reach the right pins of every chip
- address decoding, simulated gate by gate for all 65536 addresses: exactly
  one device selected, matching the memory map in board.py's docstring
- strobes, output latch clocks, input buffer enables, output enable/watchdog
- isolation: no part other than the listed bridges joins two areas
- every I/O channel wired the same way, to the right bit and terminal
"""
import sys

import board

ok = True


def check(cond, msg):
    global ok
    print(('  ok   ' if cond else '  FAIL ') + msg)
    ok &= bool(cond)


P = {p['ref']: p for p in board.PARTS}
N = board.nets()


def pin(ref, n):
    return P[ref]['pins'].get(str(n))


def two_pin(ref):
    return pin(ref, 1), pin(ref, 2)


# ---------------------------------------------------------------- nets and pins
lonely = sorted(n for n, pads in N.items() if len(pads) < 2)
check(not lonely, 'every net joins two or more pins %s' % lonely)

bad = []
for ref, p in P.items():
    n = board.NPINS.get(p['fp'])
    if n and set(p['pins']) != {str(i) for i in range(1, n + 1)}:
        bad.append(ref)
check(not bad, 'every chip lists all its pins, unused ones as None %s' % bad)
check(all(p['fp'] in board.FP for p in board.PARTS), 'every footprint is defined')
check(len({p['ref'] for p in board.PARTS}) == len(board.PARTS), 'references are unique')

# ---------------------------------------------------------------- power pins
POWER = {
    'U1': ({8: '+5V'}, {21: 'GND'}), 'U2': ({28: '+5V'}, {14: 'GND'}),
    'U3': ({32: '+5V'}, {16: 'GND'}), 'U4': ({20: '+5V'}, {1: 'GND'}),
    'U5': ({33: '+5V', 44: '+5V'}, {12: 'GND', 22: 'GND'}),
    'U6': ({14: '+5V'}, {7: 'GND'}), 'U7': ({14: '+5V'}, {7: 'GND'}),
    'U8': ({14: '+5V'}, {7: 'GND'}), 'U9': ({16: '+5V'}, {8: 'GND'}),
    'U10': ({14: '+5V'}, {7: 'GND'}), 'U11': ({16: '+5V'}, {8: 'GND'}),
    'U12': ({2: '+5V'}, {3: 'GND'}), 'U13': ({2: '+24V'}, {1: 'GND', 9: 'GND'}),
    'U14': ({20: '+5V'}, {10: 'GND'}), 'U15': ({20: '+5V'}, {10: 'GND'}),
    'U16': ({20: '+5V'}, {10: 'GND'}), 'U17': ({20: '+5V'}, {10: 'GND'}),
    'U34': ({3: '24V_IO'}, {2: '0V_IO'}), 'U40': ({3: '+24VA'}, {2: 'AGND_ISO'}),
    'U41': ({1: '+5VA'}, {3: 'AGND_ISO'}),
    'U42': ({1: '+5V', 16: '+5VA'}, {2: 'GND', 8: 'GND', 9: 'AGND_ISO', 15: 'AGND_ISO'}),
    'U43': ({1: '+5V', 8: '+5VA'}, {4: 'GND', 5: 'AGND_ISO'}),
    'U44': ({16: '+5VA'}, {9: 'AGND_ISO', 14: 'AGND_ISO'}),
    'U45': ({3: '+5VA'}, {14: 'AGND_ISO'}),
    'U46': ({4: '+24VA'}, {11: 'AGND_ISO'}), 'U47': ({4: '+24VA'}, {11: 'AGND_ISO'}),
    'U50': ({1: '+5V', 16: '+5V_485'}, {2: 'GND', 7: 'GND', 8: 'GND', 9: 'GND_485',
                                       10: 'GND_485', 15: 'GND_485'}),
    'PS1': ({2: '+24V', 3: '+24VA'}, {1: 'GND', 5: 'AGND_ISO'}),
    'PS2': ({2: '+5V', 5: '+5V_485'}, {1: 'GND', 4: 'GND_485'}),
}
for k in range(4):
    POWER['U%d' % (30 + k)] = ({1: '24V_IO', 25: '24V_IO'}, {6: '0V_IO'})
miss = [r for r, (v, g) in POWER.items()
        if any(pin(r, n) != s for d in (v, g) for n, s in d.items())]
check(not miss, 'supply and ground on every chip at its datasheet pins %s' % miss)
chips = [r for r, p in P.items() if r.startswith('U')]
optos = {r for r in chips if P[r]['value'] == 'TLP291-4'}
check(set(chips) - set(POWER) == optos, 'every chip except the optocouplers has a power-pin check %s'
      % sorted(set(chips) - set(POWER) - optos))

caps = {}
for r, p in P.items():
    if r.startswith('C') and len(p['pins']) == 2:
        caps.setdefault(frozenset(two_pin(r)), []).append(r)
nodec = []
for r, (v, g) in POWER.items():
    if r in ('PS1', 'PS2', 'U12'):
        continue
    for vn in set(v.values()):
        gn = {'+5V': 'GND', '+24V': 'GND', '24V_IO': '0V_IO', '+24VA': 'AGND_ISO',
              '+5VA': 'AGND_ISO', '+5V_485': 'GND_485'}[vn]
        if not caps.get(frozenset((vn, gn))):
            nodec.append((r, vn))
check(not nodec, 'a capacitor across every chip supply %s' % nodec)
n5 = len(caps.get(frozenset(('+5V', 'GND')), []))
check(n5 >= 20, '%d capacitors on +5V (CPU, RAM, flash, VIA, UART, 11 logic chips, isolators)' % n5)

# ---------------------------------------------------------------- buses
CPU_A = {i: (9 + i if i < 12 else 10 + i) for i in range(16)}
CPU_D = {i: 33 - i for i in range(8)}
check(all(pin('U1', CPU_A[i]) == 'A%d' % i for i in range(16)), 'W65C02S A0-A15')
check(all(pin('U1', CPU_D[i]) == 'D%d' % i for i in range(8)), 'W65C02S D0-D7')
check(pin('U1', 34) == 'RW' and pin('U1', 37) == 'PHI2' and pin('U1', 40) == '~{RES}'
      and pin('U1', 4) == '~{IRQ}' and pin('U1', 6) == '~{NMI}' and pin('U1', 2) == 'RDY'
      and pin('U1', 36) == '+5V' and pin('U1', 38) == '+5V',
      'W65C02S RWB, PHI2, RESB, IRQB, NMIB, RDY; BE and SOB high')
J28 = {'A0': 10, 'A1': 9, 'A2': 8, 'A3': 7, 'A4': 6, 'A5': 5, 'A6': 4, 'A7': 3, 'A8': 25,
       'A9': 24, 'A10': 21, 'A11': 23, 'A12': 2, 'A13': 26, 'A14': 1, 'D0': 11, 'D1': 12,
       'D2': 13, 'D3': 15, 'D4': 16, 'D5': 17, 'D6': 18, 'D7': 19}
J32 = {'A0': 12, 'A1': 11, 'A2': 10, 'A3': 9, 'A4': 8, 'A5': 7, 'A6': 6, 'A7': 5, 'A8': 27,
       'A9': 26, 'A10': 23, 'A11': 25, 'A12': 4, 'A13': 28, 'A14': 29, 'FA15': 3, 'FA16': 2,
       'D0': 13, 'D1': 14, 'D2': 15, 'D3': 17, 'D4': 18, 'D5': 19, 'D6': 20, 'D7': 21}
check(all(pin('U2', n) == s for s, n in J28.items()), 'RAM AS6C62256 SOP: A0-A14, D0-D7')
check(all(pin('U3', n) == s for s, n in J32.items()), 'flash SST39SF010A PLCC: A0-A14, bank, D0-D7')
check(pin('U2', 20) == '~{RAMCS}' and pin('U2', 22) == '~{RD}' and pin('U2', 27) == '~{WR}',
      'RAM /CE, /OE = /RD, /WE = /WR')
check(pin('U3', 22) == '~{ROMCS}' and pin('U3', 24) == '~{RD}' and pin('U3', 31) == '~{FWE}'
      and pin('JP1', 1) == '~{WR}' and pin('JP1', 2) == '~{FWE}' and pin('JP1', 3) == '+5V',
      'flash /CE, /OE = /RD, /WE through JP1 (2-3 = protected)')
VIA = {'D%d' % i: 33 - i for i in range(8)}
VIA.update({'A0': 38, 'A1': 37, 'A2': 36, 'A3': 35, 'RW': 22, 'PHI2': 25, '~{RES}': 34,
            '~{IRQ}': 21, '~{CS0}': 23, '+5V': 24})
check(all(pin('U4', n) == s for s, n in VIA.items()), 'VIA: D0-D7, RS0-3 = A0-A3, RWB, PHI2, RESB, IRQB, CS2B = /CS0, CS1 high')
UART = {'D%d' % i: 2 + i for i in range(8)}
UART.update({'A0': 10, 'A1': 14, 'A2': 15, 'A3': 16, '~{CS1}': 18, '~{WR}': 20, '~{RD}': 24,
             'RES': 21, 'UART_CLK': 11, 'UA_INT': 34, 'UB_INT': 17})
check(all(pin('U5', n) == s for s, n in UART.items()),
      'TL16C2552: D0-D7, A0-A2, CHSEL = A3, /CS = /CS1, /IOR, /IOW, RESET, XTAL1, INTA/B')
check(pin('U5', 13) is None, 'TL16C2552 XTAL2 open (external clock)')

# ---------------------------------------------------------------- decoding (gate simulation)
GATES = {'74HC00': [((1, 2), 3, 'nand'), ((4, 5), 6, 'nand'), ((9, 10), 8, 'nand'), ((12, 13), 11, 'nand')],
         '74HC32': [((1, 2), 3, 'or'), ((4, 5), 6, 'or'), ((9, 10), 8, 'or'), ((12, 13), 11, 'or')],
         '74HC30': [((1, 2, 3, 4, 5, 6, 11, 12), 8, 'nand')]}


GATE_LIST = []                                      # (input nets, output net, kind)
for _ref, _p in P.items():
    for _ins, _out, _kind in GATES.get(_p['value'], []):
        if pin(_ref, _out):
            GATE_LIST.append(([pin(_ref, i) for i in _ins], pin(_ref, _out), _kind))
    if _p['value'] == '74HC138':
        GATE_LIST.append(([pin(_ref, i) for i in (1, 2, 3, 4, 5, 6)],
                          [pin(_ref, o) for o in (15, 14, 13, 12, 11, 10, 9, 7)], '138'))


def evaluate(addr, rw, phi2, extra=None):
    v = {'A%d' % i: (addr >> i) & 1 for i in range(16)}
    v.update(RW=rw, PHI2=phi2, GND=0)
    v['+5V'] = 1
    v['~{RES}'] = 1
    v.update(extra or {})
    for _ in range(6):                                # settle the gate network
        for ins, out, kind in GATE_LIST:
            if not all(i in v for i in ins):
                continue
            x = [v[i] for i in ins]
            if kind == 'nand':
                v[out] = 0 if all(x) else 1
            elif kind == 'or':
                v[out] = 1 if any(x) else 0
            else:
                en = x[3] == 0 and x[4] == 0 and x[5] == 1
                sel = x[0] | x[1] << 1 | x[2] << 2
                for k, o in enumerate(out):
                    v[o] = 0 if en and sel == k else 1
    v['~{FWE}'] = v['~{WR}']                        # JP1 in the write position
    return v


NAMES = ('VIA', 'UART', 'IN1', 'IN2', 'OUT1', 'OUT2', 'CS6', 'CS7')


def selected(v):
    s = []
    if v['~{RAMCS}'] == 0:
        s.append('RAM')
    if v['~{ROMCS}'] == 0:
        s.append('ROM')
    for k in range(8):
        if v['~{CS%d}' % k] == 0:
            s.append(NAMES[k])
    return s


def expect(a):
    if a < 0x7F00:
        return ['RAM']
    if a < 0x7F80:
        return [NAMES[(a >> 4) & 7]]
    if a < 0x8000:
        return []
    return ['ROM']


bad = [a for a in range(0x10000) if selected(evaluate(a, 1, 1)) != expect(a)]
check(not bad, 'decoding for all 65536 addresses matches the memory map%s'
      % (' (first bad $%04X: %s)' % (bad[0], selected(evaluate(bad[0], 1, 1))) if bad else ''))
strobe = {(rw, ph): (evaluate(0x1234, rw, ph)['~{RD}'], evaluate(0x1234, rw, ph)['~{WR}'])
          for rw in (0, 1) for ph in (0, 1)}
check(strobe == {(1, 1): (0, 1), (0, 1): (1, 0), (1, 0): (1, 1), (0, 0): (1, 1)},
      '/RD only on reads, /WR only on writes, both only while PHI2 is high')

# input buffers: outputs on only when the address matches and /RD is low
for ref, base, cs in (('U14', 0x7F20, '~{CS2}'), ('U15', 0x7F30, '~{CS3}')):
    def drives(a, rw, ph):
        v = evaluate(a, rw, ph)
        return v[pin(ref, 1)] == 0 and v[pin(ref, 19)] == 0
    on = [a for a in range(0x7F00, 0x8000) if drives(a, 1, 1)]
    check(on == list(range(base, base + 16)) and not drives(base, 0, 1) and not drives(base, 1, 0),
          '%s drives the data bus only on reads of $%04X-$%04X while PHI2 is high' % (ref, base, base + 15))
# output latches: clock rises at the end of a write to their address only
for ref, base in (('U16', 0x7F40), ('U17', 0x7F50)):
    clk = pin(ref, 11)
    w = [a for a in range(0x10000) if evaluate(a, 0, 1)[clk] == 0]
    edge = all(evaluate(a, 0, 0)[clk] == 1 for a in w)
    check(w == list(range(base, base + 16)) and edge and all(evaluate(base, 1, ph)[clk] == 1 for ph in (0, 1)),
          '%s clocks on the rising edge at the end of a write to $%04X-$%04X only' % (ref, base, base + 15))
check(pin('U16', 1) == pin('U17', 1) == '~{OUT_OE}', 'both output latches enabled by ~OUT_OE')
oe = {(e, w): evaluate(0, 1, 1, {'OUT_EN': e, 'WDOK': w})['~{OUT_OE}'] for e in (0, 1) for w in (0, 1)}
check(oe == {(0, 0): 1, (0, 1): 1, (1, 0): 1, (1, 1): 0},
      'outputs enabled only when PB0 is set AND the watchdog is running')
check(two_pin('R7') == ('OUT_EN', 'GND') and two_pin('R6') == ('WD_KICK', 'GND'),
      'PB0 (output enable) and PB1 (watchdog kick) pulled low through reset')
check(pin('U11', 2) == 'WD_KICK' and pin('U11', 1) == 'GND' and pin('U11', 3) == '~{RES}'
      and pin('U11', 13) == 'WDOK', '74HC123: B = kick (rising edge, /A low), /R = /RES, Q = WDOK')
check(pin('U11', 15) == 'WD_RC' and pin('U11', 14) == 'WD_CX' and two_pin('R5') == ('+5V', 'WD_RC')
      and two_pin('C5') == ('WD_RC', 'WD_CX'), '74HC123: Rx to VCC at RxCx, Cx between Cx and RxCx')
v = evaluate(0, 1, 1, {'~{RES}': 0, '~{UA_RTS}': 1})
check(v['RES'] == 1 and evaluate(0, 1, 1)['RES'] == 0, 'UART RESET (active high) = inverted /RES')
check(v['DIR485'] == 0 and evaluate(0, 1, 1, {'~{UA_RTS}': 0})['DIR485'] == 1,
      'RS-485 receives after reset (/RTSA high); MCR RTS = 1 transmits')

# ---------------------------------------------------------------- interrupts, clock, reset
irq = sorted(r for r, _ in N['~{IRQ}'])
check(irq == sorted(['U1', 'U4', 'Q1', 'Q2', 'R11', 'J11']), '/IRQ wire-OR: VIA, UART via Q1/Q2, pull-up %s' % irq)
for q, ch in (('Q1', 'UA'), ('Q2', 'UB')):
    check(pin(q, 1) == ch + '_INTB' and pin(q, 2) == 'GND' and pin(q, 3) == '~{IRQ}'
          and (ch + '_INT', 'GND') in [two_pin(r) for r in ('R3', 'R4')],
          '%s: BC847 (1 B, 2 E, 3 C) pulls /IRQ low on %s INT, INT pulled down' % (q, ch))
check(pin('X1', 3) == 'CLK_X' and two_pin('R8') == ('CLK_X', 'PHI2') and two_pin('R9') == ('CLK_X', 'UART_CLK'),
      'one oscillator: PHI2 and UART XTAL1, each through 33 ohm')
check(pin('U12', 1) == '~{RES}' and two_pin('SW1') == ('~{RES}', 'GND'), 'DS1813 and RESET button on /RES')

# ---------------------------------------------------------------- VIA port pins
want = ['SPI_SCLK', 'SPI_MOSI', 'SPI_MISO', '~{ADC_CS}', '~{DAC_SYNC}', '~{DAC_LDAC}', 'FA15', 'FA16',
        'OUT_EN', 'WD_KICK', 'LED_RUN', 'LED_FAULT', '~{OUT_FLT}', '~{FIELD_OK}', 'V_PB6', 'V_PB7']
check([pin('U4', 2 + i) for i in range(16)] == want, 'VIA PA0-PA7, PB0-PB7 as in the README')
check(all(n in board.EXP.values() for n in ('V_PB6', 'V_PB7', 'V_CA1', 'V_CA2', 'V_CB1', 'V_CB2', '~{CS6}', '~{CS7}')),
      'PB6, PB7, CA1, CA2, CB1, CB2, /CS6, /CS7 on the expansion header')

# ---------------------------------------------------------------- isolation
AREA_OF = {n: a for a, ns in board.AREAS.items() for n in ns}
AREA_OF['PE'] = 'PE'
parent = {}


def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


for r, p in P.items():
    if r in board.BRIDGES or (r[0] == 'J' and r[1].isdigit()):   # connectors don't join pins
        continue
    ns = [n for n in p['pins'].values() if n]
    for n in ns[1:]:
        parent[find(ns[0])] = find(n)
groups = {}
for n in N:
    groups.setdefault(find(n), set()).add(n)
mixed = []
area_of_net = {}
for g in groups.values():
    areas = {AREA_OF[n] for n in g if n in AREA_OF}
    if len(areas) > 1:
        mixed.append(sorted(areas))
    a = next(iter(areas)) if len(areas) == 1 else None
    for n in g:
        area_of_net[n] = a
check(not mixed, 'no part outside the bridges joins two isolated areas %s' % mixed)
unassigned = sorted(n for n, a in area_of_net.items() if a is None)
check(not unassigned, 'every net belongs to one area %s' % unassigned[:8])
bridge_bad = []
for r, sides in board.BRIDGES.items():
    used = {area_of_net.get(n) for n in P[r]['pins'].values() if n}
    if used != set(sides):
        bridge_bad.append((r, sorted(x or '?' for x in used)))
check(not bridge_bad, 'each bridge (optos, isolators, DC-DCs, RS-485, PE cap) touches exactly its two areas %s' % bridge_bad)

# ---------------------------------------------------------------- digital inputs
okdi = True
for n in range(1, 17):
    u, ch = 'U%d' % (20 + (n - 1) // 4), (n - 1) % 4 + 1
    a = 'DI%d_A' % n
    k = 'DI%d_K' % n
    chain = (two_pin('R%d' % (100 + n)) == ('DI%d' % n, a)
             and two_pin('D%d' % (100 + n)) == (k, a)                 # LED: K, A
             and two_pin('D%d' % (120 + n)) == (a, '0V_IO')           # 1N4148W: K at the 4.7k
             and two_pin('R%d' % (120 + n)) == (k, '0V_IO')
             and two_pin('C%d' % (100 + n)) == (k, '0V_IO')
             and pin(u, 2 * ch - 1) == k and pin(u, 2 * ch) == '0V_IO'
             and pin(u, 18 - 2 * ch) == 'DIN%d' % n and pin(u, 17 - 2 * ch) == 'GND'
             and two_pin('R%d' % (140 + n)) == ('+5V', 'DIN%d' % n))
    buf, bit = ('U14', 'U15')[(n - 1) // 8], (n - 1) % 8
    bus = pin(buf, 2 + bit) == 'DIN%d' % n and pin(buf, 18 - bit) == 'D%d' % bit
    term = pin(('J2', 'J3')[(n - 1) // 8], bit + 1) == 'DI%d' % n
    if not (chain and bus and term):
        okdi = False
        print('       input %d: chain %s, bus %s, terminal %s' % (n, chain, bus, term))
check(okdi, '16 inputs: 4.7k, LED, opto (TLP291-4 pins), shunt, 1N4148W, pull-up; input n -> bit (n-1)%8')
check(all(pin(j, 9) == '24V_SNS' and pin(j, 10) == '0V_IO' for j in ('J2', 'J3'))
      and two_pin('F2') == ('24V_IO', '24V_SNS'), 'input terminals: sensor supply through the PTC, and 0V')

# ---------------------------------------------------------------- digital outputs
VNI_IN = {1: 2, 2: 4, 3: 8, 4: 10}
VNI_OUT = {1: (22, 23, 24), 2: (19, 20, 21), 3: (16, 17, 18), 4: (13, 14, 15)}
VNI_ST = {1: 3, 2: 5, 3: 7, 4: 9}
okdo = True
for n in range(1, 17):
    latch, bit = ('U16', 'U17')[(n - 1) // 8], (n - 1) % 8
    u, ch = 'U%d' % (24 + (n - 1) // 4), (n - 1) % 4 + 1
    vni = 'U%d' % (30 + (n - 1) // 4)
    o = 'OUT%d' % n
    chain = (pin(latch, 2 + bit) == 'D%d' % bit and pin(latch, 19 - bit) == 'DQ%d' % n
             and two_pin('R%d' % (200 + n)) == ('DQ%d' % n, 'DO%d_A' % n)
             and pin(u, 2 * ch - 1) == 'DO%d_A' % n and pin(u, 2 * ch) == 'GND'
             and pin(u, 18 - 2 * ch) == '+5V_IO' and pin(u, 17 - 2 * ch) == 'VIN%d' % n
             and two_pin('R%d' % (220 + n)) == ('VIN%d' % n, '0V_IO')
             and pin(vni, VNI_IN[ch]) == 'VIN%d' % n
             and all(pin(vni, k) == o for k in VNI_OUT[ch]) and pin(vni, VNI_ST[ch]) == 'OUT_FLT'
             and two_pin('R%d' % (240 + n)) == (o, 'DO%d_L' % n)
             and two_pin('D%d' % (200 + n)) == ('0V_IO', 'DO%d_L' % n))
    j, jp = ('J4', bit + 3) if n <= 8 else ('J5', bit + 1)
    if not (chain and pin(j, jp) == o):
        okdo = False
        print('       output %d: chain %s, terminal %s' % (n, chain, pin(j, jp) == o))
check(okdo, '16 outputs: latch bit -> 1k -> opto -> VNI4140K IN, all 3 OUT pins, STAT, LED; output n = bit (n-1)%8')
check(pin('J4', 1) == '24V_IO' and pin('J4', 2) == '0V_IO', 'field supply in on J4 pins 1-2')
check(pin('U35', 1) == 'FLT_A' and pin('U35', 2) == 'OUT_FLT' and pin('U35', 16) == '~{OUT_FLT}'
      and two_pin('R30') == ('+5V_IO', 'FLT_A'), 'any VNI STAT low -> opto -> PB4 low')
check(pin('U35', 3) == 'FPW_A' and pin('U35', 4) == '0V_IO' and pin('U35', 14) == '~{FIELD_OK}'
      and two_pin('R31') == ('24V_IO', 'FPW_A'), 'field supply present -> opto -> PB5 low')

# ---------------------------------------------------------------- analog
check(pin('U42', 3) == 'SPI_SCLK' and pin('U42', 14) == 'SCLK_I' and pin('U42', 4) == 'SPI_MOSI'
      and pin('U42', 13) == 'MOSI_I' and pin('U42', 5) == '~{ADC_CS}' and pin('U42', 12) == '~{ADC_CS_I}'
      and pin('U42', 11) == 'MISO_I' and pin('U42', 6) == 'SPI_MISO'
      and pin('U42', 7) == '+5V' and pin('U42', 10) == '+5VA',
      'ISO7741: INA-C -> OUTA-C (SCLK, MOSI, ADC /CS), IND -> OUTD (MISO), EN1/EN2 high')
check(pin('U43', 2) == '~{DAC_SYNC}' and pin('U43', 7) == '~{DAC_SYNC_I}' and pin('U43', 3) == '~{DAC_LDAC}'
      and pin('U43', 6) == '~{DAC_LDAC_I}', 'ISO7720: INA -> OUTA (/SYNC), INB -> OUTB (/LDAC)')
check(pin('U44', 10) == '~{ADC_CS_I}' and pin('U44', 11) == 'MOSI_I' and pin('U44', 12) == 'MISO_I'
      and pin('U44', 13) == 'SCLK_I' and pin('U44', 15) == 'VREF_ADC' and pin('U41', 2) == 'VREF_ADC',
      'MCP3208: /CS, DIN, DOUT, CLK, VREF from the REF3040')
check(pin('U45', 2) == '~{DAC_SYNC_I}' and pin('U45', 1) == '~{DAC_LDAC_I}' and pin('U45', 15) == 'MOSI_I'
      and pin('U45', 16) == 'SCLK_I' and pin('U45', 9) == 'DAC_CLR' and two_pin('R34') == ('+5VA', 'DAC_CLR'),
      'DAC7568: /SYNC, /LDAC, DIN, SCLK; /CLR held high')
DAC_OUT = {1: 4, 2: 13, 3: 5, 4: 12, 5: 6, 6: 11, 7: 7, 8: 10}
okai = True
for n in range(1, 9):
    p = 'AI%d' % n
    c = (two_pin('F%d' % (300 + n)) == (p, p + '_P')
         and two_pin('D%d' % (300 + n)) == (p + '_P', 'AGND_ISO')
         and two_pin('JP%d' % (300 + n)) == (p + '_P', p + '_M')
         and two_pin('R%d' % (330 + n)) == (p + '_M', 'AGND_ISO') and P['R%d' % (330 + n)]['value'] == '499'
         and two_pin('R%d' % (300 + n)) == (p + '_P', p + '_D') and P['R%d' % (300 + n)]['value'] == '15k'
         and two_pin('R%d' % (310 + n)) == (p + '_D', 'AGND_ISO') and P['R%d' % (310 + n)]['value'] == '10k'
         and two_pin('R%d' % (320 + n)) == (p + '_D', 'ADC%d' % n)
         and two_pin('C%d' % (300 + n)) == ('ADC%d' % n, 'AGND_ISO')
         and [pin('D%d' % (310 + n), k) for k in (1, 2, 3)] == ['AGND_ISO', '+5VA', 'ADC%d' % n]
         and pin('U44', n) == 'ADC%d' % n)
    if not c:
        okai = False
        print('       analog input %d wrong' % n)
check(okai, '8 analog inputs: PTC, TVS, mA jumper + 499R, 15k/10k, 1k, 100 nF, BAV99 (3 = common), CHn-1')
check([pin('J6', k) for k in range(1, 13)] == ['AI1', 'AI2', 'AGND_ISO', 'AI3', 'AI4', 'AGND_ISO',
                                               'AI5', 'AI6', 'AGND_ISO', 'AI7', 'AI8', 'AGND_ISO'],
      'analog input terminal J6')
okao = True
for n in range(1, 9):
    p = 'AO%d_' % n
    amp_u = ('U46', 'U47')[(n - 1) // 4]
    o, m, pl = board.AMP[(n - 1) % 4 + 1]
    c = (pin('U45', DAC_OUT[n]) == p + 'DAC' and pin(amp_u, pl) == p + 'DAC'
         and pin(amp_u, o) == p + 'OA' and pin(amp_u, m) == p + 'INV'
         and two_pin('R%d' % (400 + n)) == (p + 'OA', p + 'B')
         and [pin('Q%d' % (400 + n), k) for k in (1, 2, 3)] == [p + 'E', '+24VA', p + 'B']
         and two_pin('R%d' % (410 + n)) == (p + 'E', p + 'X')
         and [pin('Q%d' % (410 + n), k) for k in (1, 2, 3)] == [p + 'E', p + 'X', p + 'B']
         and two_pin('F%d' % (400 + n)) == (p + 'X', 'AO%d' % n)
         and two_pin('D%d' % (400 + n)) == ('AO%d' % n, 'AGND_ISO')
         and two_pin('R%d' % (420 + n)) == ('AO%d' % n, p + 'FV')
         and two_pin('R%d' % (430 + n)) == (p + 'FV', 'AGND_ISO')
         and two_pin('R%d' % (440 + n)) == (p + 'IS', 'AGND_ISO')
         and two_pin('R%d' % (450 + n)) == (p + 'FB', p + 'INV')
         and two_pin('C%d' % (400 + n)) == (p + 'OA', p + 'INV')
         and [pin('JP%d' % (400 + n), k) for k in range(1, 7)]
         == [p + 'FV', 'AGND_ISO', p + 'FB', 'AOC%d' % n, p + 'IS', p + 'IS'])
    if not c:
        okao = False
        print('       analog output %d wrong' % n)
check(okao, '8 analog outputs: DAC ch -> LM324 -> 1k -> BCX56 (1 E, 2 C, 3 B) -> 22R + BC847 limit -> PTC; V/mA jumper')
# gains: V mode 2.5 V * (1 + 30k/10k) = 10 V; mA mode 2.5 V / 124 R
check(P['R421']['value'] == '30k' and P['R431']['value'] == '10k' and P['R441']['value'] == '124',
      'V mode: 0-2.5 V x 4 = 0-10 V; mA mode: 2.5 V / 124 R = 20.2 mA full scale')
check([pin('J7', k) for k in range(1, 9)] == ['AO1', 'AOC1', 'AO2', 'AOC2', 'AO3', 'AOC3', 'AO4', 'AOC4']
      and [pin('J8', k) for k in range(1, 10)] == ['AO5', 'AOC5', 'AO6', 'AOC6', 'AO7', 'AOC7', 'AO8', 'AOC8', 'AGND_ISO'],
      'analog output terminals J7, J8')

# ---------------------------------------------------------------- power and RS-485
check(two_pin('F1') == ('24V_RAW', '24V_F') and two_pin('D1') == ('+24V', '24V_F')
      and two_pin('D2') == ('+24V', 'GND'), '24 V in: fuse, SS34 (K to +24V), SMBJ33A')
check(two_pin('R22') == ('+5V', 'BUCK_FB') and two_pin('R23') == ('BUCK_FB', 'GND')
      and abs(1.0 * (1 + 100 / 24.9) - 5.0) < 0.05, 'LMR36520 feedback: 1 V x (1 + 100k/24.9k) = 5.02 V')
check(pin('U13', 3) == '+24V' and pin('U13', 7) == 'BUCK_BOOT' and pin('U13', 8) == 'BUCK_SW'
      and two_pin('C7') == ('BUCK_BOOT', 'BUCK_SW') and two_pin('L1') == ('BUCK_SW', '+5V'),
      'LMR36520: EN to VIN, BOOT cap to SW, inductor SW -> +5V')
check(pin('U50', 3) == 'UA_RX' and pin('U50', 6) == 'UA_TX' and pin('U50', 4) == pin('U50', 5) == 'DIR485'
      and pin('U5', 38) == 'UA_TX' and pin('U5', 39) == 'UA_RX',
      'CA-IS3082WX: RO -> RXA, TXA -> DI, DE = /RE = DIR485')
check(pin('J9', 1) == 'RS485_A' and pin('J9', 2) == 'RS485_B' and pin('D7', 3) == 'GND_485',
      'RS-485 terminal A, B, 0V; SM712 common to GND_485')
check(pin('J10', 4) == 'SER_RX' and pin('J10', 5) == 'SER_TX' and pin('U5', 25) == 'SER_RX'
      and pin('U5', 26) == 'SER_TX', 'USB header TXD -> RXB, TXB -> header RXD')

print('ALL PASSED' if ok else 'FAILED')
sys.exit(0 if ok else 1)
