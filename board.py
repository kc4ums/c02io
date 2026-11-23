"""C02IO: a W65C02S industrial I/O board (16 DI, 16 DO, 8 AI, 8 AO, RS-485).

This file is the design: every part, its footprint, roughly where it sits and
what each pin connects to. check_board.py checks it. Later, mk_pcb.py and
mk_sch.py (as in C02COMM, C:\\Projects\\mymensch\\hardware\\c02board) will
build the KiCad board and schematic from it.

Memory map (the same layout as C02COMM)
    $0000-$7EFF  RAM, AS6C62256 (32 KB, the top 256 bytes are I/O)
    $7F00-$7F0F  VIA   W65C22N   SPI to the analog side, flash bank, output
                                 enable, watchdog, LEDs, fault inputs
    $7F10-$7F1F  UART  TL16C2552 A0-A2 = register, A3 = CHSEL:
                                 $7F10 = channel B (USB header), $7F18 = A (RS-485)
    $7F20        inputs 1-8   (74HC541, read)
    $7F30        inputs 9-16  (74HC541, read)
    $7F40        outputs 1-8  (74HC574, write)
    $7F50        outputs 9-16 (74HC574, write)
    $7F60, $7F70 /CS6, /CS7 on the expansion header
    $8000-$FFFF  flash, SST39SF010A: one of four 32 KB banks (VIA PA6/PA7,
                 pulled low, so bank 0 at reset). JP1 write-protects it.
Clock: one 3.6864 MHz oscillator drives PHI2 and the UART's XTAL1.

Grounds (four isolated areas)
    GND       logic, and the 0 V of the 24 V supply input
    0V_IO     field digital: the 24V_IO supply, inputs and VNI4140K outputs
    AGND_ISO  analog: from the URB2424YMD-6WR3 isolated converter
    GND_485   RS-485 bus side: from the B0505XT-1WR3 isolated converter

Datasheets the pin tables were checked against (2026-11-20):
    TL16C2552        TI SLWS163A (Jun 2006), FN (PLCC-44)
    SST39SF010A      Microchip DS20005022F (May 2025), PLCC-32. Rev F
                     corrected the PLCC pin table: don't use older copies.
    AS6C62256        Alliance Rev 1.2 (Mar 2016), 28-pin 330 mil SOP
    DS1813R-10       Maxim DS1813 REV 022306, SOT-23
    VNI4140K         ST Doc ID 14174 Rev 5 (Aug 2009), PowerSSO-24
    TLP291-4         Toshiba Rev 9.0 (2026-10-29), SO16
    CD74HC123        TI SCHS142F (Oct 2003), SOIC-16
    DAC7568          TI SBAS430F (Apr 2018), TSSOP-16
    REF3040          TI SBVS032K (Dec 2025), SOT-23-3
    ISO7741          TI SLLSEP4K (Aug 2026), SOIC-16 wide
    ISO7720          TI SLLSEP3G (May 2024), SOIC-8
    LM324            TI SLOS066AE (Sep 2025), SOIC-14
    78L05 (SOT-89)   TI SLVS010X, onsemi MC78L00A/D Rev 21, JSCJ CJ78L Rev 3.1:
                     all 1 = OUT, 2 = GND, 3 = IN
    LMR36520         TI SNVSBF0C (Nov 2025), HSOIC-8 (DDA)
    URB2424YMD-6WR3  Mornsun URB_YMD-6WR3 (2026.09.18)
    B0505XT-1WR3     Mornsun B05_XT-1WR3 (2022.01.08)
    CA-IS3082WX      Chipanalog CA-IS308x V1.08 (2023/11/13), SOIC-16 wide
    SM712            Semtech Rev 6.0 (2017)
    BCX56 / BC847 / BAV99   Nexperia Rev 13 (2023) / Rev 12 (2019) / Rev 8 (2010)
    74HC00/32/138/541/574   TI SCLS181H / SCLS200F / SCLS107G / SCLS305E / SCLS148H
    74HC30           TI CD74HC30 SCHS121E (TI has no SN74HC30)
    MCP3208          Microchip, checked in the spec (README)
"""

# ------------------------------------------------------------ footprints
FP = {
    # through-hole: sockets and connectors, soldered by hand
    'DIP40': 'Package_DIP:DIP-40_W15.24mm_Socket',
    'PLCC32S': 'Package_LCC:PLCC-32_THT-Socket',
    'H1x2': 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
    'H1x3': 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
    'H1x6': 'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
    'H2x3': 'Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical',
    'H2x16': 'Connector_PinHeader_2.54mm:PinHeader_2x16_P2.54mm_Vertical',
    'URB': 'c02io:Mornsun_URB_YMD-6WR3_THT',          # project library (to make)
    'HOLE': 'MountingHole:MountingHole_3.2mm_M3',
    'HOLE_PE': 'MountingHole:MountingHole_3.2mm_M3_Pad',
    # SMD, assembled by JLCPCB
    'PLCC44': 'Package_LCC:PLCC-44_16.6x16.6mm_P1.27mm',
    'SOP28': 'Package_SO:SOP-28_8.4x18.16mm_P1.27mm',
    'SO8': 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
    'SO14': 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',
    'SO16': 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm',
    'SO16W': 'Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm',
    'SO20W': 'Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm',
    'SOP16': 'Package_SO:SOP-16_4.4x10.4mm_P1.27mm',        # TLP291-4
    'TSSOP16': 'Package_SO:TSSOP-16_4.4x5mm_P0.65mm',
    'PSSO24': 'Package_SO:ST_PowerSSO-24_SlugDown_ThermalVias',
    'HSOIC8': 'Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm',   # mk_pcb.py adds 0.3 mm thermal vias
    'B05XT': 'c02io:Mornsun_B05_XT-1WR3_SMD',          # project library (to make)
    'SOT23': 'Package_TO_SOT_SMD:SOT-23',
    'SOT89': 'Package_TO_SOT_SMD:SOT-89-3',
    'OSC': 'Oscillator:Oscillator_SMD_EuroQuartz_XO91-4Pin_7.0x5.0mm',
    'R': 'Resistor_SMD:R_0603_1608Metric',
    'R0805': 'Resistor_SMD:R_0805_2012Metric',
    'R1206': 'Resistor_SMD:R_1206_3216Metric',
    'R2010': 'Resistor_SMD:R_2010_5025Metric',
    'C': 'Capacitor_SMD:C_0603_1608Metric',
    'C0805': 'Capacitor_SMD:C_0805_2012Metric',
    'C1206': 'Capacitor_SMD:C_1206_3216Metric',
    'C1210': 'Capacitor_SMD:C_1210_3225Metric',
    'C1808': 'Capacitor_SMD:C_1808_4520Metric',
    'CP10': 'Capacitor_SMD:CP_Elec_10x10.5',
    'L7028': 'Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm',
    'LED': 'LED_SMD:LED_0805_2012Metric',              # pad 1 = K, pad 2 = A
    'SOD123': 'Diode_SMD:D_SOD-123',                    # pad 1 = K, pad 2 = A
    'SMA': 'Diode_SMD:D_SMA',                           # pad 1 = K, pad 2 = A
    'SMB': 'Diode_SMD:D_SMB',                           # pad 1 = K, pad 2 = A
    'F1206': 'Fuse:Fuse_1206_3216Metric',
    'F1812': 'Fuse:Fuse_1812_4532Metric',
    'SW': 'Button_Switch_SMD:SW_SPST_B3S-1000',
}
for _n in (3, 8, 9, 10, 12):
    FP['TB%d' % _n] = ('Connector_Phoenix_MC:PhoenixContact_MC_1,5_%d-G-3.81_1x%02d_P3.81mm_Horizontal'
                       % (_n, _n))

# Pins per footprint, for the "every pin listed" check
NPINS = {'DIP40': 40, 'PLCC32S': 32, 'PLCC44': 44, 'SOP28': 28, 'SO8': 8, 'SO14': 14,
         'SO16': 16, 'SO16W': 16, 'SO20W': 20, 'SOP16': 16, 'TSSOP16': 16, 'PSSO24': 25,
         'HSOIC8': 9, 'SOT23': 3, 'SOT89': 3, 'OSC': 4}

BOARD_W, BOARD_H = 230.0, 147.0

PARTS = []          # dicts: ref, value, fp, x, y, rot, pins {pad: net}, mpn, note, dnp


def part(ref, value, fp, x, y, rot=0, pins=None, mpn='', note='', dnp=False):
    if any(p['ref'] == ref for p in PARTS):
        raise SystemExit('duplicate reference ' + ref)
    PARTS.append(dict(ref=ref, value=value, fp=fp, x=x, y=y, rot=rot,
                      pins={str(k): v for k, v in (pins or {}).items()},
                      mpn=mpn, note=note, dnp=dnp))


def two(ref, value, fp, x, y, a, b, rot=0, **kw):
    """A two-terminal part: pad 1 = a, pad 2 = b."""
    part(ref, value, fp, x, y, rot, pins={1: a, 2: b}, **kw)


def decouple(ref, x, y, vcc='+5V', gnd='GND', value='100nF', fp='C'):
    two(ref, value, fp, x, y, vcc, gnd)


# Positions below are rough (mm from the top-left corner), grouped by area,
# so the parts start out in the right isolation area. Real placement comes
# with mk_pcb.py.
#   y   0-38   field digital (0V_IO): terminals along the top edge
#   y  40-82   logic (GND); power input on the left edge
#   y  84-120  analog (AGND_ISO), x 0-160: terminals along the bottom edge
#   y  84-120  RS-485 (GND_485), x 165-200

# ============================================================ CPU and memory
# W65C02S (DIP-40, socket): the same pins as C02COMM. RDY pulled up (WAI),
# BE (36) and SOB (38) high.
part('U1', 'W65C02S6TPG-14', 'DIP40', 30, 60, pins={
    1: None, 2: 'RDY', 3: None, 4: '~{IRQ}', 5: None, 6: '~{NMI}', 7: None, 8: '+5V',
    9: 'A0', 10: 'A1', 11: 'A2', 12: 'A3', 13: 'A4', 14: 'A5', 15: 'A6', 16: 'A7',
    17: 'A8', 18: 'A9', 19: 'A10', 20: 'A11', 21: 'GND', 22: 'A12', 23: 'A13', 24: 'A14',
    25: 'A15', 26: 'D7', 27: 'D6', 28: 'D5', 29: 'D4', 30: 'D3', 31: 'D2', 32: 'D1',
    33: 'D0', 34: 'RW', 35: None, 36: '+5V', 37: 'PHI2', 38: '+5V', 39: None, 40: '~{RES}'},
    mpn='WDC W65C02S6TPG-14', note='40-pin socket')

# AS6C62256 32K x 8 SRAM, 28-pin 330 mil SOP (same pinout as the PDIP)
part('U2', 'AS6C62256-55SCN', 'SOP28', 50, 60, pins={
    1: 'A14', 2: 'A12', 3: 'A7', 4: 'A6', 5: 'A5', 6: 'A4', 7: 'A3', 8: 'A2', 9: 'A1', 10: 'A0',
    11: 'D0', 12: 'D1', 13: 'D2', 14: 'GND', 15: 'D3', 16: 'D4', 17: 'D5', 18: 'D6', 19: 'D7',
    20: '~{RAMCS}', 21: 'A10', 22: '~{RD}', 23: 'A11', 24: 'A9', 25: 'A8', 26: 'A13',
    27: '~{WR}', 28: '+5V'}, mpn='Alliance AS6C62256-55SCN')

# SST39SF010A 128K x 8 flash, PLCC-32 in a through-hole socket.
# PLCC numbering = PDIP numbering (DS20005022F). FA15/FA16 = bank select.
part('U3', 'SST39SF010A-70-4C-NHE', 'PLCC32S', 66, 60, pins={
    1: None, 2: 'FA16', 3: 'FA15', 4: 'A12', 5: 'A7', 6: 'A6', 7: 'A5', 8: 'A4', 9: 'A3',
    10: 'A2', 11: 'A1', 12: 'A0', 13: 'D0', 14: 'D1', 15: 'D2', 16: 'GND', 17: 'D3', 18: 'D4',
    19: 'D5', 20: 'D6', 21: 'D7', 22: '~{ROMCS}', 23: 'A10', 24: '~{RD}', 25: 'A11', 26: 'A9',
    27: 'A8', 28: 'A13', 29: 'A14', 30: None, 31: '~{FWE}', 32: '+5V'},
    mpn='Microchip SST39SF010A-70-4C-NHE', note='PLCC-32 through-hole socket')

# ============================================================ VIA
# W65C22N (open-drain IRQ, wire-ORed with the UART's interrupt transistors).
# CS1 (24) high, CS2B (23) = /CS0.
#   PA0 SCLK, PA1 MOSI, PA2 MISO, PA3 ADC /CS, PA4 DAC /SYNC, PA5 DAC /LDAC,
#   PA6/PA7 flash bank. PB0 output enable, PB1 watchdog kick, PB2/PB3 RUN/FAULT
#   LEDs, PB4 output fault (low = fault), PB5 field power (low = present),
#   PB6, PB7, CA1, CA2, CB1, CB2 to the expansion header.
part('U4', 'W65C22N6TPG-14', 'DIP40', 84, 60, pins={
    1: 'GND', 2: 'SPI_SCLK', 3: 'SPI_MOSI', 4: 'SPI_MISO', 5: '~{ADC_CS}', 6: '~{DAC_SYNC}',
    7: '~{DAC_LDAC}', 8: 'FA15', 9: 'FA16', 10: 'OUT_EN', 11: 'WD_KICK', 12: 'LED_RUN',
    13: 'LED_FAULT', 14: '~{OUT_FLT}', 15: '~{FIELD_OK}', 16: 'V_PB6', 17: 'V_PB7',
    18: 'V_CB1', 19: 'V_CB2', 20: '+5V', 21: '~{IRQ}', 22: 'RW', 23: '~{CS0}', 24: '+5V',
    25: 'PHI2', 26: 'D7', 27: 'D6', 28: 'D5', 29: 'D4', 30: 'D3', 31: 'D2', 32: 'D1', 33: 'D0',
    34: '~{RES}', 35: 'A3', 36: 'A2', 37: 'A1', 38: 'A0', 39: 'V_CA2', 40: 'V_CA1'},
    mpn='WDC W65C22N6TPG-14 (N = open-drain IRQ)', note='40-pin socket; must be the N version')

# ============================================================ UART
# TL16C2552 dual UART, PLCC-44 (SLWS163A). One /CS for both channels;
# CHSEL = A3 (1 = channel A, 0 = channel B). RESET is active high.
# INTA/INTB are active high and 3-state until MCR OUT2 = 1, so each drives
# /IRQ through an NPN (Q1, Q2) with a pull-down on the INT line.
# MFA/MFB, TXRDY and DTR unused. Channel A modem inputs tied inactive
# (/CTSA active); channel B's /CTS comes from the USB header.
part('U5', 'TL16C2552FN', 'PLCC44', 104, 60, pins={
    1: None, 2: 'D0', 3: 'D1', 4: 'D2', 5: 'D3', 6: 'D4', 7: 'D5', 8: 'D6', 9: 'D7',
    10: 'A0', 11: 'UART_CLK', 12: 'GND', 13: None, 14: 'A1', 15: 'A2', 16: 'A3',
    17: 'UB_INT', 18: '~{CS1}', 19: None, 20: '~{WR}', 21: 'RES', 22: 'GND',
    23: 'SER_RTS', 24: '~{RD}', 25: 'SER_RX', 26: 'SER_TX', 27: None, 28: 'SER_CTS',
    29: '+5V', 30: '+5V', 31: '+5V', 32: None, 33: '+5V', 34: 'UA_INT', 35: None,
    36: '~{UA_RTS}', 37: None, 38: 'UA_TX', 39: 'UA_RX', 40: 'GND', 41: '+5V', 42: '+5V',
    43: '+5V', 44: '+5V'}, mpn='TI TL16C2552FN',
    note='XTAL1 driven by the 3.6864 MHz oscillator; XTAL2 open')
for i, (ch, x) in enumerate((('UA', 116), ('UB', 122))):
    q = 'Q%d' % (i + 1)
    part(q, 'BC847', 'SOT23', x, 52, pins={1: ch + '_INTB', 2: 'GND', 3: '~{IRQ}'},
         mpn='Nexperia BC847 (1 B, 2 E, 3 C)')
    two('R%d' % (1 + i), '10k', 'R', x, 46, ch + '_INT', ch + '_INTB', note='base resistor')
    two('R%d' % (3 + i), '100k', 'R', x, 48, ch + '_INT', 'GND', note='INT is 3-state until OUT2 = 1')

# ============================================================ glue logic
# U6 74HC00: ~ROMCS = /A15, NRW = /RW, ~RD = NAND(PHI2,RW), ~WR = NAND(PHI2,NRW)
part('U6', '74HC00', 'SO14', 30, 76, pins={
    1: 'A15', 2: 'A15', 3: '~{ROMCS}', 4: 'RW', 5: 'RW', 6: 'NRW', 7: 'GND',
    8: '~{RD}', 9: 'PHI2', 10: 'RW', 11: '~{WR}', 12: 'PHI2', 13: 'NRW', 14: '+5V'},
    mpn='TI SN74HC00DR')
# U7 74HC00: ~RAMCS = NAND(~ROMCS, ~IOSEL); ~OUT_OE = NAND(OUT_EN, WDOK);
#            RES = /~RES (UART reset); DIR485 = /~UA_RTS (RS-485 DE and /RE)
part('U7', '74HC00', 'SO14', 40, 76, pins={
    1: '~{ROMCS}', 2: '~{IOSEL}', 3: '~{RAMCS}', 4: 'OUT_EN', 5: 'WDOK', 6: '~{OUT_OE}',
    7: 'GND', 8: 'RES', 9: '~{RES}', 10: '~{RES}', 11: 'DIR485', 12: '~{UA_RTS}',
    13: '~{UA_RTS}', 14: '+5V'}, mpn='TI SN74HC00DR')
# U8 74HC30: ~IOSEL low for $7Fxx (A8-A14 = 1, ~ROMCS = 1 i.e. A15 = 0).
# Pins 9, 10, 13 are not connected inside (CD74HC30).
part('U8', '74HC30', 'SO14', 50, 76, pins={
    1: 'A8', 2: 'A9', 3: 'A10', 4: 'A11', 5: 'A12', 6: 'A13', 7: 'GND', 8: '~{IOSEL}',
    9: None, 10: None, 11: 'A14', 12: '~{ROMCS}', 13: None, 14: '+5V'},
    mpn='TI CD74HC30M96')
# U9 74HC138: 16-byte selects in $7F00-$7F7F (A7 = 0)
part('U9', '74HC138', 'SO16', 60, 76, pins={
    1: 'A4', 2: 'A5', 3: 'A6', 4: '~{IOSEL}', 5: 'A7', 6: '+5V', 7: '~{CS7}', 8: 'GND',
    9: '~{CS6}', 10: '~{CS5}', 11: '~{CS4}', 12: '~{CS3}', 13: '~{CS2}', 14: '~{CS1}',
    15: '~{CS0}', 16: '+5V'}, mpn='TI SN74HC138DR')
# U10 74HC32: output latch clocks = OR(/CSn, /WR): rising edge at the end of the write
part('U10', '74HC32', 'SO14', 70, 76, pins={
    1: '~{CS4}', 2: '~{WR}', 3: 'OCLK1', 4: '~{CS5}', 5: '~{WR}', 6: 'OCLK2', 7: 'GND',
    8: None, 9: 'GND', 10: 'GND', 11: None, 12: 'GND', 13: 'GND', 14: '+5V'},
    mpn='TI SN74HC32DR')

# ============================================================ watchdog
# CD74HC123 half 1: B (rising edge, /A low) retriggers from VIA PB1. /R = /RES,
# so Q (WDOK) is low through reset; PB1 is pulled low so the release of /R
# can't trigger it. tW = 0.45 * Rx * Cx = 0.45 * 100k * 2.2uF = ~100 ms
# (less with the capacitor's DC-bias loss: kick it at least every 25 ms).
# Half 2 unused: /A high, B low, /R low.
part('U11', 'CD74HC123', 'SO16', 80, 76, pins={
    1: 'GND', 2: 'WD_KICK', 3: '~{RES}', 4: None, 5: None, 6: 'GND', 7: 'GND', 8: 'GND',
    9: '+5V', 10: 'GND', 11: 'GND', 12: None, 13: 'WDOK', 14: 'WD_CX', 15: 'WD_RC', 16: '+5V'},
    mpn='TI CD74HC123M96')
two('R5', '100k', 'R', 80, 70, '+5V', 'WD_RC', note='watchdog Rx')
two('C5', '2.2uF', 'C1206', 84, 70, 'WD_RC', 'WD_CX', note='watchdog Cx, X7R 25 V')
two('R6', '10k', 'R', 88, 70, 'WD_KICK', 'GND', note='PB1 low while the VIA is in reset')
two('R7', '10k', 'R', 90, 70, 'OUT_EN', 'GND', note='PB0 low: outputs off until software sets it')

# ============================================================ clock and reset
part('X1', '3.6864MHz', 'OSC', 96, 76, pins={1: '+5V', 2: 'GND', 3: 'CLK_X', 4: '+5V'},
     mpn='5 V HCMOS oscillator, 7 x 5 mm 4-pad', note='pad 1 = OE/EN (tied high), 2 GND, 3 OUT, 4 VDD; check against the part bought')
two('R8', '33', 'R', 100, 72, 'CLK_X', 'PHI2', note='PHI2 series termination, at X1')
two('R9', '33', 'R', 100, 80, 'CLK_X', 'UART_CLK', note='UART clock series termination')

# DS1813R-10: open drain, internal pull-up, 150 ms; SW1 pulls /RES low too
part('U12', 'DS1813R-10', 'SOT23', 110, 76, pins={1: '~{RES}', 2: '+5V', 3: 'GND'},
     mpn='Analog Devices DS1813R-10+T&R (1 RST, 2 VCC, 3 GND)')
two('SW1', 'RESET', 'SW', 116, 78, '~{RES}', 'GND', mpn='Omron B3S-1000',
    note='footprint pads 1 and 2 each appear twice')
two('R10', '3.3k', 'R', 120, 72, '+5V', '~{NMI}')
two('R11', '3.3k', 'R', 120, 74, '+5V', '~{IRQ}')
two('R12', '3.3k', 'R', 120, 76, '+5V', 'RDY')

# Flash: JP1 1-2 = writable, 2-3 = protected; bank 0 at reset
part('JP1', 'FLASH WE', 'H1x3', 126, 72, pins={1: '~{WR}', 2: '~{FWE}', 3: '+5V'},
     note='1-2 write, 2-3 protect')
two('R13', '10k', 'R', 130, 72, 'FA15', 'GND', note='bank 0 at reset')
two('R14', '10k', 'R', 130, 74, 'FA16', 'GND')

# SPI chip selects held inactive while the VIA pins are inputs
two('R15', '10k', 'R', 130, 76, '+5V', '~{ADC_CS}')
two('R16', '10k', 'R', 130, 78, '+5V', '~{DAC_SYNC}')
two('R17', '10k', 'R', 130, 80, '+5V', '~{DAC_LDAC}')

# RUN / FAULT LEDs on PB2 / PB3 (lit when high), power LED
for i, (net, col) in enumerate((('LED_RUN', 'green'), ('LED_FAULT', 'red'))):
    two('D%d' % (3 + i), 'RUN' if i == 0 else 'FAULT', 'LED', 136 + 4 * i, 76,
        'NL%d' % i, net, mpn='0805 LED, ' + col)
    two('R%d' % (18 + i), '1k', 'R', 136 + 4 * i, 80, 'NL%d' % i, 'GND')
two('D5', 'PWR', 'LED', 144, 76, 'NLP', '+5V', mpn='0805 LED, green')
two('R20', '1k', 'R', 144, 80, 'NLP', 'GND')

# ============================================================ USB serial (UART channel B)
# 6-pin FTDI header: GND CTS VCC TXD RXD RTS (module's view)
part('J10', 'USB-SERIAL', 'H1x6', 150, 60, pins={
    1: 'GND', 2: 'SER_RTS', 3: 'USB_5V', 4: 'SER_RX', 5: 'SER_TX', 6: 'SER_CTS'},
    note='GND CTS VCC TXD RXD RTS, 5 V TTL module')
two('R21', '10k', 'R', 154, 66, 'SER_CTS', 'GND', note='/CTS active without a module')
two('JP2', 'USB PWR', 'H1x2', 154, 70, 'USB_5V', '+5V',
    note='bench use only: fit only when nothing is on the 24 V input')

# ============================================================ expansion header
EXP = {1: '+5V', 2: 'GND', 3: 'D0', 4: 'D1', 5: 'D2', 6: 'D3', 7: 'D4', 8: 'D5', 9: 'D6',
       10: 'D7', 11: 'A0', 12: 'A1', 13: 'A2', 14: 'A3', 15: 'RW', 16: 'PHI2', 17: '~{RD}',
       18: '~{WR}', 19: '~{IRQ}', 20: '~{RES}', 21: '~{CS6}', 22: '~{CS7}', 23: 'V_PB6',
       24: 'V_PB7', 25: 'V_CA1', 26: 'V_CA2', 27: 'V_CB1', 28: 'V_CB2', 29: '~{NMI}',
       30: 'GND', 31: '+5V', 32: 'GND'}
part('J11', 'EXPANSION', 'H2x16', 170, 60, rot=90, pins=EXP,
     note='+5V GND D0-D7 A0-A3 RW PHI2 /RD /WR /IRQ /RES /CS6 /CS7 PB6 PB7 CA1 CA2 CB1 CB2 /NMI')

# ============================================================ power input
# 24 V (18-32 V) -> 2 A fuse -> SS34 -> SMBJ33A -> +24V (logic-side raw supply)
part('J1', '24V IN', 'TB3', 4, 50, rot=270, pins={1: '24V_RAW', 2: 'GND', 3: 'PE'},
     note='1 = +24 V, 2 = 0 V, 3 = PE')
two('F1', '2A', 'F1206', 10, 46, '24V_RAW', '24V_F', note='fast fuse')
two('D1', 'SS34', 'SMA', 10, 50, '+24V', '24V_F', note='reverse polarity (K = +24V)')
two('D2', 'SMBJ33A', 'SMB', 10, 54, '+24V', 'GND', note='TVS')
two('C1', '100uF 50V', 'CP10', 16, 46, '+24V', 'GND')
two('C2', '1nF 2kV', 'C1808', 4, 60, 'PE', 'GND', note='PE to logic 0 V')

# LMR36520ADDAR (SNVSBF0C Design 1: 24 V -> 5 V / 2 A, 400 kHz). Adjustable
# only: FB = 1 V from 100k / 24.9k. EN to VIN. PG unused. Pad 9 = thermal, GND.
part('U13', 'LMR36520ADDAR', 'HSOIC8', 16, 56, pins={
    1: 'GND', 2: '+24V', 3: '+24V', 4: None, 5: 'BUCK_FB', 6: 'BUCK_VCC', 7: 'BUCK_BOOT',
    8: 'BUCK_SW', 9: 'GND'}, mpn='TI LMR36520ADDAR')
two('C3', '4.7uF 50V', 'C1210', 20, 52, '+24V', 'GND', note='X7R, at VIN')
two('C4', '4.7uF 50V', 'C1210', 24, 52, '+24V', 'GND', note='X7R')
two('C6', '220nF 100V', 'C0805', 20, 50, '+24V', 'GND', note='closest to VIN/PGND')
two('C7', '100nF', 'C', 22, 58, 'BUCK_BOOT', 'BUCK_SW', note='BOOT, 16 V+')
two('C8', '1uF', 'C', 22, 60, 'BUCK_VCC', 'GND', note='VCC LDO, 16 V')
two('L1', '10uH', 'L7028', 22, 64, 'BUCK_SW', '+5V', mpn='Bourns SRP7028A-100M',
    note='Isat above the LMR36520 current limit')
two('R22', '100k', 'R', 26, 58, '+5V', 'BUCK_FB', note='RFBT, 1 %')
two('R23', '24.9k', 'R', 26, 60, 'BUCK_FB', 'GND', note='RFBB, 1 %')
two('C9', '22uF 16V', 'C1210', 28, 64, '+5V', 'GND', note='X7R')
two('C10', '22uF 16V', 'C1210', 28, 68, '+5V', 'GND', note='X7R')

# Logic decoupling, one 100 nF per chip (U1-U12, X1)
for _i, (_x, _y) in enumerate(((36, 50), (54, 50), (70, 50), (90, 50), (110, 50), (34, 82),
                               (44, 82), (54, 82), (64, 82), (74, 82), (84, 82), (96, 82))):
    decouple('C%d' % (11 + _i), _x, _y)            # C11-C22
decouple('C23', 110, 82, value='10uF', fp='C0805')

# ============================================================ digital inputs (x16)
# Field side, per input: terminal -> 4.7k (1206) -> green LED -> opto LED -> 0V_IO,
# with 2.2k and 10 nF across the opto LED and a 1N4148W from 0V_IO to the
# 4.7k's far end (reverse voltage). About 1.7 mA at 11 V; 5 V stays off.
# Logic side: opto collector pulled up by 22k, read by the 74HC541 (low = on).
# TLP291-4 (Rev 9.0): ch k: anode 2k-1, cathode 2k, collector 18-2k, emitter 17-2k.
def opto4(ref, x, y, chans, mpn='Toshiba TLP291-4(GB)'):
    """chans: 4 tuples (anode, cathode, collector, emitter) for channels 1-4."""
    pins = {}
    for k, (a, c, col, e) in enumerate(chans, start=1):
        pins.update({2 * k - 1: a, 2 * k: c, 18 - 2 * k: col, 17 - 2 * k: e})
    part(ref, 'TLP291-4', 'SOP16', x, y, pins=pins, mpn=mpn)


DI = ['DI%d' % n for n in range(1, 17)]
for n in range(1, 17):
    x = 6 + 5.5 * (n - 1)
    p = 'DI%d_' % n
    two('R%d' % (100 + n), '4.7k', 'R1206', x, 14, DI[n - 1], p + 'A', note='input current')
    two('D%d' % (120 + n), '1N4148W', 'SOD123', x, 18, p + 'A', '0V_IO', note='reverse voltage')
    two('D%d' % (100 + n), 'IN', 'LED', x, 22, p + 'K', p + 'A', mpn='0805 LED, green')
    two('R%d' % (120 + n), '2.2k', 'R', x, 26, p + 'K', '0V_IO', note='threshold shunt')
    two('C%d' % (100 + n), '10nF', 'C', x, 29, p + 'K', '0V_IO', note='filter')
    two('R%d' % (140 + n), '22k', 'R', x, 46, '+5V', 'DIN%d' % n, note='pull-up')
for k in range(4):                                    # U20-U23: inputs 4k+1 .. 4k+4
    opto4('U%d' % (20 + k), 14 + 22 * k, 38,
          [('DI%d_K' % (4 * k + j), '0V_IO', 'DIN%d' % (4 * k + j), 'GND') for j in range(1, 5)])

# 74HC541 x2: /OE1 = chip select, /OE2 = /RD. Input 1 -> D0.
for i, (ref, cs) in enumerate((('U14', '~{CS2}'), ('U15', '~{CS3}'))):
    pins = {1: cs, 10: 'GND', 19: '~{RD}', 20: '+5V'}
    for b in range(8):
        pins[2 + b] = 'DIN%d' % (8 * i + b + 1)        # A1-A8 on pins 2-9
        pins[18 - b] = 'D%d' % b                       # Y1-Y8 on pins 18-11
    part(ref, '74HC541', 'SO20W', 20 + 40 * i, 50, pins=pins, mpn='TI SN74HC541DWR')
    decouple('C%d' % (24 + i), 28 + 40 * i, 50)

# ============================================================ digital outputs (x16)
# 74HC574 -> 1k -> opto LED -> GND. Opto transistor: +5V_IO -> VNI4140K IN,
# 10k pull-down. /OE = ~OUT_OE (high = latches off = outputs off) until
# software sets PB0 and the watchdog is running.
for i, (ref, clk) in enumerate((('U16', 'OCLK1'), ('U17', 'OCLK2'))):
    pins = {1: '~{OUT_OE}', 10: 'GND', 11: clk, 20: '+5V'}
    for b in range(8):
        pins[2 + b] = 'D%d' % b                        # 1D-8D on pins 2-9
        pins[19 - b] = 'DQ%d' % (8 * i + b + 1)        # 1Q-8Q on pins 19-12
    part(ref, '74HC574', 'SO20W', 110 + 40 * i, 50, pins=pins, mpn='TI SN74HC574DWR')
    decouple('C%d' % (26 + i), 118 + 40 * i, 50)

for n in range(1, 17):
    x = 104 + 5.5 * (n - 1)
    two('R%d' % (200 + n), '1k', 'R', x, 44, 'DQ%d' % n, 'DO%d_A' % n, note='opto LED, ~3.8 mA')
    two('R%d' % (220 + n), '10k', 'R', x, 30, 'VIN%d' % n, '0V_IO', note='VNI input pull-down')
    two('R%d' % (240 + n), '4.7k', 'R1206', x, 22, 'OUT%d' % n, 'DO%d_L' % n, note='output LED')
    two('D%d' % (200 + n), 'OUT', 'LED', x, 18, '0V_IO', 'DO%d_L' % n, mpn='0805 LED, yellow')
    two('C%d' % (200 + n), '10nF 50V', 'C', x, 14, 'OUT%d' % n, '0V_IO',
        note='per VNI4140K application circuit')
for k in range(4):                                    # U24-U27: outputs 4k+1 .. 4k+4
    opto4('U%d' % (24 + k), 112 + 22 * k, 38,
          [('DO%d_A' % (4 * k + j), 'GND', '+5V_IO', 'VIN%d' % (4 * k + j)) for j in range(1, 5)])

# VNI4140K x4 (Doc 14174 Rev 5). Slug (pad 25) is Vcc. STATn: open drain,
# active low, one per channel (low only on over-temperature with IN high):
# all 16 wire-ORed onto OUT_FLT.
for k in range(4):
    ref = 'U%d' % (30 + k)
    c = [4 * k + j for j in range(1, 5)]
    part(ref, 'VNI4140K', 'PSSO24', 112 + 22 * k, 8, pins={
        1: '24V_IO', 2: 'VIN%d' % c[0], 3: 'OUT_FLT', 4: 'VIN%d' % c[1], 5: 'OUT_FLT',
        6: '0V_IO', 7: 'OUT_FLT', 8: 'VIN%d' % c[2], 9: 'OUT_FLT', 10: 'VIN%d' % c[3],
        11: None, 12: None, 13: 'OUT%d' % c[3], 14: 'OUT%d' % c[3], 15: 'OUT%d' % c[3],
        16: 'OUT%d' % c[2], 17: 'OUT%d' % c[2], 18: 'OUT%d' % c[2], 19: 'OUT%d' % c[1],
        20: 'OUT%d' % c[1], 21: 'OUT%d' % c[1], 22: 'OUT%d' % c[0], 23: 'OUT%d' % c[0],
        24: 'OUT%d' % c[0], 25: '24V_IO'}, mpn='ST VNI4140KTR',
        note='slug = Vcc: copper pour on 24V_IO, not 0V_IO')
    decouple('C%d' % (30 + k), 118 + 22 * k, 2, vcc='24V_IO', gnd='0V_IO', value='100nF 50V')

# ============================================================ field supply and status
# 24V_IO comes in on J4 pins 9-10. It feeds the VNI4140Ks directly (up to 8 A in all:
# fuse it outside the board). A reversed field supply is shorted by D6: the
# external fuse must blow. The sensor-supply terminals are fed through a PTC.
two('D6', 'SMBJ33A', 'SMB', 100, 4, '24V_IO', '0V_IO', note='field supply TVS')
two('C34', '47uF 50V', 'CP10', 100, 10, '24V_IO', '0V_IO')
two('F2', '0.5A PTC', 'F1812', 96, 14, '24V_IO', '24V_SNS', note='sensor supply, 30 V+ rated')
part('U34', '78L05', 'SOT89', 96, 20, pins={1: '+5V_IO', 2: '0V_IO', 3: '24V_IO'},
     mpn='78L05 SOT-89 (1 OUT, 2 GND, 3 IN), 30 V input')
two('C35', '100nF 50V', 'C', 92, 20, '24V_IO', '0V_IO')
two('C36', '1uF', 'C', 92, 22, '+5V_IO', '0V_IO')

# U35 TLP291-4: ch1 = output fault, ch2 = field power present, ch3-4 spare.
# Fault: +5V_IO -> 2.2k -> opto LED -> OUT_FLT (pulled low by any STATn).
# Field power: 24V_IO -> 10k -> opto LED -> 0V_IO.
opto4('U35', 96, 32, [('FLT_A', 'OUT_FLT', '~{OUT_FLT}', 'GND'),
                      ('FPW_A', '0V_IO', '~{FIELD_OK}', 'GND'),
                      ('0V_IO', '0V_IO', None, 'GND'),
                      ('0V_IO', '0V_IO', None, 'GND')])
two('R30', '2.2k', 'R', 92, 28, '+5V_IO', 'FLT_A', note='~1.5 mA; STAT is specified at 1.6 mA')
two('R31', '10k', 'R1206', 92, 30, '24V_IO', 'FPW_A', note='~2.2 mA at 24 V')
two('R32', '22k', 'R', 100, 44, '+5V', '~{OUT_FLT}', note='PB4 pull-up')
two('R33', '22k', 'R', 102, 44, '+5V', '~{FIELD_OK}', note='PB5 pull-up')

# Field terminals (3.81 mm pluggable, top edge)
part('J2', 'DI 1-8', 'TB10', 10, 3, pins={**{i + 1: DI[i] for i in range(8)}, 9: '24V_SNS', 10: '0V_IO'}, note='IN1-IN8, 24V (sensor supply), 0V')
part('J3', 'DI 9-16', 'TB10', 50, 3, pins={**{i + 1: DI[8 + i] for i in range(8)}, 9: '24V_SNS', 10: '0V_IO'}, note='IN9-IN16, 24V (sensor supply), 0V')
part('J4', 'DO 1-8', 'TB10', 120, 3, pins={**{i + 1: 'OUT%d' % (i + 1) for i in range(8)}, 9: '24V_IO', 10: '0V_IO'},
     note='OUT1-OUT8, 24V_IO in, 0V_IO in')
part('J5', 'DO 9-16', 'TB10', 160, 3, pins={**{i + 1: 'OUT%d' % (9 + i) for i in range(8)}, 9: '0V_IO', 10: '0V_IO'}, note='OUT9-OUT16, 0V, 0V (load return)')

# ============================================================ analog isolation
# URB2424YMD-6WR3 (through-hole, 25.4 mm square): 1 GND, 2 Vin, 3 +Vo,
# 4 absent, 5 0V. 1500 VDC isolation, no minimum load.
part('PS1', 'URB2424YMD-6WR3', 'URB', 14, 96, pins={1: 'GND', 2: '+24V', 3: '+24VA', 5: 'AGND_ISO'},
     mpn='Mornsun URB2424YMD-6WR3', note='Cin 100 uF (C1), Cout 10 uF')
two('C40', '10uF 50V', 'C1210', 30, 90, '+24VA', 'AGND_ISO', note='URB output, X7R')
two('C41', '4.7uF 50V', 'C1210', 4, 90, '+24V', 'GND', note='URB input, at the module')
part('U40', '78L05', 'SOT89', 30, 96, pins={1: '+5VA', 2: 'AGND_ISO', 3: '+24VA'},
     mpn='78L05 SOT-89 (1 OUT, 2 GND, 3 IN), 30 V input')
two('C42', '330nF 50V', 'C', 34, 96, '+24VA', 'AGND_ISO')
two('C43', '10uF', 'C0805', 34, 100, '+5VA', 'AGND_ISO')
# REF3040: 1 IN, 2 OUT, 3 GND. 4.096 V for the MCP3208.
part('U41', 'REF3040', 'SOT23', 40, 100, pins={1: '+5VA', 2: 'VREF_ADC', 3: 'AGND_ISO'},
     mpn='TI REF3040AIDBZR')
two('C44', '100nF', 'C', 40, 96, '+5VA', 'AGND_ISO')
two('C45', '1uF', 'C', 44, 100, 'VREF_ADC', 'AGND_ISO', note='ADC reference bypass')

# SPI across the barrier. ISO7741 (default-high, no F suffix): A/B/C forward
# = SCLK, MOSI, ADC /CS; D back = MISO. EN1/EN2 tied high.
part('U42', 'ISO7741DWR', 'SO16W', 50, 84, pins={
    1: '+5V', 2: 'GND', 3: 'SPI_SCLK', 4: 'SPI_MOSI', 5: '~{ADC_CS}', 6: 'SPI_MISO', 7: '+5V',
    8: 'GND', 9: 'AGND_ISO', 10: '+5VA', 11: 'MISO_I', 12: '~{ADC_CS_I}', 13: 'MOSI_I',
    14: 'SCLK_I', 15: 'AGND_ISO', 16: '+5VA'}, mpn='TI ISO7741DWR (default high)')
# ISO7720 (default-high): DAC /SYNC and /LDAC
part('U43', 'ISO7720DR', 'SO8', 64, 84, pins={
    1: '+5V', 2: '~{DAC_SYNC}', 3: '~{DAC_LDAC}', 4: 'GND', 5: 'AGND_ISO', 6: '~{DAC_LDAC_I}',
    7: '~{DAC_SYNC_I}', 8: '+5VA'}, mpn='TI ISO7720DR (default high)')
for _r, _x, _y, _v, _g in (('C46', 46, 80, '+5V', 'GND'), ('C47', 46, 90, '+5VA', 'AGND_ISO'),
                           ('C48', 60, 80, '+5V', 'GND'), ('C49', 60, 90, '+5VA', 'AGND_ISO')):
    decouple(_r, _x, _y, _v, _g)

# ============================================================ analog inputs (x8)
# MCP3208 (SOIC-16): CH0-7 on 1-8, DGND 9, /CS 10, DIN 11, DOUT 12, CLK 13,
# AGND 14, VREF 15, VDD 16.
part('U44', 'MCP3208', 'SO16', 70, 100, pins={
    **{i + 1: 'ADC%d' % (i + 1) for i in range(8)},
    9: 'AGND_ISO', 10: '~{ADC_CS_I}', 11: 'MOSI_I', 12: 'MISO_I', 13: 'SCLK_I',
       14: 'AGND_ISO', 15: 'VREF_ADC', 16: '+5VA'}, mpn='Microchip MCP3208-CI/SL')
decouple('C50', 74, 94, '+5VA', 'AGND_ISO')

# Per input: terminal -> PTC -> SMAJ12A to AGND -> 15k/10k (10 V -> 4.0 V)
# -> 1k -> ADC, 100 nF and BAV99 clamps (1 AGND, 2 +5VA, 3 node).
# JP3nn fitted = 499 R burden (4-20 mA: 20 mA reads ~9.8 V).
for n in range(1, 9):
    x = 80 + 6 * (n - 1)
    p = 'AI%d' % n
    two('F%d' % (300 + n), '50mA PTC', 'F1812', x, 116, p, p + '_P')
    two('D%d' % (300 + n), 'SMAJ12A', 'SMA', x, 112, p + '_P', 'AGND_ISO')
    two('JP%d' % (300 + n), 'mA', 'H1x2', x, 108, p + '_P', p + '_M', note='fit for 4-20 mA')
    two('R%d' % (330 + n), '499', 'R2010', x, 104, p + '_M', 'AGND_ISO', note='0.1 %, 0.5 W')
    two('R%d' % (300 + n), '15k', 'R', x, 100, p + '_P', p + '_D', note='0.1 %')
    two('R%d' % (310 + n), '10k', 'R', x, 98, p + '_D', 'AGND_ISO', note='0.1 %')
    two('R%d' % (320 + n), '1k', 'R', x, 96, p + '_D', 'ADC%d' % n)
    two('C%d' % (300 + n), '100nF', 'C', x, 94, 'ADC%d' % n, 'AGND_ISO')
    part('D%d' % (310 + n), 'BAV99', 'SOT23', x, 90, pins={1: 'AGND_ISO', 2: '+5VA', 3: 'ADC%d' % n},
         mpn='Nexperia BAV99 (3 = common)')

# ============================================================ analog outputs (x8)
# DAC7568IAPW: A grade = gain 1, 0-2.5 V from the internal 2.5 V reference
# (off at power-up: firmware enables it). The C grade (0-5 V) needs AVDD
# >= 5.0 V, which a 78L05 doesn't guarantee. /CLR held high (10k).
# Outputs A-H = channels 1-8: A 4, B 13, C 5, D 12, E 6, F 11, G 7, H 10.
part('U45', 'DAC7568IAPW', 'TSSOP16', 70, 90, pins={
    1: '~{DAC_LDAC_I}', 2: '~{DAC_SYNC_I}', 3: '+5VA', 4: 'AO1_DAC', 5: 'AO3_DAC',
    6: 'AO5_DAC', 7: 'AO7_DAC', 8: 'DAC_VREF', 9: 'DAC_CLR', 10: 'AO8_DAC', 11: 'AO6_DAC',
    12: 'AO4_DAC', 13: 'AO2_DAC', 14: 'AGND_ISO', 15: 'MOSI_I', 16: 'SCLK_I'},
    mpn='TI DAC7568IAPWR (A grade)')
decouple('C51', 74, 86, '+5VA', 'AGND_ISO')
two('C52', '100nF', 'C', 66, 94, 'DAC_VREF', 'AGND_ISO', note='internal reference, >= 100 nF')
two('R34', '10k', 'R', 66, 96, '+5VA', 'DAC_CLR')

# LM324 x2 on +24VA. Amp k: (out, in-, in+) = 1:(1,2,3) 2:(7,6,5) 3:(8,9,10) 4:(14,13,12)
AMP = {1: (1, 2, 3), 2: (7, 6, 5), 3: (8, 9, 10), 4: (14, 13, 12)}
for i, ref in enumerate(('U46', 'U47')):
    pins = {4: '+24VA', 11: 'AGND_ISO'}
    for k in range(1, 5):
        ch = 4 * i + k
        o, m, pl = AMP[k]
        pins.update({o: 'AO%d_OA' % ch, m: 'AO%d_INV' % ch, pl: 'AO%d_DAC' % ch})
    part(ref, 'LM324', 'SO14', 100 + 30 * i, 86, pins=pins, mpn='TI LM324DR')
    decouple('C%d' % (53 + i), 104 + 30 * i, 86, '+24VA', 'AGND_ISO', value='100nF 50V')

# Per output: LM324 -> 1k -> BCX56 follower from +24VA -> 22R -> PTC -> OUT.
# BC847 across the 22R limits the current to ~27 mA.
# JP4nn 2x3 (rows 1-3-5 / 2-4-6):
#   both shunts 1-3, 2-4 ("left")  = 0-10 V: feedback from 30k/10k on OUT (gain 4), COM = AGND
#   both shunts 3-5, 4-6 ("right") = 4-20 mA: feedback from COM, which returns
#                                    through 124R 0.1 % (2.5 V = 20.2 mA)
# 10k + 10 nF around the op-amp (compensation): values to confirm in simulation.
for n in range(1, 9):
    x = 96 + 7 * (n - 1)
    p = 'AO%d_' % n
    two('R%d' % (400 + n), '1k', 'R', x, 92, p + 'OA', p + 'B', note='base resistor')
    part('Q%d' % (400 + n), 'BCX56', 'SOT89', x, 96, pins={1: p + 'E', 2: '+24VA', 3: p + 'B'},
         mpn='Nexperia BCX56 (1 E, 2 C + tab, 3 B)')
    two('R%d' % (410 + n), '22', 'R', x, 100, p + 'E', p + 'X', note='current limit sense')
    part('Q%d' % (410 + n), 'BC847', 'SOT23', x + 3, 100, pins={1: p + 'E', 2: p + 'X', 3: p + 'B'},
         mpn='Nexperia BC847 (1 B, 2 E, 3 C)')
    two('F%d' % (400 + n), '50mA PTC', 'F1812', x, 104, p + 'X', 'AO%d' % n)
    two('D%d' % (400 + n), 'SMAJ15A', 'SMA', x, 108, 'AO%d' % n, 'AGND_ISO')
    two('C%d' % (410 + n), '10nF 50V', 'C', x + 3, 108, 'AO%d' % n, 'AGND_ISO')
    two('R%d' % (420 + n), '30k', 'R', x, 110, 'AO%d' % n, p + 'FV', note='0.1 %')
    two('R%d' % (430 + n), '10k', 'R', x, 112, p + 'FV', 'AGND_ISO', note='0.1 %')
    two('R%d' % (440 + n), '124', 'R0805', x + 3, 112, p + 'IS', 'AGND_ISO', note='0.1 %, 25 ppm')
    part('JP%d' % (400 + n), 'V / mA', 'H2x3', x, 116, pins={
        1: p + 'FV', 2: 'AGND_ISO', 3: p + 'FB', 4: 'AOC%d' % n, 5: p + 'IS', 6: p + 'IS'},
        note='1-3 + 2-4 = 0-10 V; 3-5 + 4-6 = 4-20 mA')
    two('R%d' % (450 + n), '10k', 'R', x + 3, 92, p + 'FB', p + 'INV')
    two('C%d' % (400 + n), '10nF', 'C', x + 3, 94, p + 'OA', p + 'INV', note='compensation')

# Analog terminals (bottom edge)
part('J6', 'AI 1-8', 'TB12', 84, 117, pins={
    1: 'AI1', 2: 'AI2', 3: 'AGND_ISO', 4: 'AI3', 5: 'AI4', 6: 'AGND_ISO', 7: 'AI5', 8: 'AI6',
    9: 'AGND_ISO', 10: 'AI7', 11: 'AI8', 12: 'AGND_ISO'}, note='AI1 AI2 0V AI3 AI4 0V ...')
part('J7', 'AO 1-4', 'TB8', 110, 117, pins={
    1: 'AO1', 2: 'AOC1', 3: 'AO2', 4: 'AOC2', 5: 'AO3', 6: 'AOC3', 7: 'AO4', 8: 'AOC4'},
    note='OUT1 COM1 ... OUT4 COM4')
part('J8', 'AO 5-8', 'TB9', 140, 117, pins={
    1: 'AO5', 2: 'AOC5', 3: 'AO6', 4: 'AOC6', 5: 'AO7', 6: 'AOC7', 7: 'AO8', 8: 'AOC8',
    9: 'AGND_ISO'}, note='OUT5 COM5 ... OUT8 COM8, 0V')

# ============================================================ RS-485 (UART channel A)
# B0505XT-1WR3 (SMD): 1 GND, 2 Vin, 4 0V, 5 +Vo, 8 NC (isolated). 20 mA
# minimum load: R50 (330R, 15 mA) plus the bias network and transceiver.
part('PS2', 'B0505XT-1WR3', 'B05XT', 176, 92, pins={1: 'GND', 2: '+5V', 4: 'GND_485', 5: '+5V_485', 8: None},
     mpn='Mornsun B0505XT-1WR3')
two('C60', '4.7uF', 'C0805', 172, 88, '+5V', 'GND', note='B0505 input')
two('C61', '10uF', 'C0805', 182, 88, '+5V_485', 'GND_485', note='B0505 output')
two('R50', '330', 'R1206', 186, 92, '+5V_485', 'GND_485', note='minimum load')
# CA-IS3082WX: 1 VDDA, 2/7/8 GNDA, 3 RO, 4 /RE, 5 DE, 6 DI, 9/10/15 GNDB,
# 12 A, 13 B, 11/14 NC, 16 VDDB. DE = /RE = DIR485 (high = transmit).
part('U50', 'CA-IS3082WX', 'SO16W', 176, 102, pins={
    1: '+5V', 2: 'GND', 3: 'UA_RX', 4: 'DIR485', 5: 'DIR485', 6: 'UA_TX', 7: 'GND', 8: 'GND',
    9: 'GND_485', 10: 'GND_485', 11: None, 12: 'RS485_A', 13: 'RS485_B', 14: None,
    15: 'GND_485', 16: '+5V_485'}, mpn='Chipanalog CA-IS3082WX')
decouple('C62', 170, 98)
decouple('C63', 182, 98, '+5V_485', 'GND_485')
two('C64', '1uF', 'C', 184, 100, '+5V_485', 'GND_485', note='VDDB 0.1 + 1 uF')
two('R51', '10k', 'R', 166, 96, '+5V', 'UA_RX', note='RO is off while transmitting')
two('R52', '680', 'R', 186, 104, '+5V_485', 'RS485_A', note='bias')
two('R53', '680', 'R', 186, 108, 'RS485_B', 'GND_485', note='bias')
two('R54', '120', 'R1206', 190, 106, 'RS485_A', 'RT_B', note='termination')
two('JP3', 'TERM', 'H1x2', 194, 106, 'RT_B', 'RS485_B', note='fit at the ends of the bus')
part('D7', 'SM712', 'SOT23', 186, 112, pins={1: 'RS485_A', 2: 'RS485_B', 3: 'GND_485'},
     mpn='Semtech SM712')
part('J9', 'RS-485', 'TB3', 190, 117, pins={1: 'RS485_A', 2: 'RS485_B', 3: 'GND_485'},
     note='A, B, 0V')

# ============================================================ mounting holes
# H1 is plated and on PE (DIN-rail clip / chassis); the rest are bare.
part('H1', 'M3 PE', 'HOLE_PE', 4, 116, pins={1: 'PE'})
for _i, (_x, _y) in enumerate(((BOARD_W - 4, 40), (4, 40), (BOARD_W - 4, 80))):
    part('H%d' % (_i + 2), 'M3', 'HOLE', _x, _y)


# ============================================================ nets
def nets():
    """net -> [(ref, pad)]"""
    out = {}
    for p in PARTS:
        for pad, net in p['pins'].items():
            if net:
                out.setdefault(net, []).append((p['ref'], pad))
    return out


# Each isolated area: its power and ground nets
AREAS = {
    'logic': {'GND', '+5V', '+24V', '24V_RAW', '24V_F', 'USB_5V'},
    'field': {'0V_IO', '24V_IO', '+5V_IO', '24V_SNS'},
    'analog': {'AGND_ISO', '+24VA', '+5VA', 'VREF_ADC'},
    'rs485': {'GND_485', '+5V_485'},
}
POWER_NETS = set().union(*AREAS.values()) | {'PE'}

# Parts allowed to join two areas, and the areas they join
BRIDGES = {'U20': ('field', 'logic'), 'U21': ('field', 'logic'), 'U22': ('field', 'logic'),
           'U23': ('field', 'logic'), 'U24': ('logic', 'field'), 'U25': ('logic', 'field'),
           'U26': ('logic', 'field'), 'U27': ('logic', 'field'), 'U35': ('field', 'logic'),
           'U42': ('logic', 'analog'), 'U43': ('logic', 'analog'), 'PS1': ('logic', 'analog'),
           'PS2': ('logic', 'rs485'), 'U50': ('logic', 'rs485'), 'C2': ('logic', 'PE')}


def net_areas():
    """net -> area name, found by following every part except the bridges and
    the connectors (whose pins aren't joined inside). None if a net reaches no
    power net, or several areas' power nets."""
    area_of = {n: a for a, ns in AREAS.items() for n in ns}
    area_of['PE'] = 'PE'
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in PARTS:
        r = p['ref']
        if r in BRIDGES or (r[0] == 'J' and r[1].isdigit()):
            continue
        ns = [n for n in p['pins'].values() if n]
        for n in ns[1:]:
            parent[find(ns[0])] = find(n)
    groups = {}
    for n in nets():
        groups.setdefault(find(n), set()).add(n)
    out = {}
    for g in groups.values():
        areas = {area_of[n] for n in g if n in area_of}
        a = next(iter(areas)) if len(areas) == 1 else None
        for n in g:
            out[n] = a
    return out


# ============================================================ placement
# Courtyard of each footprint at rotation 0, relative to its origin
# (xmin, ymin, xmax, ymax). Written by fpgeom.py; check_place.py checks it.
CRT = {
    'B05XT': (-7.1, -6.6, 7.1, 6.6), 'C': (-1.48, -0.73, 1.48, 0.73),
    'C0805': (-1.7, -0.98, 1.7, 0.98), 'C1206': (-2.3, -1.15, 2.3, 1.15),
    'C1210': (-2.3, -1.6, 2.3, 1.6), 'C1808': (-3.1, -1.4, 3.1, 1.4),
    'CP10': (-6.65, -5.5, 6.65, 5.5), 'DIP40': (-1.53, -1.59, 16.77, 49.84),
    'F1206': (-2.28, -1.13, 2.28, 1.13), 'F1812': (-2.95, -1.95, 2.95, 1.95),
    'H1x2': (-1.77, -1.77, 1.77, 4.32), 'H1x3': (-1.77, -1.77, 1.77, 6.85),
    'H1x6': (-1.77, -1.77, 1.77, 14.47), 'H2x16': (-1.77, -1.78, 4.32, 39.88),
    'H2x3': (-1.77, -1.77, 4.32, 6.85), 'HOLE': (-3.45, -3.45, 3.45, 3.45),
    'HOLE_PE': (-3.45, -3.45, 3.45, 3.45), 'HSOIC8': (-3.7, -2.7, 3.7, 2.7),
    'L7028': (-4.45, -3.55, 4.45, 3.55), 'LED': (-1.68, -0.95, 1.68, 0.95),
    'OSC': (-4.0, -3.35, 4.0, 3.35), 'PLCC32S': (-10.8, -5.72, 8.26, 15.88),
    'PLCC44': (-9.1, -9.1, 9.1, 9.1), 'PSSO24': (-6.04, -5.4, 6.04, 5.4),
    'R': (-1.48, -0.73, 1.48, 0.73), 'R0805': (-1.68, -0.95, 1.68, 0.95),
    'R1206': (-2.28, -1.13, 2.28, 1.13), 'R2010': (-3.18, -1.58, 3.18, 1.58),
    'SMA': (-3.5, -1.75, 3.5, 1.75), 'SMB': (-3.65, -2.25, 3.65, 2.25),
    'SO14': (-3.7, -4.58, 3.7, 4.58), 'SO16': (-3.7, -5.2, 3.7, 5.2),
    'SO16W': (-5.93, -5.4, 5.93, 5.4), 'SO20W': (-5.93, -6.65, 5.93, 6.65),
    'SO8': (-3.7, -2.7, 3.7, 2.7), 'SOD123': (-2.35, -1.15, 2.35, 1.15),
    'SOP16': (-4.25, -5.45, 4.25, 5.45), 'SOP28': (-6.95, -9.33, 6.95, 9.33),
    'SOT23': (-1.93, -1.7, 1.93, 1.7), 'SOT89': (-2.85, -2.5, 2.25, 2.5),
    'SW': (-5.0, -3.7, 5.0, 3.7), 'TB10': (-3.21, -2.3, 37.39, 8.5),
    'TB12': (-3.21, -2.3, 45.01, 8.5), 'TB3': (-3.21, -2.3, 10.72, 8.5),
    'TB8': (-3.21, -2.3, 29.77, 8.5), 'TB9': (-3.21, -2.3, 33.58, 8.5),
    'TSSOP16': (-3.85, -2.75, 3.85, 2.75), 'URB': (-13.2, -13.2, 13.2, 13.2),
}


def rotate(x, y, rot):
    """KiCad footprint rotation (degrees, counter-clockwise on screen, y down)."""
    return {0: (x, y), 90: (y, -x), 180: (-x, -y), 270: (-y, x)}[rot % 360]


P_BY_REF = {p['ref']: p for p in PARTS}


def box(ref, x=None, y=None, rot=None):
    """Courtyard (xmin, ymin, xmax, ymax) on the board."""
    p = P_BY_REF[ref]
    x = p['x'] if x is None else x
    y = p['y'] if y is None else y
    rot = p['rot'] if rot is None else rot
    x0, y0, x1, y1 = CRT[p['fp']]
    pts = [rotate(a, b, rot) for a, b in ((x0, y0), (x1, y1))]
    return (x + min(q[0] for q in pts), y + min(q[1] for q in pts),
            x + max(q[0] for q in pts), y + max(q[1] for q in pts))


PLACE = {}                              # ref -> (x, y, rot) of the footprint origin


def at(ref, cx, cy, rot=0):
    """Place ref with its courtyard centred on (cx, cy)."""
    b = box(ref, 0, 0, rot)
    PLACE[ref] = (round(cx - (b[0] + b[2]) / 2, 3), round(cy - (b[1] + b[3]) / 2, 3), rot)


def origin(ref, x, y, rot=0):
    PLACE[ref] = (x, y, rot)


# Areas, 3 mm apart. Bridges (optos, isolators, converters) straddle the gaps.
GAP = 3.0
Y_FIELD = 45.5                          # field digital: y 0 .. 45.5
Y_LOGIC = Y_FIELD + GAP                 # logic: y 48.5 .. 95
Y_LOW = 95.0
Y_ANALOG = Y_LOW + GAP                  # analog and RS-485: y 98 .. bottom
X_485 = 192.5                           # analog x < 192.5, RS-485 x > 195.5
AREA_RECTS = {
    'field': [(0, 0, BOARD_W, Y_FIELD)],
    'logic': [(0, Y_LOGIC, BOARD_W, Y_LOW)],
    'analog': [(0, Y_ANALOG, X_485, BOARD_H)],
    'rs485': [(X_485 + GAP, Y_ANALOG, BOARD_W, BOARD_H)],
    'PE': [(0, Y_LOGIC, 20, Y_LOW)],
}
GAP_FL = Y_FIELD + GAP / 2              # 47.0: centre of the field / logic gap
GAP_LA = Y_LOW + GAP / 2                # 96.5: centre of the logic / analog gap

# ---------------------------------------------------------------- field digital
# Terminals along the top edge, turned 180 degrees so the plugs face out;
# pin k is 3.81 mm to the LEFT of pin k-1. Each channel's parts sit in a
# column under its terminal pin.
T_TOP = 9.0
J_X0 = {'J2': 42.0, 'J3': 86.0, 'J4': 181.5, 'J5': 225.5}
for _j, _x in J_X0.items():
    origin(_j, _x, T_TOP, 180)


def di_x(n):
    return J_X0['J2' if n <= 8 else 'J3'] - 3.81 * ((n - 1) % 8)


def do_x(n):
    return J_X0['J4' if n <= 8 else 'J5'] - 3.81 * ((n - 1) % 8)


for n in range(1, 17):
    x = di_x(n)
    at('R%d' % (100 + n), x, 14.6, 270)          # 4.7k, pad 1 (terminal) up
    at('D%d' % (120 + n), x, 19.9, 270)          # 1N4148W
    at('D%d' % (100 + n), x, 24.6, 90)           # LED, anode up
    at('R%d' % (120 + n), x, 28.6, 270)          # 2.2k shunt
    at('C%d' % (100 + n), x, 32.2, 270)          # 10 nF
    at('R%d' % (140 + n), x, 52.9, 270)          # 22k pull-up (logic)
    x = do_x(n)
    at('R%d' % (240 + n), x, 27.4, 270)          # LED resistor, pad 1 (OUT) up
    at('D%d' % (200 + n), x, 31.6, 90)           # LED
    at('C%d' % (200 + n), x, 35.0, 270)          # 10 nF on OUT
    at('R%d' % (220 + n), x, 38.6, 270)          # VNI input pull-down
    at('R%d' % (200 + n), x, 52.9, 90)           # 1k opto LED (logic)
for k in range(4):
    cx = sum(di_x(4 * k + j) for j in range(1, 5)) / 4
    at('U%d' % (20 + k), cx, GAP_FL, 270)        # input optos: LEDs (1-8) up, in the field area
    cx = sum(do_x(4 * k + j) for j in range(1, 5)) / 4
    at('U%d' % (24 + k), cx, GAP_FL, 90)         # output optos: LEDs (1-8) down, in the logic area
    at('U%d' % (30 + k), cx, 18.3, 90)           # VNI4140K: outputs (13-24) up
# VNI decoupling, in the gaps between the drivers
for _r, _x in (('C30', 168.165), ('C31', 152.9), ('C32', 212.165), ('C33', 197.4)):
    at(_r, _x, 18.3, 90)

# Field supply: J4 pins 9-10 (x 151.0, 147.2) bring 24V_IO and 0V_IO in
at('C34', 134.0, 18.0)                           # 47 uF
at('D6', 134.5, 27.0)                            # SMBJ33A
at('F2', 122.0, 14.5)                            # sensor supply PTC
at('U34', 122.0, 21.5)                           # 78L05 -> +5V_IO
at('C35', 122.0, 26.0)
at('C36', 122.0, 28.5)
at('U35', 136.0, GAP_FL, 270)                    # fault / field-power opto
at('R30', 135.0, 40.5)
at('R31', 129.0, 38.0)
at('R32', 133.0, 53.0)
at('R33', 137.0, 53.0)

# ---------------------------------------------------------------- logic, upper row
# Input buffers under the input optos, output latches under the output optos
for _r, _n0 in (('U14', 1), ('U15', 9)):
    at(_r, sum(di_x(_n0 + j) for j in range(8)) / 8, 60.5, 270)
for _r, _n0 in (('U16', 1), ('U17', 9)):
    at(_r, sum(do_x(_n0 + j) for j in range(8)) / 8, 60.5, 90)
at('C24', 37.3, 60.5, 90)
at('C25', 81.3, 60.5, 90)
at('C26', 159.6, 60.5, 90)
at('C27', 203.6, 60.5, 90)
# Decoding: 74HC00 x2, 74HC30, 74HC138
for _i, _r in enumerate(('U6', 'U7', 'U8', 'U9')):
    at(_r, 93 + 10 * _i, 56.0, 90)
    at('C%d' % (16 + _i), 93 + 10 * _i, 61.3)
# Output clocks (74HC32) and watchdog (74HC123), between the output latches
at('U10', 182.0, 60.0)
at('U11', 196.0, 60.0)
at('C20', 182.0, 66.3)
at('C21', 196.0, 66.3)
at('R5', 189.0, 56.5, 90)
at('C5', 189.0, 62.0, 90)
at('R6', 186.0, 66.3)
at('R7', 191.8, 66.3)
# Clock, reset, pull-ups
at('X1', 46.5, 59.0)
at('C22', 46.5, 64.3)
at('R8', 53.0, 57.0, 90)
at('R9', 56.0, 57.0, 90)
at('U12', 41.5, 65.5)
at('R10', 53.0, 62.5, 90)
at('R11', 56.0, 62.5, 90)
at('R12', 59.0, 62.5, 90)
at('C23', 62.5, 62.5, 90)
# Expansion header (2x16) lying along the upper row
at('J11', 110.0, 65.2, 90)
# USB serial header and jumpers
at('J10', 146.0, 65.5, 90)
at('R21', 152.0, 61.0)
at('JP2', 142.0, 61.0, 90)
at('JP1', 148.0, 57.0, 90)
# Left edge: reset button, LEDs, PE hole
at('SW1', 7.0, 53.5, 90)
at('H1', 4.5, 62.5)
for _i, (_d, _r) in enumerate((('D3', 'R18'), ('D4', 'R19'), ('D5', 'R20'))):
    at(_d, 12.5, 59.5 + 2.6 * _i)
    at(_r, 17.0, 59.5 + 2.6 * _i)
at('C2', 5.5, 67.5)                              # PE to GND

# ---------------------------------------------------------------- logic, CPU row
ROW = 80.0
at('U1', 73.0, ROW, 90)                          # W65C02S: pin 1 bottom left
at('U2', 110.0, ROW, 90)                         # RAM
at('U3', 131.0, ROW)                             # flash socket
at('U4', 168.5, ROW, 90)                         # VIA
at('U5', 205.5, ROW)                             # UART
at('C11', 92.0, 91.5)
at('C12', 110.0, 89.0)
at('C13', 131.0, 93.0)
at('C14', 184.0, 91.5)
at('C15', 217.0, 84.5, 90)
for _i, _r in enumerate(('R13', 'R14', 'R15', 'R16', 'R17')):
    at(_r, 147.5 + 3.4 * _i, 91.5)
# UART interrupt transistors, right of the UART
at('Q1', 218.5, 73.0)
at('Q2', 218.5, 79.0)
at('R1', 223.5, 72.0)
at('R2', 223.5, 78.0)
at('R3', 223.5, 74.0)
at('R4', 223.5, 80.0)
at('H2', 225.5, 62.0)

# Power input, left edge: J1 faces out to the left
origin('J1', 9.0, 72.3, 270)
at('F1', 15.5, 71.0)
at('D1', 23.0, 71.0)
at('D2', 16.0, 75.5)
at('C3', 23.5, 75.0)
at('C4', 23.5, 78.6)
at('U13', 31.0, 74.5)
at('C6', 29.0, 70.0)
at('C7', 37.0, 70.0)
at('C8', 37.0, 72.0)
at('L1', 39.3, 78.5)
at('R22', 31.0, 79.0)
at('R23', 31.0, 81.0)
at('C9', 45.5, 76.0, 90)
at('C10', 45.5, 81.0, 90)
at('C1', 35.6, 89.0)
at('C41', 16.5, 81.3)                           # URB input

# ---------------------------------------------------------------- isolation row
at('PS1', 14.0, GAP_LA, 270)                     # URB: input pins (1, 2) up
at('U42', 60.0, GAP_LA, 270)                     # ISO7741: side 1 up
at('U43', 72.0, GAP_LA, 270)                     # ISO7720: side 1 up
at('C46', 52.0, 92.8)
at('C47', 52.0, 100.0)
at('C48', 78.0, 92.8)
at('C49', 78.0, 100.0)
# B0505XT: pins 1, 2 (input) and 4 (output 0V) share a row, so the barrier
# runs between pins 2 and 4. Turned 270 degrees, 1 and 2 are up (logic) and
# 4 and 5 down (RS-485), with the gap centred 1.27 mm below the body centre.
at('PS2', 222.5, GAP_LA - 1.27, 270)
at('U50', 207.0, GAP_LA, 270)                    # CA-IS3082WX: side A up
at('C60', 199.0, 91.6)
at('C62', 195.5, 91.6)
at('R51', 198.0, 93.6)

# ---------------------------------------------------------------- analog
# Chip row under the isolators
at('U40', 33.0, 103.5)                           # 78L05 -> +5VA
at('C40', 33.5, 109.5)                           # URB output 10 uF
at('C42', 38.0, 103.0, 90)
at('C43', 39.5, 108.5)
at('U41', 44.0, 103.0)                           # REF3040
at('C44', 44.0, 106.6)
at('C45', 47.5, 103.0, 90)
at('U44', 55.0, 107.0, 90)                       # MCP3208: CH0-7 down
at('C50', 63.0, 107.0, 90)
at('U45', 100.0, 106.0)                          # DAC7568
at('C51', 106.0, 106.0, 90)
at('C52', 94.0, 106.0, 90)
at('R34', 100.0, 110.3)
at('U46', 115.0, 106.5, 90)                      # LM324, channels 1-4
at('C53', 121.5, 106.5, 90)
at('U47', 165.0, 106.5, 90)                      # LM324, channels 5-8
at('C54', 171.5, 106.5, 90)

# Channel cells above the bottom terminals: AI cells 11 mm wide from x 2,
# AO cells 12.5 mm wide from x 91, rows from y 113 down to the terminals.
AI_W, AO_W, CELL_Y = 11.0, 12.5, 113.0
for n in range(1, 9):
    x, y = 2.0 + AI_W * (n - 1), CELL_Y
    at('R%d' % (300 + n), x + 1.0, y + 2.5, 90)   # 15k
    at('R%d' % (310 + n), x + 2.8, y + 2.5, 90)   # 10k
    at('R%d' % (320 + n), x + 4.6, y + 2.5, 90)   # 1k
    at('C%d' % (300 + n), x + 6.4, y + 2.5, 90)   # 100 nF
    at('D%d' % (310 + n), x + 9.1, y + 2.5)       # BAV99
    at('JP%d' % (300 + n), x + 2.2, y + 8.3)      # mA jumper
    at('R%d' % (330 + n), x + 5.8, y + 8.3, 90)   # 499R
    at('F%d' % (300 + n), x + 2.3, y + 15.5, 90)  # PTC
    at('D%d' % (300 + n), x + 6.6, y + 15.5, 90)  # SMAJ12A
for n in range(1, 9):
    x, y = 91.0 + AO_W * (n - 1), CELL_Y
    at('Q%d' % (400 + n), x + 2.9, y + 2.6)       # BCX56
    at('Q%d' % (410 + n), x + 8.0, y + 2.0)       # BC847
    at('R%d' % (410 + n), x + 11.0, y + 2.5, 90)  # 22R
    at('JP%d' % (400 + n), x + 3.3, y + 9.8)      # V / mA
    at('R%d' % (400 + n), x + 8.0, y + 6.3)       # base 1k
    at('R%d' % (420 + n), x + 8.0, y + 8.1)       # 30k
    at('R%d' % (430 + n), x + 8.0, y + 9.9)       # 10k
    at('R%d' % (450 + n), x + 8.0, y + 11.7)      # 10k feedback
    at('C%d' % (400 + n), x + 11.0, y + 7.0, 90)  # compensation
    at('C%d' % (410 + n), x + 11.0, y + 10.2, 90)  # 10 nF on OUT
    at('R%d' % (440 + n), x + 10.9, y + 13.8, 90)  # 124R
    at('F%d' % (400 + n), x + 2.3, y + 18.0, 90)  # PTC
    at('D%d' % (400 + n), x + 6.6, y + 18.0, 90)  # SMAJ15A

# Bottom terminals (plugs face down, out of the board)
T_BOT = BOARD_H - 9.0
origin('J6', 25.0, T_BOT)
origin('J7', 100.0, T_BOT)
origin('J8', 140.0, T_BOT)
origin('J9', 200.0, T_BOT)
at('H3', 5.0, BOARD_H - 6.0)
at('H4', 225.5, BOARD_H - 6.0)

# ---------------------------------------------------------------- RS-485 (bus side)
at('C61', 205.0, 106.0, 90)
at('R50', 212.0, 106.0, 90)
at('C63', 222.0, 105.5)
at('C64', 222.0, 108.0)
at('R52', 210.0, 116.0, 90)
at('R53', 213.0, 116.0, 90)
at('R54', 218.0, 116.0, 90)
at('JP3', 222.5, 116.0)
at('D7', 205.0, 116.0)

for _p in PARTS:
    if _p['ref'] not in PLACE:
        raise SystemExit('no placement for ' + _p['ref'])
    _p['x'], _p['y'], _p['rot'] = PLACE[_p['ref']]
