"""C02IO: a Raspberry Pi CM5 industrial I/O board (16 DI, 16 DO, 8 AI, 8 AO, RS-485).

This file is the design: every part, its footprint, roughly where it sits and
what each pin connects to. check_board.py checks it; mk_pcb.py and mk_sch.py
build the KiCad board and schematic from it.

Rev B: the W65C02S system (CPU, RAM, flash, VIA, UART, decoding) is replaced
by a Raspberry Pi Compute Module 5 with gigabit Ethernet and a USB-C port
(rpiboot flashing). The I/O is unchanged except at its logic end:
    inputs 1-16    2 x 74HC165 on SPI0, loaded by GPIO6
    outputs 1-16   2 x 74HC595 on SPI0, latched by CE0 (GPIO8); /OE from the
                   watchdog (GPIO5 = enable, GPIO4 = kick)
    analog         SPI1 through the ISO7741 / ISO7720 (ADC CE0, DAC CE2, /LDAC GPIO24)
    RS-485         UART0 (GPIO14/15), driver enable on RTS (GPIO17)
    status         /OUT_FLT GPIO22, /FIELD_OK GPIO23, LEDs GPIO12/13
The logic side runs at 3.3 V from the CM5's own 3.3 V output, so nothing
drives a CM5 pin while it is unpowered.

Grounds (four isolated areas)
    GND       logic, and the 0 V of the 24 V supply input
    0V_IO     field digital: the 24V_IO supply, inputs and VNI4140K outputs
    AGND_ISO  analog: from the URB2424YMD-6WR3 isolated converter
    GND_485   RS-485 bus side: from the B0505XT-1WR3 isolated converter

Datasheets the pin tables were checked against (2026-11-20, rev B 2026-11-23):
    CM5              Raspberry Pi CM5 datasheet Release 4 (Nov 2026), Table 4; CM5 IO
                     board rev 2 schematic and KiCad files (footprints in vendor/cm5io)
    TRJG0926HENL     as wired on the CM5 IO board (MagJack A70-112-331N126)
    TYPE-C-31-M-12   HRO drawing Rev A (2020-12-08)
    USBLC6-2SC6      KiCad symbol (ST usblc6-2.pdf), UMW second-source drawing
    TPS54560B        TI SLVSF00 (Jan 2019), HSOIC-8 (DDA)
    74HC165/595      TI SCLS116H / SCLS041J
    VNI4140K         ST Doc ID 14174 Rev 5 (Aug 2009), PowerSSO-24
    TLP291-4         Toshiba Rev 9.0 (2026-10-29), SO16
    CD74HC123        TI SCHS142F (Oct 2003), SOIC-16; K ~0.48 at 3.3 V (Fig. 5): tW ~106 ms
    DAC7568          TI SBAS430F (Apr 2018), TSSOP-16
    REF3040          TI SBVS032K (Dec 2025), SOT-23-3
    ISO7741          TI SLLSEP4K (Aug 2026), SOIC-16 wide
    ISO7720          TI SLLSEP3G (May 2024), SOIC-8
    LM324            TI SLOS066AE (Sep 2025), SOIC-14
    78L05 (SOT-89)   TI SLVS010X, onsemi MC78L00A/D Rev 21, JSCJ CJ78L Rev 3.1:
                     all 1 = OUT, 2 = GND, 3 = IN
    URB2424YMD-6WR3  Mornsun URB_YMD-6WR3 (2026.09.18)
    B0505XT-1WR3     Mornsun B05_XT-1WR3 (2022.01.08)
    CA-IS3082WX      Chipanalog CA-IS308x V1.08 (2023/11/13), SOIC-16 wide
    SM712            Semtech Rev 6.0 (2017)
    BCX56 / BC847 / BAV99   Nexperia Rev 13 (2023) / Rev 12 (2019) / Rev 8 (2010)
    MCP3208          Microchip, checked in the spec (README)
"""

# ------------------------------------------------------------ footprints
FP = {
    # through-hole: sockets and connectors, soldered by hand
    'H1x2': 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
    'H1x3': 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
    'H2x3': 'Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical',
    'H2x5': 'Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical',
    'RJ45': 'c02io:TRJG0926HENL',                     # from the CM5 IO board files
    'USBC': 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
    'URB': 'c02io:Mornsun_URB_YMD-6WR3_THT',          # project library (to make)
    'HOLE': 'MountingHole:MountingHole_3.2mm_M3',
    'HOLE_PE': 'MountingHole:MountingHole_3.2mm_M3_Pad',
    # SMD, assembled by JLCPCB
    'CM5': 'c02io:Raspberry-Pi-5-Compute-Module',      # from the CM5 IO board files
    'SO8': 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
    'SO14': 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',
    'SO16': 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm',
    'SO16W': 'Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm',
    'SOP16': 'Package_SO:SOP-16_4.4x10.4mm_P1.27mm',        # TLP291-4
    'TSSOP16': 'Package_SO:TSSOP-16_4.4x5mm_P0.65mm',
    'PSSO24': 'Package_SO:ST_PowerSSO-24_SlugDown_ThermalVias',
    'HSOIC8': 'Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm',   # mk_pcb.py adds 0.3 mm thermal vias
    'B05XT': 'c02io:Mornsun_B05_XT-1WR3_SMD',          # project library (to make)
    'SOT23': 'Package_TO_SOT_SMD:SOT-23',
    'SOT89': 'Package_TO_SOT_SMD:SOT-89-3',
    'SOT23-6': 'Package_TO_SOT_SMD:SOT-23-6',
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
    'L1245': 'Inductor_SMD:L_Bourns_SRP1245A',
    'LED': 'LED_SMD:LED_0805_2012Metric',              # pad 1 = K, pad 2 = A
    'SOD123': 'Diode_SMD:D_SOD-123',                    # pad 1 = K, pad 2 = A
    'SMA': 'Diode_SMD:D_SMA',                           # pad 1 = K, pad 2 = A
    'SMB': 'Diode_SMD:D_SMB',                           # pad 1 = K, pad 2 = A
    'SMC': 'Diode_SMD:D_SMC',                           # pad 1 = K, pad 2 = A
    'F1206': 'Fuse:Fuse_1206_3216Metric',
    'F1812': 'Fuse:Fuse_1812_4532Metric',
    'SW': 'Button_Switch_SMD:SW_SPST_B3S-1000',
}
for _n in (3, 8, 9, 10, 12):
    FP['TB%d' % _n] = ('Connector_Phoenix_MC:PhoenixContact_MC_1,5_%d-G-3.81_1x%02d_P3.81mm_Horizontal'
                       % (_n, _n))

# Pins per footprint, for the "every pin listed" check
NPINS = {'CM5': 200, 'SO8': 8, 'SO14': 14, 'SO16': 16, 'SO16W': 16, 'SOP16': 16, 'TSSOP16': 16,
         'PSSO24': 25, 'HSOIC8': 9, 'SOT23': 3, 'SOT23-6': 6, 'SOT89': 3}

BOARD_W, BOARD_H = 230.0, 157.0

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
#   y   0-45   field digital (0V_IO): terminals along the top edge
#   y  48-105  logic (GND): CM5, Ethernet and USB-C on the right edge,
#              power input on the left edge
#   y 108-157  analog (AGND_ISO): terminals along the bottom edge
#   y 108-157  RS-485 (GND_485), bottom right

# ============================================================ Compute Module 5
# Raspberry Pi CM5 on two Amphenol 10164227-1001A1RLF (1.5 mm stack). Pin
# numbers from the CM5 datasheet (Release 4, Table 4 pp.17-22) and the CM5 IO
# board schematic and KiCad files (revision 2). Unused pins are left open:
# GPIO0/1 (HAT ID), SD (Lite only), PCIe, MIPI, HDMI, USB 3, fan, CC1/CC2,
# PMIC_Enable, EEPROM_nWP, WL/BT_nDisable, VBAT (no RTC battery).
CM5_GND = (1, 2, 7, 8, 13, 14, 22, 23, 32, 33, 42, 43, 52, 53, 59, 60, 65, 66, 71, 74, 98,
           107, 108, 113, 114, 119, 120, 125, 126, 131, 132, 137, 138, 144, 150, 155, 156, 161,
           162, 167, 168, 173, 174, 179, 180, 185, 186, 191, 192, 197, 198)
CM5_GPIO = {0: 36, 1: 35, 2: 58, 3: 56, 4: 54, 5: 34, 6: 30, 7: 37, 8: 39, 9: 40, 10: 44, 11: 38,
            12: 31, 13: 28, 14: 55, 15: 51, 16: 29, 17: 50, 18: 49, 19: 26, 20: 27, 21: 25,
            22: 46, 23: 47, 24: 45, 25: 41, 26: 24, 27: 48}
# GPIO use (RP1 alternate functions, CM5 datasheet Table 1 pp.11-12):
#   SPI0 (a0)  shift registers: 11 SCLK, 10 MOSI -> 74HC595 chain, 9 MISO <- 74HC165
#              chain, 8 CE0 = 74HC595 latch (rises at the end of the transfer)
#   SPI1 (a0)  analog side through the ISO7741/ISO7720: 21 SCLK, 20 MOSI, 19 MISO,
#              18 CE0 = ADC /CS, 16 CE2 = DAC /SYNC
#   UART0 (a4) RS-485: 14 TX, 15 RX, 17 RTS = driver enable (Linux RS-485 mode,
#              set so the pin is high while sending)
#   4 watchdog kick, 5 output enable, 6 input load (/PL), 12 RUN LED, 13 FAULT LED,
#   22 /OUT_FLT in, 23 /FIELD_OK in, 24 DAC /LDAC
#   2/3 (I2C1, 1.8k pull-ups on the module), 7, 25, 26, 27 to the expansion header
GPIO_USE = {2: 'GPIO2_SDA', 3: 'GPIO3_SCL', 4: 'WD_KICK', 5: 'OUT_EN', 6: '~{DI_LOAD}',
            7: 'GPIO7', 8: 'SR_LATCH', 9: 'SR_MISO', 10: 'SR_MOSI', 11: 'SR_SCLK',
            12: 'LED_RUN', 13: 'LED_FAULT', 14: 'UA_TX', 15: 'UA_RX', 16: '~{DAC_SYNC}',
            17: 'DIR485', 18: '~{ADC_CS}', 19: 'SPI_MISO', 20: 'SPI_MOSI', 21: 'SPI_SCLK',
            22: '~{OUT_FLT}', 23: '~{FIELD_OK}', 24: '~{DAC_LDAC}', 25: 'GPIO25', 26: 'GPIO26',
            27: 'GPIO27'}
CM5_PINS = {k: None for k in range(1, 201)}
CM5_PINS.update({k: 'GND' for k in CM5_GND})
CM5_PINS.update({k: '+5V' for k in (77, 79, 81, 83, 85, 87)})       # 5 V in, 4.75-5.25 V
CM5_PINS.update({84: '+3V3', 86: '+3V3', 78: '+3V3'})               # 3.3 V out (600 mA), GPIO_VREF
CM5_PINS.update({CM5_GPIO[g]: n for g, n in GPIO_USE.items()})
CM5_PINS.update({
    12: 'ETH0_P', 10: 'ETH0_N', 4: 'ETH1_P', 6: 'ETH1_N', 11: 'ETH2_P', 9: 'ETH2_N',
    3: 'ETH3_P', 5: 'ETH3_N', 15: 'ETH_NLED3', 17: 'ETH_NLED2',
    21: 'LED_NACT', 92: '~{PWR_BUT}', 93: '~{RPIBOOT}', 103: 'USB_DN', 105: 'USB_DP'})
part('U1', 'CM5', 'CM5', 0, 0, pins=CM5_PINS,
     mpn='Raspberry Pi CM5 (any RAM/eMMC/wireless option)',
     note='on 2 x Amphenol 10164227-1001A1RLF; M2.5 spacers to suit the 1.5 mm stack')
two('C11', '10uF', 'C0805', 0, 0, '+3V3', 'GND', note='CM5 3.3 V out')
two('C12', '22uF 16V', 'C1210', 0, 0, '+5V', 'GND', note='near the CM5 5 V pins, X7R')
two('C13', '22uF 16V', 'C1210', 0, 0, '+5V', 'GND', note='X7R')

# Ethernet: TRXCOM TRJG0926HENL gigabit MagJack (footprint from the CM5 IO
# board), wired as there: PHY-side centre taps (4, 5) to 100 nF only; line-side
# taps (11-14, PoE) open; LED anodes to 3.3 V, cathodes through 470R to nLED3
# (green, activity) and nLED2 (yellow, speed). Shield to GND.
# Pairs: 100 ohm differential, P/N matched to 0.15 mm.
part('J12', 'ETHERNET', 'RJ45', 0, 0, pins={
    1: 'ETH0_P', 2: 'ETH0_N', 3: 'ETH1_P', 6: 'ETH1_N', 7: 'ETH2_P', 8: 'ETH2_N',
    9: 'ETH3_P', 10: 'ETH3_N', 4: 'ETH_CT', 5: 'ETH_CT', 11: None, 12: None, 13: None, 14: None,
    15: '+3V3', 16: 'ETH_LY_K', 17: '+3V3', 18: 'ETH_LG_K', 19: 'GND', 20: 'GND'},
    mpn='TRXCOM TRJG0926HENL', note='as on the CM5 IO board; through-hole, hand-soldered')
two('C70', '100nF', 'C', 0, 0, 'ETH_CT', 'GND', note='MagJack PHY-side centre taps')
two('R25', '470', 'R', 0, 0, 'ETH_NLED3', 'ETH_LG_K', note='green LED (activity)')
two('R26', '470', 'R', 0, 0, 'ETH_NLED2', 'ETH_LY_K', note='yellow LED (speed)')

# USB-C (USB 2.0 device: rpiboot flashing and gadget console). The board is
# powered from 24 V, so VBUS is NOT joined to +5V (it would feed the host): it
# only reaches the ESD part and 100 nF. Rd 5.1k on CC1 and CC2 so the host turns
# VBUS on. USB_OTG_ID left open (device). Pairs: 90 ohm differential.
part('J13', 'USB-C', 'USBC', 0, 0, pins={
    'A1': 'GND', 'B12': 'GND', 'B1': 'GND', 'A12': 'GND', 'A4': 'USB_VBUS', 'B9': 'USB_VBUS',
    'B4': 'USB_VBUS', 'A9': 'USB_VBUS', 'A5': 'USB_CC1', 'B5': 'USB_CC2', 'A6': 'USB_DP',
    'B6': 'USB_DP', 'A7': 'USB_DN', 'B7': 'USB_DN', 'A8': None, 'B8': None, 'SH': 'GND'},
    mpn='Korean Hroparts TYPE-C-31-M-12 (LCSC C165948)')
two('R27', '5.1k', 'R', 0, 0, 'USB_CC1', 'GND', note='Rd')
two('R28', '5.1k', 'R', 0, 0, 'USB_CC2', 'GND', note='Rd')
two('C71', '100nF', 'C', 0, 0, 'USB_VBUS', 'GND')
part('U51', 'USBLC6-2SC6', 'SOT23-6', 0, 0, pins={
    1: 'USB_DP', 2: 'GND', 3: 'USB_DN', 4: 'USB_DN', 5: 'USB_VBUS', 6: 'USB_DP'},
    mpn='ST USBLC6-2SC6 (LCSC C7519)', note='1/6 = line 1, 3/4 = line 2, 2 GND, 5 VBUS')

# Boot and power: JP1 fitted at power-up = USB boot (rpiboot); SW1 = CM5
# power button (press to start after a shutdown, hold 5 s to force off).
two('JP1', 'RPIBOOT', 'H1x2', 0, 0, '~{RPIBOOT}', 'GND', note='fit, then power up, to flash eMMC')
two('SW1', 'POWER', 'SW', 0, 0, '~{PWR_BUT}', 'GND', mpn='Omron B3S-1000',
    note='footprint pads 1 and 2 each appear twice')
two('D8', 'ACT', 'LED', 0, 0, 'ACT_K', '+3V3', mpn='0805 LED, green')
two('R24', '1k', 'R', 0, 0, 'ACT_K', 'LED_NACT', note='CM5 activity LED (open drain)')
two('R29', '10k', 'R', 0, 0, 'DIR485', 'GND', note='RS-485 driver off while GPIO17 floats')

# Expansion header (3.3 V logic): I2C1 and four spare GPIOs
part('J11', 'EXPANSION', 'H2x5', 0, 0, pins={
    1: '+3V3', 2: '+5V', 3: 'GPIO2_SDA', 4: 'GND', 5: 'GPIO3_SCL', 6: 'GPIO25', 7: 'GPIO26',
    8: 'GPIO27', 9: 'GND', 10: 'GPIO7'}, note='3V3 5V SDA GND SCL 25 26 27 GND 7')

# ============================================================ watchdog
# CD74HC123 half 1 at 3.3 V: B (rising edge, /A low) retriggers from GPIO4.
# /R = OUT_EN (GPIO5): while it is low, /Q is high and the 74HC595 outputs are
# off. /Q low (= triggered) enables them, so the outputs work only while
# software sets OUT_EN AND keeps kicking. GPIO4 is pulled low so the release of
# /R can't trigger it. tW = 0.45 * Rx * Cx = 0.45 * 100k * 2.2uF = ~100 ms
# (less with the capacitor's DC-bias loss: kick it at least every 25 ms).
# Half 2 unused: /A high, B low, /R low.
part('U11', 'CD74HC123', 'SO16', 0, 0, pins={
    1: 'GND', 2: 'WD_KICK', 3: 'OUT_EN', 4: '~{OUT_OE}', 5: None, 6: 'GND', 7: 'GND', 8: 'GND',
    9: '+3V3', 10: 'GND', 11: 'GND', 12: None, 13: None, 14: 'WD_CX', 15: 'WD_RC', 16: '+3V3'},
    mpn='TI CD74HC123M96')
decouple('C14', 0, 0, '+3V3')
two('R5', '100k', 'R', 0, 0, '+3V3', 'WD_RC', note='watchdog Rx')
two('C5', '2.2uF', 'C1206', 0, 0, 'WD_RC', 'WD_CX', note='watchdog Cx, X7R 25 V')
two('R6', '10k', 'R', 0, 0, 'WD_KICK', 'GND', note='GPIO4 low while the CM5 boots')
two('R7', '10k', 'R', 0, 0, 'OUT_EN', 'GND', note='GPIO5 low: outputs off until software sets it')

# SPI chip selects held inactive while the GPIOs are inputs
two('R15', '10k', 'R', 0, 0, '+3V3', '~{ADC_CS}')
two('R16', '10k', 'R', 0, 0, '+3V3', '~{DAC_SYNC}')
two('R17', '10k', 'R', 0, 0, '+3V3', '~{DAC_LDAC}')

# RUN / FAULT LEDs on GPIO12 / GPIO13 (lit when high), power LED on +5V
for i, (net, col) in enumerate((('LED_RUN', 'green'), ('LED_FAULT', 'red'))):
    two('D%d' % (3 + i), 'RUN' if i == 0 else 'FAULT', 'LED', 0, 0,
        'NL%d' % i, net, mpn='0805 LED, ' + col)
    two('R%d' % (18 + i), '680', 'R', 0, 0, 'NL%d' % i, 'GND', note='~2 mA from 3.3 V')
two('D5', 'PWR', 'LED', 0, 0, 'NLP', '+5V', mpn='0805 LED, green')
two('R20', '1k', 'R', 0, 0, 'NLP', 'GND')

# ============================================================ power input
# 24 V (18-32 V) -> 3 A fuse -> SS54 -> SMBJ33A -> +24V (logic-side raw supply)
part('J1', '24V IN', 'TB3', 0, 0, pins={1: '24V_RAW', 2: 'GND', 3: 'PE'},
     note='1 = +24 V, 2 = 0 V, 3 = PE')
two('F1', '3A', 'F1206', 0, 0, '24V_RAW', '24V_F', note='fast fuse')
two('D1', 'SS54', 'SMB', 0, 0, '+24V', '24V_F', note='reverse polarity, 5 A (K = +24V)')
two('D2', 'SMBJ33A', 'SMB', 0, 0, '+24V', 'GND', note='TVS')
two('C1', '100uF 50V', 'CP10', 0, 0, '+24V', 'GND')
two('C2', '1nF 2kV', 'C1808', 0, 0, 'PE', 'GND', note='PE to logic 0 V')

# TPS54560B (TI SLVSF00, Jan 2019): 4.5-60 V in, 5 A, non-synchronous, so a
# B560C catch diode. Values from the datasheet's 5 V / 5 A design (Fig. 32,
# pp.24-31): 400 kHz (RT 243k), FB 0.8 V x (1 + 53.6k/10.2k) = 5.00 V,
# COMP 16.9k + 4.7 nF with 47 pF, BOOT 100 nF. L = 10 uH for 24-48 V in.
# EN left open (on). Budget: CM5 2.5 A (datasheet B.3) + RS-485 converter
# and LEDs; the CM5 PSU warning is silenced with PSU_MAX_CURRENT in its EEPROM.
part('U13', 'TPS54560BDDAR', 'HSOIC8', 0, 0, pins={
    1: 'BUCK_BOOT', 2: '+24V', 3: None, 4: 'BUCK_RT', 5: 'BUCK_FB', 6: 'BUCK_COMP', 7: 'GND',
    8: 'BUCK_SW', 9: 'GND'}, mpn='TI TPS54560BDDAR (LCSC C1850354)')
two('C3', '4.7uF 50V', 'C1210', 0, 0, '+24V', 'GND', note='X7R, at VIN')
two('C4', '4.7uF 50V', 'C1210', 0, 0, '+24V', 'GND', note='X7R')
two('C6', '220nF 100V', 'C0805', 0, 0, '+24V', 'GND', note='closest to VIN/GND')
two('C7', '100nF', 'C', 0, 0, 'BUCK_BOOT', 'BUCK_SW', note='BOOT, X7R 16 V+')
two('R8', '243k', 'R', 0, 0, 'BUCK_RT', 'GND', note='RT: 400 kHz, 1 %')
two('R9', '16.9k', 'R', 0, 0, 'BUCK_COMP', 'BUCK_CZ', note='compensation')
two('C8', '4.7nF', 'C', 0, 0, 'BUCK_CZ', 'GND', note='compensation')
two('C15', '47pF', 'C', 0, 0, 'BUCK_COMP', 'GND', note='compensation')
two('D9', 'B560C', 'SMC', 0, 0, 'BUCK_SW', 'GND', note='catch diode, 60 V 5 A (LCSC C85100)')
two('L1', '10uH', 'L1245', 0, 0, 'BUCK_SW', '+5V', mpn='Bourns SRP1245A-100M',
    note='Isat >= 8 A (the TPS54560B current limit)')
two('R22', '53.6k', 'R', 0, 0, '+5V', 'BUCK_FB', note='RFBT, 1 %')
two('R23', '10.2k', 'R', 0, 0, 'BUCK_FB', 'GND', note='RFBB, 1 %')
two('C9', '47uF 10V', 'C1210', 0, 0, '+5V', 'GND', note='X7R/X5R')
two('C10', '47uF 10V', 'C1210', 0, 0, '+5V', 'GND')
two('C16', '47uF 10V', 'C1210', 0, 0, '+5V', 'GND')

# ============================================================ digital inputs (x16)
# Field side, per input: terminal -> 4.7k (1206) -> green LED -> opto LED -> 0V_IO,
# with 2.2k and 10 nF across the opto LED and a 1N4148W from 0V_IO to the
# 4.7k's far end (reverse voltage). About 1.7 mA at 11 V; 5 V stays off.
# Logic side: opto collector pulled up by 22k to 3.3 V, read by a 74HC165 (low = on).
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
    two('R%d' % (140 + n), '22k', 'R', x, 46, '+3V3', 'DIN%d' % n, note='pull-up')
for k in range(4):                                    # U20-U23: inputs 4k+1 .. 4k+4
    opto4('U%d' % (20 + k), 14 + 22 * k, 38,
          [('DI%d_K' % (4 * k + j), '0V_IO', 'DIN%d' % (4 * k + j), 'GND') for j in range(1, 5)])

# 74HC165 x2 (TI SCLS116H): 1 SH/LD, 2 CLK, 3-6 E-H, 7 /QH, 8 GND, 9 QH,
# 10 SER, 11-14 A-D, 15 CLK INH, 16 VCC. Input n -> A..H of U14 (1-8) / U15 (9-16).
# GPIO6 pulses /PL low to load, then SPI0 clocks the chain: U14 QH -> MISO,
# U15 QH -> U14 SER. First bit read = input 8, then 7 .. 1, 16 .. 9 (low = on).
HC165_IN = (11, 12, 13, 14, 3, 4, 5, 6)                  # A..H
for i, (ref, ser, qh) in enumerate((('U14', 'SR_CHAIN_I', 'SR_MISO'), ('U15', 'GND', 'SR_CHAIN_I'))):
    pins = {1: '~{DI_LOAD}', 2: 'SR_SCLK', 7: None, 8: 'GND', 9: qh, 10: ser, 15: 'GND', 16: '+3V3'}
    for k in range(8):
        pins[HC165_IN[k]] = 'DIN%d' % (8 * i + k + 1)
    part(ref, '74HC165', 'SO16', 20 + 40 * i, 50, pins=pins, mpn='Nexperia 74HC165D (LCSC C5613)')
    decouple('C%d' % (24 + i), 28 + 40 * i, 50, '+3V3')

# ============================================================ digital outputs (x16)
# 74HC595 -> 330R -> opto LED -> GND. Opto transistor: +5V_IO -> VNI4140K IN,
# 10k pull-down. /OE = ~OUT_OE from the watchdog (high = outputs off).
# 74HC595 x2 (TI SCLS041J): 15 QA, 1-7 QB-QH, 8 GND, 9 QH', 10 /SRCLR, 11 SRCLK,
# 12 RCLK, 13 /OE, 14 SER, 16 VCC. SPI0 MOSI -> U16 SER, U16 QH' -> U17 SER;
# RCLK = CE0 latches at the end of the 16-bit transfer. Output n = QA..QH of
# U16 (1-8) / U17 (9-16): send outputs 16 .. 9, then 8 .. 1 (MSB first).
HC595_Q = (15, 1, 2, 3, 4, 5, 6, 7)                      # QA..QH
for i, (ref, ser, qh2) in enumerate((('U16', 'SR_MOSI', 'SR_CHAIN_O'), ('U17', 'SR_CHAIN_O', None))):
    pins = {8: 'GND', 9: qh2, 10: '+3V3', 11: 'SR_SCLK', 12: 'SR_LATCH', 13: '~{OUT_OE}',
            14: ser, 16: '+3V3'}
    for k in range(8):
        pins[HC595_Q[k]] = 'DQ%d' % (8 * i + k + 1)
    part(ref, '74HC595', 'SO16', 110 + 40 * i, 50, pins=pins, mpn='Nexperia 74HC595D (LCSC C5947)')
    decouple('C%d' % (26 + i), 118 + 40 * i, 50, '+3V3')

for n in range(1, 17):
    x = 104 + 5.5 * (n - 1)
    two('R%d' % (200 + n), '330', 'R', x, 44, 'DQ%d' % n, 'DO%d_A' % n,
        note='opto LED, ~5 mA from 3.3 V (TLP291 VF 1.2 V typ)')
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

# U35 TLP291-4: ch1 = output fault (GPIO22), ch2 = field power present (GPIO23), ch3-4 spare.
# Fault: +5V_IO -> 2.2k -> opto LED -> OUT_FLT (pulled low by any STATn).
# Field power: 24V_IO -> 10k -> opto LED -> 0V_IO.
opto4('U35', 96, 32, [('FLT_A', 'OUT_FLT', '~{OUT_FLT}', 'GND'),
                      ('FPW_A', '0V_IO', '~{FIELD_OK}', 'GND'),
                      ('0V_IO', '0V_IO', None, 'GND'),
                      ('0V_IO', '0V_IO', None, 'GND')])
two('R30', '2.2k', 'R', 92, 28, '+5V_IO', 'FLT_A', note='~1.5 mA; STAT is specified at 1.6 mA')
two('R31', '10k', 'R1206', 92, 30, '24V_IO', 'FPW_A', note='~2.2 mA at 24 V')
two('R32', '22k', 'R', 100, 44, '+3V3', '~{OUT_FLT}', note='GPIO22 pull-up')
two('R33', '22k', 'R', 102, 44, '+3V3', '~{FIELD_OK}', note='GPIO23 pull-up')

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

# SPI1 across the barrier, 3.3 V side 1, 5 V side 2 (2.25-5.5 V each, set
# independently). ISO7741 (default-high, no F suffix): A/B/C forward
# = SCLK, MOSI, ADC /CS; D back = MISO. EN1/EN2 tied high.
part('U42', 'ISO7741DWR', 'SO16W', 50, 84, pins={
    1: '+3V3', 2: 'GND', 3: 'SPI_SCLK', 4: 'SPI_MOSI', 5: '~{ADC_CS}', 6: 'SPI_MISO', 7: '+3V3',
    8: 'GND', 9: 'AGND_ISO', 10: '+5VA', 11: 'MISO_I', 12: '~{ADC_CS_I}', 13: 'MOSI_I',
    14: 'SCLK_I', 15: 'AGND_ISO', 16: '+5VA'}, mpn='TI ISO7741DWR (default high)')
# ISO7720 (default-high): DAC /SYNC and /LDAC
part('U43', 'ISO7720DR', 'SO8', 64, 84, pins={
    1: '+3V3', 2: '~{DAC_SYNC}', 3: '~{DAC_LDAC}', 4: 'GND', 5: 'AGND_ISO', 6: '~{DAC_LDAC_I}',
    7: '~{DAC_SYNC_I}', 8: '+5VA'}, mpn='TI ISO7720DR (default high)')
for _r, _x, _y, _v, _g in (('C46', 46, 80, '+3V3', 'GND'), ('C47', 46, 90, '+5VA', 'AGND_ISO'),
                           ('C48', 60, 80, '+3V3', 'GND'), ('C49', 60, 90, '+5VA', 'AGND_ISO')):
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

# ============================================================ RS-485 (UART0)
# B0505XT-1WR3 (SMD): 1 GND, 2 Vin, 4 0V, 5 +Vo, 8 NC (isolated). 20 mA
# minimum load: R50 (330R, 15 mA) plus the bias network and transceiver.
part('PS2', 'B0505XT-1WR3', 'B05XT', 176, 92, pins={1: 'GND', 2: '+5V', 4: 'GND_485', 5: '+5V_485', 8: None},
     mpn='Mornsun B0505XT-1WR3')
two('C60', '4.7uF', 'C0805', 172, 88, '+5V', 'GND', note='B0505 input')
two('C61', '10uF', 'C0805', 182, 88, '+5V_485', 'GND_485', note='B0505 output')
two('R50', '330', 'R1206', 186, 92, '+5V_485', 'GND_485', note='minimum load')
# CA-IS3082WX: 1 VDDA, 2/7/8 GNDA, 3 RO, 4 /RE, 5 DE, 6 DI, 9/10/15 GNDB,
# 12 A, 13 B, 11/14 NC, 16 VDDB. DE = /RE = DIR485 (high = transmit).
# VDDA 3.3 V (2.375-5.5 V), VDDB 5 V; DE/DI TTL inputs, RO swings to VDDA.
part('U50', 'CA-IS3082WX', 'SO16W', 176, 102, pins={
    1: '+3V3', 2: 'GND', 3: 'UA_RX', 4: 'DIR485', 5: 'DIR485', 6: 'UA_TX', 7: 'GND', 8: 'GND',
    9: 'GND_485', 10: 'GND_485', 11: None, 12: 'RS485_A', 13: 'RS485_B', 14: None,
    15: 'GND_485', 16: '+5V_485'}, mpn='Chipanalog CA-IS3082WX')
decouple('C62', 170, 98, '+3V3')
decouple('C63', 182, 98, '+5V_485', 'GND_485')
two('C64', '1uF', 'C', 184, 100, '+5V_485', 'GND_485', note='VDDB 0.1 + 1 uF')
two('R51', '10k', 'R', 166, 96, '+3V3', 'UA_RX', note='RO is off while transmitting')
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
    'logic': {'GND', '+5V', '+3V3', '+24V', '24V_RAW', '24V_F', 'USB_VBUS'},
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
    'CM5': (-3.75, -51.75, 36.75, 3.75), 'RJ45': (-9.25, -10.75, 9.25, 11.15),
    'USBC': (-5.32, -5.27, 5.32, 4.15), 'SOT23-6': (-2.05, -1.7, 2.05, 1.7),
    'SMC': (-4.9, -3.35, 4.9, 3.35), 'L1245': (-7.35, -6.5, 7.35, 6.5),
    'H2x5': (-1.77, -1.77, 4.32, 11.93),
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
Y_LOGIC = Y_FIELD + GAP                 # logic: y 48.5 .. 105
Y_LOW = 105.0
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
# Input shift registers under the input optos, output shift registers under
# the output optos
SR_Y = 58.7
for _r, _n0 in (('U14', 1), ('U15', 9)):
    at(_r, sum(di_x(_n0 + j) for j in range(8)) / 8, SR_Y, 270)
for _r, _n0 in (('U16', 1), ('U17', 9)):
    at(_r, sum(do_x(_n0 + j) for j in range(8)) / 8, SR_Y, 90)
at('C24', 37.3, SR_Y, 90)
at('C25', 81.3, SR_Y, 90)
at('C26', 159.6, SR_Y, 90)
at('C27', 203.6, SR_Y, 90)
at('H2', 225.5, 59.0)
# Left edge: power button, LEDs, PE hole
at('SW1', 7.0, 53.5, 90)
at('H1', 4.5, 62.5)
for _i, (_d, _r) in enumerate((('D3', 'R18'), ('D4', 'R19'), ('D5', 'R20'), ('D8', 'R24'))):
    at(_d, 12.5, 59.5 + 2.6 * _i)
    at(_r, 17.0, 59.5 + 2.6 * _i)
at('C2', 5.5, 67.5)                              # PE to GND

# ---------------------------------------------------------------- CM5, Ethernet, USB
# CM5 turned 270 degrees: connector 1-100 along the top, 101-200 along the
# bottom, the Ethernet pins (3-12) toward the right, near the jack.
at('U1', 175.75, 83.5, 270)
at('C12', 145.5, 66.0, 90)                       # 5 V, left of the module
at('C13', 145.5, 71.0, 90)
at('C11', 145.5, 75.5, 90)                       # 3.3 V
# MagJack on the right edge, cable end out (footprint front = +y, turned 90)
origin('J12', BOARD_W - 11.15, 73.0, 90)
at('R25', 205.8, 68.0, 90)
at('R26', 205.8, 72.0, 90)
at('C70', 205.8, 76.0, 90)
# USB-C below it, also opening to the right
origin('J13', BOARD_W - 4.15, 89.0, 90)
at('U51', 216.0, 88.5)
at('R27', 209.5, 85.5)
at('R28', 209.5, 88.0)
at('C71', 209.5, 90.5)
at('R29', 209.5, 93.0)                           # DIR485 pull-down

# ---------------------------------------------------------------- watchdog, boot, expansion
at('U11', 138.0, 74.0)
at('C14', 138.0, 66.6)
at('R5', 131.0, 69.5, 90)
at('C5', 131.0, 74.5, 90)
at('R6', 131.0, 79.5, 90)
at('R7', 138.0, 81.5)
at('J11', 125.0, 99.0, 90)                       # expansion header
at('JP1', 138.0, 99.0, 90)                       # RPIBOOT jumper
for _i, _r in enumerate(('R15', 'R16', 'R17')):  # SPI1 chip-select pull-ups
    at(_r, 84.0 + 3.5 * _i, 101.5, 90)

# Power input, left edge: J1 faces out to the left
origin('J1', 9.0, 72.3, 270)
at('F1', 15.5, 71.0)
at('D1', 23.0, 71.0)
at('D2', 16.0, 75.5)
at('C3', 23.5, 75.0)
at('C4', 23.5, 78.6)
at('U13', 31.0, 74.5)                            # TPS54560B
at('C6', 29.0, 70.0)
at('C7', 35.5, 70.5)                             # BOOT
at('R8', 28.0, 79.5)                             # RT
at('R9', 31.5, 79.5)                             # COMP R
at('C8', 35.0, 79.5)                             # COMP C
at('C15', 28.0, 81.5)                            # COMP 47 pF
at('R22', 31.5, 81.5)                            # FB top
at('R23', 35.0, 81.5)                            # FB bottom
at('D9', 42.0, 74.0, 90)                         # B560C catch diode
at('L1', 53.0, 75.0)                             # 10 uH
at('C9', 63.5, 75.0, 90)                         # 47 uF output
at('C10', 67.0, 75.0, 90)
at('C16', 70.5, 75.0, 90)
at('C1', 35.6, 89.0)
at('C41', 16.5, 81.3)                            # URB input

# ---------------------------------------------------------------- isolation row
at('PS1', 14.0, GAP_LA, 270)                     # URB: input pins (1, 2) up
at('U42', 60.0, GAP_LA, 270)                     # ISO7741: side 1 up
at('U43', 72.0, GAP_LA, 270)                     # ISO7720: side 1 up
at('C46', 52.0, 102.8)
at('C47', 52.0, 110)
at('C48', 78.0, 102.8)
at('C49', 78.0, 110)
# B0505XT: pins 1, 2 (input) and 4 (output 0V) share a row, so the barrier
# runs between pins 2 and 4. Turned 270 degrees, 1 and 2 are up (logic) and
# 4 and 5 down (RS-485), with the gap centred 1.27 mm below the body centre.
at('PS2', 222.5, GAP_LA - 1.27, 270)
at('U50', 210.0, GAP_LA, 270)                    # CA-IS3082WX: side A up
at('C60', 217.0, 95.5)
at('C62', 207.0, 98.6)
at('R51', 212.5, 98.6)

# ---------------------------------------------------------------- analog
# Chip row under the isolators
at('U40', 33.0, 113.5)                           # 78L05 -> +5VA
at('C40', 33.5, 119.5)                           # URB output 10 uF
at('C42', 38.0, 113, 90)
at('C43', 39.5, 118.5)
at('U41', 44.0, 113)                           # REF3040
at('C44', 44.0, 116.6)
at('C45', 47.5, 113, 90)
at('U44', 55.0, 117, 90)                       # MCP3208: CH0-7 down
at('C50', 63.0, 117, 90)
at('U45', 100.0, 116)                          # DAC7568
at('C51', 106.0, 116, 90)
at('C52', 94.0, 116, 90)
at('R34', 100.0, 120.3)
at('U46', 115.0, 116.5, 90)                      # LM324, channels 1-4
at('C53', 121.5, 116.5, 90)
at('U47', 165.0, 116.5, 90)                      # LM324, channels 5-8
at('C54', 171.5, 116.5, 90)

# Channel cells above the bottom terminals: AI cells 11 mm wide from x 2,
# AO cells 12.5 mm wide from x 91, rows from y 123 down to the terminals.
AI_W, AO_W, CELL_Y = 11.0, 12.5, 123.0
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
at('C61', 203.0, 116, 90)
at('R50', 212.0, 116, 90)
at('C63', 222.0, 115.5)
at('C64', 222.0, 118)
at('R52', 210.0, 126, 90)
at('R53', 213.0, 126, 90)
at('R54', 218.0, 126, 90)
at('JP3', 222.5, 126)
at('D7', 205.0, 126)

for _p in PARTS:
    if _p['ref'] not in PLACE:
        raise SystemExit('no placement for ' + _p['ref'])
    _p['x'], _p['y'], _p['rot'] = PLACE[_p['ref']]
