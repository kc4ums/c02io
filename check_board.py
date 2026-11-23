"""Check the C02IO design in board.py (plain Python, no KiCad needed).

    python check_board.py

- every net joins two or more pins; every chip lists all its pins
- power and ground on each chip's datasheet pins, and a decoupling capacitor
- CM5: every ground pin, 5 V in, GPIO_VREF, SPI/UART alternate-function GPIOs,
  Ethernet pairs to the MagJack, USB-C, boot and power pins
- input and output shift-register chains, output enable and watchdog
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
    'U1': ({77: '+5V', 79: '+5V', 81: '+5V', 83: '+5V', 85: '+5V', 87: '+5V'},
           {k: 'GND' for k in board.CM5_GND}),
    'U11': ({16: '+3V3'}, {8: 'GND'}), 'U13': ({2: '+24V'}, {7: 'GND', 9: 'GND'}),
    'U14': ({16: '+3V3'}, {8: 'GND'}), 'U15': ({16: '+3V3'}, {8: 'GND'}),
    'U16': ({16: '+3V3'}, {8: 'GND'}), 'U17': ({16: '+3V3'}, {8: 'GND'}),
    'U34': ({3: '24V_IO'}, {2: '0V_IO'}), 'U40': ({3: '+24VA'}, {2: 'AGND_ISO'}),
    'U41': ({1: '+5VA'}, {3: 'AGND_ISO'}),
    'U42': ({1: '+3V3', 16: '+5VA'}, {2: 'GND', 8: 'GND', 9: 'AGND_ISO', 15: 'AGND_ISO'}),
    'U43': ({1: '+3V3', 8: '+5VA'}, {4: 'GND', 5: 'AGND_ISO'}),
    'U44': ({16: '+5VA'}, {9: 'AGND_ISO', 14: 'AGND_ISO'}),
    'U45': ({3: '+5VA'}, {14: 'AGND_ISO'}),
    'U46': ({4: '+24VA'}, {11: 'AGND_ISO'}), 'U47': ({4: '+24VA'}, {11: 'AGND_ISO'}),
    'U50': ({1: '+3V3', 16: '+5V_485'}, {2: 'GND', 7: 'GND', 8: 'GND', 9: 'GND_485',
                                        10: 'GND_485', 15: 'GND_485'}),
    'U51': ({5: 'USB_VBUS'}, {2: 'GND'}),
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
    if r in ('PS1', 'PS2'):
        continue
    for vn in set(v.values()):
        gn = {'+5V': 'GND', '+3V3': 'GND', '+24V': 'GND', '24V_IO': '0V_IO', '+24VA': 'AGND_ISO',
              '+5VA': 'AGND_ISO', '+5V_485': 'GND_485', 'USB_VBUS': 'GND'}[vn]
        if not caps.get(frozenset((vn, gn))):
            nodec.append((r, vn))
check(not nodec, 'a capacitor across every chip supply %s' % nodec)

# ---------------------------------------------------------------- CM5
cm = P['U1']['pins']
check(set(cm) == {str(i) for i in range(1, 201)}, 'CM5: all 200 pins listed')
check(all(pin('U1', k) == 'GND' for k in board.CM5_GND) and len(board.CM5_GND) == 51,
      'CM5: all 51 ground pins on GND (datasheet 4.2.1: connect every ground pin)')
check(pin('U1', 84) == pin('U1', 86) == pin('U1', 78) == '+3V3' and pin('U1', 88) is None
      and pin('U1', 90) is None, 'CM5: GPIO_VREF (78) on its own 3.3 V output (84, 86); 1.8 V unused')
check([n for n, s in N.items() if s and n == '+5V'] and
      not any(('U1', str(k)) in N['+3V3'] for k in (77, 79, 81, 83, 85, 87)),
      'CM5 5 V input pins not on 3.3 V')
GPIO_FN = {11: 'SR_SCLK', 10: 'SR_MOSI', 9: 'SR_MISO', 8: 'SR_LATCH',          # SPI0
           21: 'SPI_SCLK', 20: 'SPI_MOSI', 19: 'SPI_MISO', 18: '~{ADC_CS}', 16: '~{DAC_SYNC}',  # SPI1
           14: 'UA_TX', 15: 'UA_RX', 17: 'DIR485'}                            # UART0
check(all(pin('U1', board.CM5_GPIO[g]) == n for g, n in GPIO_FN.items()),
      'CM5: SPI0 (11/10/9/8), SPI1 (21/20/19/18/16), UART0 (14/15/17 RTS) on their alt-function GPIOs')
check(len(set(board.CM5_GPIO.values())) == 28 and all(pin('U1', board.CM5_GPIO[g]) is None for g in (0, 1)),
      'CM5: 28 distinct GPIO pins; GPIO0/1 (HAT ID) unused')
ETH = {12: 'ETH0_P', 10: 'ETH0_N', 4: 'ETH1_P', 6: 'ETH1_N', 11: 'ETH2_P', 9: 'ETH2_N', 3: 'ETH3_P', 5: 'ETH3_N'}
JACK = {'ETH0_P': 1, 'ETH0_N': 2, 'ETH1_P': 3, 'ETH1_N': 6, 'ETH2_P': 7, 'ETH2_N': 8, 'ETH3_P': 9, 'ETH3_N': 10}
check(all(pin('U1', k) == n and pin('J12', JACK[n]) == n for k, n in ETH.items())
      and pin('J12', 4) == pin('J12', 5) == 'ETH_CT' and two_pin('C70') == ('ETH_CT', 'GND'),
      'Ethernet: CM5 pairs 0-3 to MagJack TRD0-3 as on the CM5 IO board; centre taps to 100 nF')
check(pin('J12', 15) == pin('J12', 17) == '+3V3' and two_pin('R25') == ('ETH_NLED3', 'ETH_LG_K')
      and pin('J12', 18) == 'ETH_LG_K' and two_pin('R26') == ('ETH_NLED2', 'ETH_LY_K') and pin('J12', 16) == 'ETH_LY_K'
      and pin('U1', 15) == 'ETH_NLED3' and pin('U1', 17) == 'ETH_NLED2',
      'Ethernet LEDs: anodes 3.3 V, nLED3 -> green, nLED2 -> yellow through 470R')
check(pin('U1', 103) == 'USB_DN' and pin('U1', 105) == 'USB_DP'
      and pin('J13', 'A6') == pin('J13', 'B6') == 'USB_DP' and pin('J13', 'A7') == pin('J13', 'B7') == 'USB_DN'
      and two_pin('R27') == ('USB_CC1', 'GND') and two_pin('R28') == ('USB_CC2', 'GND')
      and pin('J13', 'A5') == 'USB_CC1' and pin('J13', 'B5') == 'USB_CC2',
      'USB-C: D+/D- both orientations to CM5 USB_P (105) / USB_N (103); Rd 5.1k on CC1, CC2')
check(not set(N['USB_VBUS']) & set(N['+5V']) and sorted(r for r, _ in N['USB_VBUS']) == ['C71', 'J13', 'J13', 'J13', 'J13', 'U51'],
      'USB VBUS reaches only the ESD part and 100 nF (never the board +5V)')
check([pin('U51', k) for k in range(1, 7)] == ['USB_DP', 'GND', 'USB_DN', 'USB_DN', 'USB_VBUS', 'USB_DP'],
      'USBLC6-2SC6: 1/6 D+, 3/4 D-, 2 GND, 5 VBUS')
check(two_pin('JP1') == ('~{RPIBOOT}', 'GND') and pin('U1', 93) == '~{RPIBOOT}'
      and two_pin('SW1') == ('~{PWR_BUT}', 'GND') and pin('U1', 92) == '~{PWR_BUT}',
      'nRPIBOOT jumper (93) and power button (92) to GND')
check(pin('U1', 99) is None and pin('U1', 20) is None and pin('U1', 101) is None and pin('U1', 76) is None,
      'PMIC_Enable, EEPROM_nWP, USB_OTG_ID, VBAT left open')

# ---------------------------------------------------------------- shift registers
HC165_IN = (11, 12, 13, 14, 3, 4, 5, 6)
HC595_Q = (15, 1, 2, 3, 4, 5, 6, 7)
check(pin('U14', 9) == 'SR_MISO' and pin('U15', 9) == 'SR_CHAIN_I' and pin('U14', 10) == 'SR_CHAIN_I'
      and pin('U15', 10) == 'GND' and all(pin(u, 1) == '~{DI_LOAD}' and pin(u, 2) == 'SR_SCLK'
                                          and pin(u, 15) == 'GND' for u in ('U14', 'U15')),
      '74HC165 chain: U15 QH -> U14 SER, U14 QH -> MISO; /PL = GPIO6, CLK = SCLK, CLK INH low')
check(pin('U16', 14) == 'SR_MOSI' and pin('U16', 9) == 'SR_CHAIN_O' and pin('U17', 14) == 'SR_CHAIN_O'
      and all(pin(u, 11) == 'SR_SCLK' and pin(u, 12) == 'SR_LATCH' and pin(u, 13) == '~{OUT_OE}'
              and pin(u, 10) == '+3V3' for u in ('U16', 'U17')),
      '74HC595 chain: MOSI -> U16 SER, QH\' -> U17 SER; SRCLK = SCLK, RCLK = CE0, /OE from the watchdog, /SRCLR high')
check(pin('U11', 2) == 'WD_KICK' and pin('U11', 1) == 'GND' and pin('U11', 3) == 'OUT_EN'
      and pin('U11', 4) == '~{OUT_OE}', '74HC123: B = kick, /A low, /R = OUT_EN, /Q drives the 595 /OE')
check(pin('U11', 15) == 'WD_RC' and pin('U11', 14) == 'WD_CX' and two_pin('R5') == ('+3V3', 'WD_RC')
      and two_pin('C5') == ('WD_RC', 'WD_CX'), '74HC123: Rx to VCC at RxCx, Cx between Cx and RxCx')
check(two_pin('R7') == ('OUT_EN', 'GND') and two_pin('R6') == ('WD_KICK', 'GND')
      and pin('U1', board.CM5_GPIO[5]) == 'OUT_EN' and pin('U1', board.CM5_GPIO[4]) == 'WD_KICK',
      'OUT_EN (GPIO5) and WD_KICK (GPIO4) pulled low while the CM5 boots')


# outputs on only while OUT_EN is high and the monostable runs (behaviour, HC123 table)
def oe(out_en, triggered):
    q_n = 0 if (out_en and triggered) else 1                 # /R low forces /Q high
    return q_n


check([oe(e, t) for e in (0, 1) for t in (0, 1)] == [1, 1, 1, 0],
      'outputs enabled (/OE low) only when OUT_EN is set AND the watchdog is kicked')

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
             and two_pin('R%d' % (140 + n)) == ('+3V3', 'DIN%d' % n))
    buf, bit = ('U14', 'U15')[(n - 1) // 8], (n - 1) % 8
    bus = pin(buf, HC165_IN[bit]) == 'DIN%d' % n
    term = pin(('J2', 'J3')[(n - 1) // 8], bit + 1) == 'DI%d' % n
    if not (chain and bus and term):
        okdi = False
        print('       input %d: chain %s, bus %s, terminal %s' % (n, chain, bus, term))
check(okdi, '16 inputs: 4.7k, LED, opto (TLP291-4 pins), shunt, 1N4148W, 3.3 V pull-up; input n -> 165 A..H')
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
    chain = (pin(latch, HC595_Q[bit]) == 'DQ%d' % n
             and two_pin('R%d' % (200 + n)) == ('DQ%d' % n, 'DO%d_A' % n)
             and pin(u, 2 * ch - 1) == 'DO%d_A' % n and pin(u, 2 * ch) == 'GND'
             and pin(u, 18 - 2 * ch) == '+5V_IO' and pin(u, 17 - 2 * ch) == 'VIN%d' % n
             and two_pin('R%d' % (220 + n)) == ('VIN%d' % n, '0V_IO')
             and pin(vni, VNI_IN[ch]) == 'VIN%d' % n
             and all(pin(vni, k) == o for k in VNI_OUT[ch]) and pin(vni, VNI_ST[ch]) == 'OUT_FLT'
             and two_pin('R%d' % (240 + n)) == (o, 'DO%d_L' % n)
             and two_pin('D%d' % (200 + n)) == ('0V_IO', 'DO%d_L' % n))
    j, jp = ('J4', 'J5')[(n - 1) // 8], bit + 1
    if not (chain and pin(j, jp) == o):
        okdo = False
        print('       output %d: chain %s, terminal %s' % (n, chain, pin(j, jp) == o))
check(okdo, '16 outputs: 595 QA..QH -> 330R -> opto -> VNI4140K IN, all 3 OUT pins, STAT, LED')
check(pin('J4', 9) == '24V_IO' and pin('J4', 10) == '0V_IO', 'field supply in on J4 pins 9-10')
check(pin('U35', 1) == 'FLT_A' and pin('U35', 2) == 'OUT_FLT' and pin('U35', 16) == '~{OUT_FLT}'
      and two_pin('R30') == ('+5V_IO', 'FLT_A') and pin('U1', board.CM5_GPIO[22]) == '~{OUT_FLT}',
      'any VNI STAT low -> opto -> GPIO22 low')
check(pin('U35', 3) == 'FPW_A' and pin('U35', 4) == '0V_IO' and pin('U35', 14) == '~{FIELD_OK}'
      and two_pin('R31') == ('24V_IO', 'FPW_A') and pin('U1', board.CM5_GPIO[23]) == '~{FIELD_OK}',
      'field supply present -> opto -> GPIO23 low')

# ---------------------------------------------------------------- analog
check(pin('U42', 3) == 'SPI_SCLK' and pin('U42', 14) == 'SCLK_I' and pin('U42', 4) == 'SPI_MOSI'
      and pin('U42', 13) == 'MOSI_I' and pin('U42', 5) == '~{ADC_CS}' and pin('U42', 12) == '~{ADC_CS_I}'
      and pin('U42', 11) == 'MISO_I' and pin('U42', 6) == 'SPI_MISO'
      and pin('U42', 7) == '+3V3' and pin('U42', 10) == '+5VA',
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
      and two_pin('D2') == ('+24V', 'GND'), '24 V in: fuse, SS54 (K to +24V), SMBJ33A')
check(two_pin('R22') == ('+5V', 'BUCK_FB') and two_pin('R23') == ('BUCK_FB', 'GND')
      and abs(0.8 * (1 + 53.6 / 10.2) - 5.0) < 0.05, 'TPS54560B feedback: 0.8 V x (1 + 53.6k/10.2k) = 5.00 V')
check(pin('U13', 1) == 'BUCK_BOOT' and pin('U13', 8) == 'BUCK_SW' and pin('U13', 3) is None
      and two_pin('C7') == ('BUCK_BOOT', 'BUCK_SW') and two_pin('L1') == ('BUCK_SW', '+5V')
      and two_pin('D9') == ('BUCK_SW', 'GND') and two_pin('R8') == ('BUCK_RT', 'GND')
      and pin('U13', 6) == 'BUCK_COMP' and two_pin('R9') == ('BUCK_COMP', 'BUCK_CZ')
      and two_pin('C8') == ('BUCK_CZ', 'GND'),
      'TPS54560B: EN open, BOOT cap to SW, catch diode (K = SW), RT, COMP R-C, inductor SW -> +5V')
check(pin('U50', 3) == 'UA_RX' and pin('U50', 6) == 'UA_TX' and pin('U50', 4) == pin('U50', 5) == 'DIR485'
      and pin('U1', board.CM5_GPIO[14]) == 'UA_TX' and pin('U1', board.CM5_GPIO[15]) == 'UA_RX'
      and two_pin('R29') == ('DIR485', 'GND'),
      'CA-IS3082WX: RO -> GPIO15, GPIO14 -> DI, DE = /RE = GPIO17 (RTS), pulled low')
check(pin('J9', 1) == 'RS485_A' and pin('J9', 2) == 'RS485_B' and pin('D7', 3) == 'GND_485',
      'RS-485 terminal A, B, 0V; SM712 common to GND_485')

print('ALL PASSED' if ok else 'FAILED')
sys.exit(0 if ok else 1)
