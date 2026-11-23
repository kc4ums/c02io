"""Write the C02IO schematic from board.py: every part, every pin labelled with its net.

    python mk_sch.py

c02io.kicad_sch is the root sheet; it holds one sheet symbol per block, and
each block is its own file (sch_*.kicad_sch). Chips are drawn as boxes in
package pin order (pin 1 top left), with a global label on every pin, so
equal labels join across sheets and the schematic is the same netlist as
the board. Unused pins get a no-connect flag. Pin names come from the
datasheet pin tables listed in board.py.

check_sch.py runs KiCad's ERC and compares the schematic's netlist with board.py.
"""
import os
import uuid

import board

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = 'c02io'
G = 2.54
NS = uuid.UUID('6f3f0c9e-1c55-4a5e-9a64-0c02c010a001')
ROOT = str(uuid.uuid5(NS, 'root'))


def uid(*k):
    return str(uuid.uuid5(NS, '/'.join(map(str, k))))


# ------------------------------------------------------------ pin names
def names(*seq):
    return {i + 1: n for i, n in enumerate(seq)}


HC00 = names('1A', '1B', '1Y', '2A', '2B', '2Y', 'GND', '3Y', '3A', '3B', '4Y', '4A', '4B', 'VCC')
def _cm5_names():
    """CM5 pin names (datasheet Table 4) for the pins this board uses."""
    gpio = {v: 'GPIO%d' % k for k, v in board.CM5_GPIO.items()}
    fixed = {77: '+5V_IN', 79: '+5V_IN', 81: '+5V_IN', 83: '+5V_IN', 85: '+5V_IN', 87: '+5V_IN',
             84: '+3V3_OUT', 86: '+3V3_OUT', 78: 'GPIO_VREF', 12: 'ETH_P0_P', 10: 'ETH_P0_N',
             4: 'ETH_P1_P', 6: 'ETH_P1_N', 11: 'ETH_P2_P', 9: 'ETH_P2_N', 3: 'ETH_P3_P', 5: 'ETH_P3_N',
             15: 'ETH_~{LED3}', 17: 'ETH_~{LED2}', 21: 'LED_~{ACT}', 92: 'PWR_BUT', 93: '~{RPIBOOT}',
             103: 'USB_N', 105: 'USB_P'}
    out = {}
    for k, n in board.P_BY_REF['U1']['pins'].items():
        if n:
            k = int(k)
            out[k] = 'GND' if n == 'GND' else fixed.get(k) or gpio[k]
    return out


PINNAMES = {
    'CM5': _cm5_names(),
    '74HC165': names('SH/~{LD}', 'CLK', 'E', 'F', 'G', 'H', '~{QH}', 'GND', 'QH', 'SER', 'A', 'B',
                     'C', 'D', 'CLK_INH', 'VCC'),
    '74HC595': names('QB', 'QC', 'QD', 'QE', 'QF', 'QG', 'QH', 'GND', "QH'", '~{SRCLR}', 'SRCLK',
                     'RCLK', '~{OE}', 'SER', 'QA', 'VCC'),
    'TPS54560B': names('BOOT', 'VIN', 'EN', 'RT/CLK', 'FB', 'COMP', 'GND', 'SW', 'PAD'),
    'USBLC6-2SC6': names('I/O1', 'GND', 'I/O2', 'I/O2', 'VBUS', 'I/O1'),
    'RJ45_MAGJACK': names('TRD0+', 'TRD0-', 'TRD1+', 'CT', 'CT', 'TRD1-', 'TRD2+', 'TRD2-', 'TRD3+',
                          'TRD3-', 'VC1', 'VC2', 'VC3', 'VC4', 'LEDY_A', 'LEDY_K', 'LEDG_A', 'LEDG_K',
                          'SHIELD', 'SHIELD'),
    'USB_C_2.0': {'A1': 'GND', 'A4': 'VBUS', 'A5': 'CC1', 'A6': 'D+', 'A7': 'D-', 'A8': 'SBU1',
                  'A9': 'VBUS', 'A12': 'GND', 'B1': 'GND', 'B4': 'VBUS', 'B5': 'CC2', 'B6': 'D+',
                  'B7': 'D-', 'B8': 'SBU2', 'B9': 'VBUS', 'B12': 'GND', 'SH': 'SHIELD'},
    'W65C02S': names('VPB', 'RDY', 'PHI1O', 'IRQB', 'MLB', 'NMIB', 'SYNC', 'VDD',
                     *['A%d' % i for i in range(12)], 'VSS', 'A12', 'A13', 'A14', 'A15',
                     *['D%d' % i for i in range(7, -1, -1)], 'RWB', 'NC', 'BE', 'PHI2', 'SOB',
                     'PHI2O', 'RESB'),
    'AS6C62256': names('A14', 'A12', 'A7', 'A6', 'A5', 'A4', 'A3', 'A2', 'A1', 'A0', 'DQ0', 'DQ1',
                       'DQ2', 'VSS', 'DQ3', 'DQ4', 'DQ5', 'DQ6', 'DQ7', '~{CE}', 'A10', '~{OE}', 'A11',
                       'A9', 'A8', 'A13', '~{WE}', 'VCC'),
    'SST39SF010A': names('NC', 'A16', 'A15', 'A12', 'A7', 'A6', 'A5', 'A4', 'A3', 'A2', 'A1', 'A0',
                         'DQ0', 'DQ1', 'DQ2', 'VSS', 'DQ3', 'DQ4', 'DQ5', 'DQ6', 'DQ7', '~{CE}', 'A10',
                         '~{OE}', 'A11', 'A9', 'A8', 'A13', 'A14', 'NC', '~{WE}', 'VDD'),
    'W65C22N': names('VSS', *['PA%d' % i for i in range(8)], *['PB%d' % i for i in range(8)], 'CB1',
                     'CB2', 'VDD', 'IRQB', 'RWB', 'CS2B', 'CS1', 'PHI2', *['D%d' % i for i in range(7, -1, -1)],
                     'RESB', 'RS3', 'RS2', 'RS1', 'RS0', 'CA2', 'CA1'),
    'TL16C2552': names('~{TXRDYA}', *['D%d' % i for i in range(8)], 'A0', 'XTAL1', 'GND', 'XTAL2', 'A1',
                       'A2', 'CHSEL', 'INTB', '~{CS}', 'MFB', '~{IOW}', 'RESET', 'GND', '~{RTSB}', '~{IOR}',
                       'RXB', 'TXB', '~{DTRB}', '~{CTSB}', '~{DSRB}', '~{CDB}', '~{RIB}', '~{TXRDYB}', 'VCC',
                       'INTA', 'MFA', '~{RTSA}', '~{DTRA}', 'TXA', 'RXA', '~{CTSA}', '~{DSRA}', '~{CDA}',
                       '~{RIA}', 'VCC'),
    '74HC00': HC00, '74HC32': HC00,
    '74HC30': names('A', 'B', 'C', 'D', 'E', 'F', 'GND', 'Y', 'NC', 'NC', 'G', 'H', 'NC', 'VCC'),
    '74HC138': names('A0', 'A1', 'A2', '~{E1}', '~{E2}', 'E3', 'Y7', 'GND', 'Y6', 'Y5', 'Y4', 'Y3',
                     'Y2', 'Y1', 'Y0', 'VCC'),
    '74HC541': names('~{OE1}', *['A%d' % i for i in range(1, 9)], 'GND',
                     *['Y%d' % i for i in range(8, 0, -1)], '~{OE2}', 'VCC'),
    '74HC574': names('~{OE}', *['%dD' % i for i in range(1, 9)], 'GND', 'CLK',
                     *['%dQ' % i for i in range(8, 0, -1)], 'VCC'),
    'CD74HC123': names('~{1A}', '1B', '~{1R}', '~{1Q}', '2Q', '2CX', '2RXCX', 'GND', '~{2A}', '2B', '~{2R}',
                       '~{2Q}', '1Q', '1CX', '1RXCX', 'VCC'),
    'DS1813': names('~{RST}', 'VCC', 'GND'),
    'OSC': names('OE', 'GND', 'OUT', 'VDD'),
    'LMR36520': names('PGND', 'VIN', 'EN', 'PG', 'FB', 'VCC', 'BOOT', 'SW', 'PAD'),
    'TLP291-4': names('A1', 'K1', 'A2', 'K2', 'A3', 'K3', 'A4', 'K4', 'E4', 'C4', 'E3', 'C3', 'E2', 'C2',
                      'E1', 'C1'),
    'VNI4140K': names('VCC', 'IN1', '~{STAT1}', 'IN2', '~{STAT2}', 'GND', '~{STAT3}', 'IN3', '~{STAT4}',
                      'IN4', 'NC', 'NC', 'OUT4', 'OUT4', 'OUT4', 'OUT3', 'OUT3', 'OUT3', 'OUT2', 'OUT2',
                      'OUT2', 'OUT1', 'OUT1', 'OUT1', 'TAB(VCC)'),
    '78L05': names('OUT', 'GND', 'IN'),
    'REF3040': names('IN', 'OUT', 'GND'),
    'ISO7741': names('VCC1', 'GND1', 'INA', 'INB', 'INC', 'OUTD', 'EN1', 'GND1', 'GND2', 'EN2', 'IND',
                     'OUTC', 'OUTB', 'OUTA', 'GND2', 'VCC2'),
    'ISO7720': names('VCC1', 'INA', 'INB', 'GND1', 'GND2', 'OUTB', 'OUTA', 'VCC2'),
    'MCP3208': names(*['CH%d' % i for i in range(8)], 'DGND', '~{CS}', 'DIN', 'DOUT', 'CLK', 'AGND',
                     'VREF', 'VDD'),
    'DAC7568': names('~{LDAC}', '~{SYNC}', 'AVDD', 'VOUTA', 'VOUTC', 'VOUTE', 'VOUTG', 'VREF', '~{CLR}',
                     'VOUTH', 'VOUTF', 'VOUTD', 'VOUTB', 'GND', 'DIN', 'SCLK'),
    'LM324': names('1OUT', '1IN-', '1IN+', 'VCC', '2IN+', '2IN-', '2OUT', '3OUT', '3IN-', '3IN+', 'GND',
                   '4IN+', '4IN-', '4OUT'),
    'CA-IS3082WX': names('VDDA', 'GNDA', 'RO', '~{RE}', 'DE', 'DI', 'GNDA', 'GNDA', 'GNDB', 'GNDB', 'NC',
                         'A', 'B', 'NC', 'GNDB', 'VDDB'),
    'URB2424YMD': {1: 'GND', 2: 'VIN', 3: '+VO', 5: '0V'},
    'B0505XT': {1: 'GND', 2: 'VIN', 4: '0V', 5: '+VO', 8: 'NC'},
    'BC847': names('B', 'E', 'C'),
    'BCX56': names('E', 'C', 'B'),
    'BAV99': names('A1', 'K2', 'K1/A2'),
    'SM712': names('IO1', 'IO2', 'GND'),
}


def kind(p):
    """(symbol name, {pin: name}, style): style 'box' (pins down both sides),
    'side' (one column), 'two' (two-terminal), 'none' (no pins)."""
    v, fp, ref = p['value'], p['fp'], p['ref']
    if fp == 'RJ45':
        return 'RJ45_MAGJACK', PINNAMES['RJ45_MAGJACK'], 'box'
    if fp == 'USBC':
        return 'USB_C_2.0', PINNAMES['USB_C_2.0'], 'box'
    for prefix, name in (('TPS54560', 'TPS54560B'), ('ISO7741', 'ISO7741'), ('ISO7720', 'ISO7720'),
                         ('DAC7568', 'DAC7568'), ('URB2424', 'URB2424YMD'), ('B0505XT', 'B0505XT')):
        if v.startswith(prefix):
            return name, PINNAMES[name], 'box' if len(PINNAMES[name]) > 5 else 'side'
    if v in PINNAMES:
        pn = PINNAMES[v]
        return v, pn, 'box' if len(pn) > 5 else 'side'
    if fp == 'OSC':
        return 'OSC', PINNAMES['OSC'], 'side'
    if fp.startswith('TB'):
        n = len(p['pins'])
        return 'TERMINAL_%d' % n, {i: str(i) for i in range(1, n + 1)}, 'side'
    if fp.startswith('H') and fp[1].isdigit():
        n = {'H1x2': 2, 'H1x3': 3, 'H2x3': 6, 'H2x5': 10}[fp]
        return 'HEADER_%s' % fp[1:], {i: str(i) for i in range(1, n + 1)}, 'side' if n <= 6 else 'box'
    if fp == 'HOLE':
        return 'MOUNTING_HOLE', {}, 'none'
    if fp == 'HOLE_PE':
        return 'MOUNTING_HOLE_PE', {1: 'PE'}, 'side'
    if fp == 'SW':
        return 'SWITCH', {1: '', 2: ''}, 'two'
    if fp in ('LED', 'SOD123', 'SMA', 'SMB', 'SMC'):
        return 'DIODE', {1: 'K', 2: 'A'}, 'two'
    if fp == 'CP10':
        return 'C_POL', {1: '+', 2: ''}, 'two'
    if fp.startswith('C'):
        return 'C', {1: '', 2: ''}, 'two'
    if fp.startswith('R'):
        return 'R', {1: '', 2: ''}, 'two'
    if fp.startswith('F'):
        return 'FUSE', {1: '', 2: ''}, 'two'
    if fp.startswith('L'):
        return 'L', {1: '', 2: ''}, 'two'
    raise SystemExit('no symbol for ' + ref)


def pin_layout(pn, style):
    """[(number, name, x, y, angle)] in library coordinates (y up), and the body box."""
    nums = sorted(pn)
    out = []
    if style == 'box':
        n = len(nums)
        h = (n + 1) // 2                               # left column gets the odd one
        left, right = nums[:h], nums[h:][::-1]
        for i, k in enumerate(left):
            out.append((k, pn[k], -12.7, (h - 1 - i) * G, 0))
        for i, k in enumerate(right):
            out.append((k, pn[k], 12.7, (h - 1 - i) * G, 180))
        box = (-10.16, (h - 1) * G + G, 10.16, -G)
    elif style == 'side':
        n = len(nums)
        for i, k in enumerate(nums):
            out.append((k, pn[k], -10.16, (n - 1 - i) * G, 0))
        box = (-7.62, (n - 1) * G + G, 7.62, -G)
    elif style == 'two':
        out = [(1, pn[1], 0, 3.81, 270), (2, pn[2], 0, -3.81, 90)]
        box = (-1.016, 2.54, 1.016, -2.54)
    else:
        box = (-2.54, 2.54, 2.54, -2.54)
    return out, box


def eff(size=1.27, justify=None, hide=False):
    j = ' (justify %s)' % justify if justify else ''
    return '(effects (font (size %g %g))%s)%s' % (size, size, j, ' (hide yes)' if hide else '')


def lib_symbol(name, pn, style):
    pins, (x0, y0, x1, y1) = pin_layout(pn, style)
    s = ['(symbol "%s:%s" (pin_names (offset 0.508)) (exclude_from_sim no) (in_bom yes) (on_board yes)'
         % (PROJECT, name)]
    if style == 'two':
        s[0] = s[0].replace('(pin_names (offset 0.508))', '(pin_numbers (hide yes)) (pin_names (offset 0) (hide yes))')
    s.append('(property "Reference" "U" (at 0 %g 0) %s)' % (y0 + 2, eff()))
    s.append('(property "Value" "%s" (at 0 %g 0) %s)' % (name, y0 + 4, eff()))
    s.append('(property "Footprint" "" (at 0 0 0) %s)' % eff(hide=True))
    s.append('(property "Datasheet" "" (at 0 0 0) %s)' % eff(hide=True))
    if style == 'none':
        s.append('(symbol "%s_0_1" (circle (center 0 0) (radius 1.6) (stroke (width 0.254) (type default)) '
                 '(fill (type none))))' % name)
    else:
        s.append('(symbol "%s_0_1" (rectangle (start %g %g) (end %g %g) (stroke (width 0.254) (type default)) '
                 '(fill (type background))))' % (name, x0, y0, x1, y1))
    s.append('(symbol "%s_1_1"' % name)
    for num, nm, x, y, a in pins:
        length = 1.27 if style == 'two' else 2.54
        s.append('(pin passive line (at %g %g %d) (length %g) (name "%s" %s) (number "%s" %s))' % (
            x, y, a, length, nm, eff(), num, eff()))
    s.append(')')
    s.append('(embedded_fonts no))')
    return '\n'.join(s)


# ------------------------------------------------------------ sheets
# Each sheet: (file stem, title, rows). A row is a list of references drawn
# left to right; long rows wrap.
SHEETS = [
    ('cm5', 'Compute Module 5, Ethernet, USB-C, expansion', [
        ['U1', 'C11', 'C12', 'C13'], ['J12', 'C70', 'R25', 'R26'],
        ['J13', 'U51', 'R27', 'R28', 'C71'], ['J11', 'JP1', 'SW1', 'D8', 'R24', 'R29']]),
    ('logic', 'Watchdog, SPI chip-select pull-ups, LEDs', [
        ['U11', 'C14', 'R5', 'C5', 'R6', 'R7'], ['R15', 'R16', 'R17'],
        ['D3', 'R18', 'D4', 'R19', 'D5', 'R20']]),
    ('power', '24 V input, 5 V buck, mounting holes', [
        ['J1', 'F1', 'D1', 'D2', 'C1', 'C2', 'C3', 'C4', 'C6'],
        ['U13', 'C7', 'R8', 'R9', 'C8', 'C15', 'D9', 'L1', 'R22', 'R23', 'C9', 'C10', 'C16'],
        ['H1', 'H2', 'H3', 'H4']]),
    ('inputs', 'Digital inputs 1-16 (field side 0V_IO, opto-isolated)', [
        ['J2', 'J3'], ['U20', 'U21', 'U22', 'U23'], ['U14', 'C24', 'U15', 'C25']] + [
        ['R%d' % (100 + n), 'D%d' % (120 + n), 'D%d' % (100 + n), 'R%d' % (120 + n), 'C%d' % (100 + n),
         'R%d' % (140 + n)] for n in range(1, 17)]),
    ('outputs', 'Digital outputs 1-16, field supply, status', [
        ['J4', 'J5'], ['U16', 'C26', 'U17', 'C27'], ['U24', 'U25', 'U26', 'U27'],
        ['U30', 'C30', 'U31', 'C31'], ['U32', 'C32', 'U33', 'C33'],
        ['D6', 'C34', 'F2', 'U34', 'C35', 'C36'], ['U35', 'R30', 'R31', 'R32', 'R33']] + [
        ['R%d' % (200 + n), 'R%d' % (220 + n), 'R%d' % (240 + n), 'D%d' % (200 + n), 'C%d' % (200 + n)]
        for n in range(1, 17)]),
    ('analog_in', 'Analog isolation, ADC, analog inputs 1-8', [
        ['PS1', 'C40', 'C41', 'U40', 'C42', 'C43', 'U41', 'C44', 'C45'],
        ['U42', 'C46', 'C47', 'U43', 'C48', 'C49'], ['U44', 'C50', 'J6']] + [
        ['F%d' % (300 + n), 'D%d' % (300 + n), 'JP%d' % (300 + n), 'R%d' % (330 + n), 'R%d' % (300 + n),
         'R%d' % (310 + n), 'R%d' % (320 + n), 'C%d' % (300 + n), 'D%d' % (310 + n)] for n in range(1, 9)]),
    ('analog_out', 'DAC, analog outputs 1-8 (0-10 V / 4-20 mA)', [
        ['U45', 'C51', 'C52', 'R34'], ['U46', 'C53', 'U47', 'C54'], ['J7', 'J8']] + [
        ['R%d' % (450 + n), 'C%d' % (400 + n), 'R%d' % (400 + n), 'Q%d' % (400 + n), 'R%d' % (410 + n),
         'Q%d' % (410 + n), 'F%d' % (400 + n), 'D%d' % (400 + n), 'C%d' % (410 + n), 'R%d' % (420 + n),
         'R%d' % (430 + n), 'R%d' % (440 + n), 'JP%d' % (400 + n)] for n in range(1, 9)]),
    ('rs485', 'Isolated RS-485 (UART0)', [
        ['PS2', 'C60', 'C61', 'R50'], ['U50', 'C62', 'C63', 'C64', 'R51'],
        ['R52', 'R53', 'R54', 'JP3', 'D7', 'J9']]),
]

P = {p['ref']: p for p in board.PARTS}
_placed = [r for _, _, rows in SHEETS for row in rows for r in row]
_missing = sorted(set(P) - set(_placed))
_twice = sorted({r for r in _placed if _placed.count(r) > 1})
if _missing or _twice:
    raise SystemExit('sheet lists: missing %s, twice %s' % (_missing, _twice))


def snap(v):
    return round(v / G) * G


def label_w(net):
    return len(net) * 1.0 + 4.0


def size(p):
    name, pn, style = kind(p)
    pins, (x0, y0, x1, y1) = pin_layout(pn, style)
    nets = [p['pins'].get(str(k)) or '' for k in pn]
    lw = max([label_w(n) for n in nets] or [0])
    if style == 'two':
        return 10.16, 7.62 + 2 * lw + 6
    if style == 'none':
        return 10.16, 10.16
    if style == 'side':
        return 20.32 + lw + 6, (y0 - y1) + 12
    return 25.4 + 2 * lw + 6, (y0 - y1) + 12


PAPERS = [('A3', 420, 297), ('A2', 594, 420), ('A1', 841, 594), ('A0', 1189, 841)]


def layout(rows, width):
    """Positions (x, y) of each part's top-left corner; returns them and the height used."""
    pos, y = {}, 20.0
    for row in rows:
        x, rowh = 12.0, 0
        for ref in row:
            w, h = size(P[ref])
            if x + w > width - 12 and x > 12:
                x, y, rowh = 12.0, y + rowh + 4, 0
            pos[ref] = (x, y, w, h)
            x += w + 4
            rowh = max(rowh, h)
        y += rowh + 6
    return pos, y


def sheet_file(stem, title, rows, sheet_uuid, page):
    for paper, W, H in PAPERS:
        pos, used = layout(rows, W)
        if used < H - 30:
            break
    syms, insts, labels, ncs = {}, [], [], []
    path = '/%s/%s' % (ROOT, sheet_uuid)
    for ref, (x, y, w, h) in pos.items():
        p = P[ref]
        name, pn, style = kind(p)
        syms[name] = lib_symbol(name, pn, style)
        pins, (bx0, by0, bx1, by1) = pin_layout(pn, style)
        lw = max([label_w(p['pins'].get(str(k)) or '') for k in pn] or [0])
        if style == 'two':
            ox, oy = snap(x + w / 2), snap(y + lw + 4.5)
        elif style == 'none':
            ox, oy = snap(x + 5), snap(y + 5)
        elif style == 'side':
            ox, oy = snap(x + lw + 11), snap(y + 6 + by0)
        else:
            ox, oy = snap(x + lw + 14), snap(y + 6 + by0)
        props = ['(property "Reference" "%s" (at %g %g 0) %s)' % (
                     ref, ox + (3 if style == 'two' else 0), oy - by0 - (1 if style == 'two' else 3.5),
                     eff(1.27, 'left' if style == 'two' else None)),
                 '(property "Value" "%s" (at %g %g 0) %s)' % (
                     p['value'], ox + (3 if style == 'two' else 0), oy - by0 + (1.5 if style == 'two' else -1.2),
                     eff(1.27, 'left' if style == 'two' else None)),
                 '(property "Footprint" "%s" (at %g %g 0) %s)' % (board.FP[p['fp']], ox, oy, eff(hide=True)),
                 '(property "Datasheet" "" (at %g %g 0) %s)' % (ox, oy, eff(hide=True))]
        if p['mpn']:
            props.append('(property "MPN" "%s" (at %g %g 0) %s)' % (p['mpn'].replace('"', "'"), ox, oy, eff(hide=True)))
        if p['note']:
            props.append('(property "Note" "%s" (at %g %g 0) %s)' % (p['note'].replace('"', "'"), ox, oy, eff(hide=True)))
        pinl = ' '.join('(pin "%s" (uuid "%s"))' % (k, uid('p', ref, k)) for k in pn)
        insts.append('(symbol (lib_id "%s:%s") (at %g %g 0) (unit 1) (exclude_from_sim no) (in_bom %s) '
                     '(on_board yes) (dnp %s) (uuid "%s") %s %s (instances (project "%s" '
                     '(path "%s" (reference "%s") (unit 1)))))' % (
                         PROJECT, name, ox, oy, 'no' if p['dnp'] or style == 'none' else 'yes',
                         'yes' if p['dnp'] else 'no', uid('s', ref), ' '.join(props), pinl, PROJECT, path, ref))
        for num, nm, px, py, a in pins:
            ex, ey = ox + px, oy - py
            net = p['pins'].get(str(num))
            if not net:
                ncs.append('(no_connect (at %g %g) (uuid "%s"))' % (ex, ey, uid('nc', ref, num)))
                continue
            ang, just = {0: (180, 'right'), 180: (0, 'left'), 270: (90, 'left'), 90: (270, 'right')}[a]
            labels.append('(global_label "%s" (shape passive) (at %g %g %d) (fields_autoplaced yes) %s '
                          '(uuid "%s") (property "Intersheetrefs" "${INTERSHEET_REFS}" (at %g %g 0) %s))' % (
                              net, ex, ey, ang, eff(1.27, just), uid('l', ref, num), ex, ey, eff(hide=True)))
    head = ('(kicad_sch (version 20250610) (generator "c02io_mk_sch") (generator_version "10.0") '
            '(uuid "%s") (paper "%s") (title_block (title "C02IO: %s") (rev "A") (company "KC4UMS") '
            '(comment 1 "Generated from board.py by mk_sch.py; edit board.py, not this file")) '
            % (uid('file', stem), paper, title))
    body = ['(lib_symbols', *syms.values(), ')', *insts, *labels, *ncs, '(embedded_fonts no))']
    with open(os.path.join(HERE, 'sch_%s.kicad_sch' % stem), 'w') as f:
        f.write(head + '\n'.join(body) + '\n')
    return syms, len(insts), len(labels), len(ncs), paper


def build():
    allsyms, sheets, totals = {}, [], [0, 0, 0]
    for i, (stem, title, rows) in enumerate(SHEETS):
        su = uid('sheet', stem)
        syms, ni, nl, nn, paper = sheet_file(stem, title, rows, su, i + 2)
        allsyms.update(syms)
        totals = [totals[0] + ni, totals[1] + nl, totals[2] + nn]
        x, y = 20 + (i % 4) * 95, 40 + (i // 4) * 50
        sheets.append(
            '(sheet (at %g %g) (size 80 30) (fields_autoplaced yes) (stroke (width 0.1524) (type solid)) '
            '(fill (color 0 0 0 0.0000)) (uuid "%s") '
            '(property "Sheetname" "%s" (at %g %g 0) %s) '
            '(property "Sheetfile" "sch_%s.kicad_sch" (at %g %g 0) %s) '
            '(instances (project "%s" (path "/%s" (page "%d")))))' % (
                x, y, su, title.split(' (')[0], x, y - 0.7, eff(1.27, 'left bottom'),
                stem, x, y + 30.6, eff(1.27, 'left top'), PROJECT, ROOT, i + 2))
        print('  sch_%s.kicad_sch (%s): %d symbols, %d labels, %d no-connects' % (stem, paper, ni, nl, nn))
    head = ('(kicad_sch (version 20250610) (generator "c02io_mk_sch") (generator_version "10.0") '
            '(uuid "%s") (paper "A3") (title_block (title "C02IO: W65C02S industrial I/O board") (rev "A") '
            '(company "KC4UMS") (comment 1 "Generated from board.py by mk_sch.py; edit board.py, not this file")) '
            % ROOT)
    note = ('(text "One sheet per block. Every pin carries a global label with its net name, so equal labels '
            'join across sheets.\\nFour isolated grounds: GND (logic), 0V_IO (field digital), AGND_ISO (analog), '
            'GND_485 (RS-485)." (exclude_from_sim no) (at 20 160 0) %s (uuid "%s"))' % (
                eff(1.8, 'left bottom'), uid('note')))
    body = ['(lib_symbols)', *sheets, note, '(sheet_instances (path "/" (page "1")))', '(embedded_fonts no))']
    with open(os.path.join(HERE, PROJECT + '.kicad_sch'), 'w') as f:
        f.write(head + '\n'.join(body) + '\n')
    with open(os.path.join(HERE, PROJECT + '.kicad_sym'), 'w') as f:
        f.write('(kicad_symbol_lib (version 20251024) (generator "c02io_mk_sch") (generator_version "10.0")\n')
        f.write('\n'.join(v.replace('(symbol "%s:' % PROJECT, '(symbol "', 1) for v in allsyms.values()))
        f.write(')\n')
    with open(os.path.join(HERE, 'sym-lib-table'), 'w') as f:
        f.write('(sym_lib_table (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s.kicad_sym")'
                '(options "")(descr "C02IO symbols, made by mk_sch.py"))\n)\n' % (PROJECT, PROJECT))
    print('%s.kicad_sch: %d sheets, %d symbols, %d labels, %d no-connects' % (
        PROJECT, len(SHEETS), *totals))


if __name__ == '__main__':
    build()
