# C02IO: W65C02S industrial I/O board (design spec)

Status: **netlist written and checked (2026-11-20).** `board.py` has every part, footprint and pin connection; `python check_board.py` passes. Every chip's pin table was checked against its current datasheet (listed at the top of `board.py`). **Placed (2026-11-23):** every part has its position and rotation in `board.py`, and `python check_place.py png` passes (no courtyard overlaps; every part inside its isolated area; every bridge pad on the right side of its gap). `place.png` shows it. The KiCad board and schematic (`mk_pcb.py`, `mk_sch.py`, as in C02COMM at `C:\Projects\mymensch\hardware\c02board`) are next.

![placement](place.png)

The datasheet check changed a few things in this spec; see **Changes from the datasheet check** below.

This is a small PLC-style controller:
- 16 opto-isolated 24 V digital inputs
- 16 opto-isolated 24 V sourcing outputs, 0.5 A each
- 8 analog inputs and 8 analog outputs, each set to 0-10 V or 4-20 mA with a jumper, isolated as a group
- isolated RS-485 (Modbus RTU) and a USB-serial header

## Choices made (2026-11-20)

| | Choice | Why |
|---|---|---|
| CPU | **W65C02S**, DIP-40 in a socket | The W65C134S PLCC-68 is end-of-life, and no distributor stocks the QFP-80. The W65C02S is in stock and is the same core C02COMM uses, so its decode, memory map and software carry over. |
| Build | **SMD, assembled by JLCPCB** | JLCPCB fits everything except the WDC chips' sockets, the flash socket and the terminal headers, which are through-hole parts you solder. |
| Analog | **0-10 V or 4-20 mA, one jumper per channel** | Analog inputs use a 2-pin jumper, analog outputs a 2x3 header with two shunts. |
| Outputs | **Sourcing (high-side), 0.5 A, short-circuit protected** | The standard for PLCs driving relays, valves and lamps. |
| Comms | **Isolated RS-485, USB-serial header, LEDs on every I/O** | |
| Analog isolation | **Yes, as one group** | The analog section has its own isolated 24 V supply and ground, and talks to the CPU through digital isolators. The channels share that ground with each other. |
| Layers | **4** | GND and power planes, which helps the analog section. |

## Block diagram

```
 FOUR ISOLATED AREAS: logic (GND), field digital (0V_IO), analog (AGND_ISO), RS-485 (GND_485)

 24V IN --fuse--diode--TVS--+-- LMR36520 buck --> +5V (logic)
                            +-- URB2424YMD-6WR3 isolated DC-DC --> +24VA, AGND_ISO
                                    +24VA --> 78L05 --> +5VA --> REF3040 (4.096 V)

 W65C02S --+-- 32K RAM, 128K flash (4 banks), same as C02COMM
           |                                                  || FIELD DIGITAL (0V_IO)
           +-- 74HC541 x2 <-- pull-ups <---- TLP291-4 x4 <----||---- 16 inputs (LED + opto per input)
           +-- 74HC574 x2 --> R --> LED of -- TLP291-4 x4 ----||---> VNI4140K x4 --> 16 outputs, LED each
           |      ^ /OE = NAND(VIA PB0, watchdog OK)          ||      STATUS (wire-OR) --> opto --> VIA PB4
           |                                                  ||  24V_IO IN --> VNI4140K, 78L05 (+5V_IO); --PTC-->
           |                                                  ||                       sensor supply terminals
           +-- TL16C2552 dual UART -- A --> CA-IS3082WX ------||---- RS-485 A/B (GND_485, from B0505XT)
           |                       -- B --> FTDI 6-pin header
           +-- W65C22 VIA -- SPI --> ISO7741 + ISO7720 -------|| ANALOG (AGND_ISO)
                                                              ||-- MCP3208 ADC <-- 8 x (divider, 499R mA jumper, PTC, TVS)
                                                              ||-- DAC7568A --> 8 x (LM324 + NPN, V/I jumper) --> AO
```

Each area has its own ground. Only optocouplers, digital isolators, the isolated DC-DC converters and the isolated RS-485 chip cross between them. The 8 analog channels are isolated from the logic, the field I/O and the power input, but not from each other: they share AGND_ISO.

## Memory map (same layout as C02COMM)

| Address | Device |
|---|---|
| `$0000-$7EFF` | RAM, 32 KB SRAM |
| `$7F00-$7F0F` | VIA, W65C22N: SPI to the ADC/DAC, flash bank, output enable, watchdog, LEDs |
| `$7F10-$7F1F` | UART, TL16C2552: A0-A2 select the register, A3 the channel (`$7F10` = B, USB; `$7F18` = A, RS-485) |
| `$7F20` | Inputs 1-8 (74HC541, read) |
| `$7F30` | Inputs 9-16 (74HC541, read) |
| `$7F40` | Outputs 1-8 (74HC574, write) |
| `$7F50` | Outputs 9-16 (74HC574, write) |
| `$7F60`, `$7F70` | `/CS6`, `/CS7` on the expansion header (2x16: +5V, GND, D0-D7, A0-A3, RW, PHI2, `/RD`, `/WR`, `/IRQ`, `/RES`, `/NMI`, `/CS6`, `/CS7`, PB6, PB7, CA1, CA2, CB1, CB2) |
| `$8000-$FFFF` | Flash, SST39SF010A, one of four 32 KB banks (VIA PA6/PA7) |

The decode is C02COMM's: a 74HC30 for `$7Fxx`, a 74HC138 on A4-A6, and 74HC00 strobes. Each 74HC541 is enabled by its chip select **and** `/RD`. Each 74HC574 clocks on `OR(/CSn, /WR)`, from a 74HC32. Reading or writing one address moves 8 channels in one instruction.

**Clock:** one 3.6864 MHz oscillator drives PHI2 and the UART's XTAL1. 9600 baud is divisor 24.

## VIA pins

| Pin | Use |
|---|---|
| PA0, PA1, PA2 | SPI SCLK, MOSI, MISO (bit-banged, through the digital isolators) |
| PA3 | ADC `/CS` |
| PA4 | DAC `/SYNC` |
| PA5 | DAC `/LDAC`: updates all 8 outputs at once |
| PA6, PA7 | Flash bank, pulled low (bank 0 at reset) |
| PB0 | Output enable, pulled low. **The outputs stay off until software sets this.** |
| PB1 | Watchdog kick (74HC123: if not toggled for ~100 ms, the outputs drop) |
| PB2, PB3 | RUN and FAULT LEDs |
| PB4 | Output fault in (any VNI4140K over-temperature), through an opto |
| PB5 | Field power present (24V_IO), through an opto |
| PB6, PB7, CA1, CA2, CB1, CB2 | Expansion header (PB7 = Timer 1 output) |

**RS-485 direction:** the UART's channel-A `/RTS`, inverted by a 74HC00 gate, drives DE and `/RE`. Setting MCR RTS transmits. After reset `/RTS` is high, so the transceiver receives and never drives the bus.

**UART interrupts:** INTA and INTB are active high and 3-state until MCR OUT2 is set, so each one pulls `/IRQ` low through a BC847, with a pull-down on the INT line. Software must set OUT2 to use interrupts.

## Circuits

**Digital input (x16), IEC 61131-2 type 1/3 style:**
- **Signal path:** terminal → 4.7k (1206) → green LED → opto LED, with 2.2k and 10 nF across the opto LED, then → 0V_IO. An antiparallel 1N4148W protects against reverse voltage.
- **Thresholds:** about 1.7 mA at 11 V reads ON. 5 V stays OFF, because the shunt keeps the opto LED below its threshold. 30 V draws 5.7 mA.
- **Logic side:** the opto transistor pulls the input low against a 22k pull-up, and the 74HC541 reads it. Software inverts the reading, so 1 = ON.
- **Wiring:** sourcing (PNP) sensors connect between 24V_IO and the input. 0V_IO is the common.

**Digital output (x16):**
- **Signal path:** 74HC574 → 1k → opto LED. The opto transistor drives the VNI4140K input from +5V_IO, with a 10k pull-down.
- **Driver:** the VNI4140K is a quad high-side switch: 3.3 V CMOS inputs, 0.6 A per channel in the current datasheet (0.7 A in older ones), current limiting and per-channel thermal shutdown.
- **Indication:** a yellow LED and 4.7k from each output to 0V_IO light when the output is on.
- **Faults:** each VNI4140K has one open-drain STAT pin per channel. All 16 are wire-ORed through one opto to VIA PB4. STAT goes low **only on over-temperature** (with IN high), not while the output is current-limiting a short.
- **Supply:** the VNI4140K's exposed slug is **Vcc** (24V_IO), not ground. 24V_IO feeds the four drivers directly (up to 8 A with all outputs on), so **fuse the field supply outside the board**. A reversed field supply is shorted by the SMBJ33A, which must blow that fuse.
- **Start-up and crashes:** the 74HC574s have no reset. Their `/OE` is held high (outputs off) until software has written the latches and set PB0. It also goes high if the watchdog times out.

**Analog isolation:**
- **Power:** a Mornsun URB2424YMD-6WR3 (9-36 V in, isolated 24 V out, 6 W) makes +24VA on AGND_ISO. A 78L05 makes +5VA for the ADC, DAC and isolators' analog side, and a REF3040 makes the 4.096 V ADC reference.
- **Budget:** 8 outputs at 20 mA from 24 V is about 4 W, plus about 0.5 W for the rest, so the 6 W converter runs at about 75 %.
- **SPI:** an ISO7741 (3 channels to the analog side, 1 back) carries SCLK, MOSI, ADC `/CS` and MISO. An ISO7720 (2 channels) carries DAC `/SYNC` and `/LDAC`. Use the default-high versions, so the chip selects sit inactive while the logic side is unpowered. The SPI is bit-banged slowly, so isolator speed doesn't matter.

**Analog input (x8):**
- **Signal path:** terminal → PTC (50 mA hold) → SMAJ12A TVS to AGND_ISO → 15k/10k divider (10 V → 4.0 V) → 1k → ADC, with 100 nF and BAV99 clamps to +5VA/AGND_ISO.
- **4-20 mA:** a jumper puts **499 Ω (2010, 0.5 W)** across the input, so 20 mA reads about 9.8 V. Software calibrates it, and a table in software says which channels are mA.
- **ADC:** MCP3208, 12-bit, with a 4.096 V reference (REF3040), so the input range is 0-10.24 V.
- **Mistakes:** 24 V on an input trips the PTC into the TVS.

**Analog output (x8):**
- **DAC:** DAC7568**A**, 12-bit, 8 channels, internal 2.5 V reference, gain 1, so 0-2.5 V. The internal reference is **off at power-up and after a reset**: firmware must enable it. Its outputs drive an LM324 (2 chips, on +24VA), and the op-amp drives an NPN emitter follower (BCX56, SOT-89) from +24VA.
- **Current limit:** a 22 Ω resistor with a sensing transistor limits the output to about 26-29 mA.
- **2x3 jumper:** both shunts left = **0-10 V**: feedback from a 30k/10k divider on the terminal side of the PTC (gain 4), and COM tied to AGND_ISO. Both shunts right = **4-20 mA**: feedback from COM, which returns through a 124 Ω (0.1 %) sense resistor, so 2.5 V gives 20.2 mA.
- **Compensation:** 10k in series with the op-amp's inverting input and 10 nF from its output to that input, plus 10 nF on OUT. These are starting values to check in simulation.
- **Compliance:** about 900 Ω at 20 mA, from the isolated 24 V (only 2.5 V is lost in the sense resistor).
- **Protection:** a PTC and an SMAJ15A TVS at each terminal.
- **Wiring:** in mA mode the load goes between OUT and COM. In V mode, COM is 0 V (AGND_ISO).

**Power:**
- **Input:** 24 V nominal (18-32 V) → 2 A fuse → SS34 reverse diode → SMBJ33A TVS.
- **Regulators:** the LMR36520 (4.2-65 V, 2 A, HSOIC-8) makes the logic +5 V. The analog supply comes from its own isolated converter (see Analog isolation).
- **Field supply:** 24V_IO is a separate pair of terminals. It can come from the same supply, but isolation only helps if it doesn't.

**RS-485:**
- **Chips:** CA-IS3082WX (isolated transceiver, SOIC-16 wide), powered on the bus side by a B0505XT-1WR3 (SMD) isolated DC-DC converter. The converter needs a 20 mA minimum load, so a 330 Ω resistor (15 mA) sits across its output.
- **Bus side:** a 120 Ω termination jumper (JP3), 680 Ω bias resistors, and an SM712 TVS on A/B.

## Terminals

Pluggable 3.81 mm blocks along the two long edges (headers on the board, plugs in the BOM):

Phoenix MC 1,5/x-G-3.81 headers go up to 16 pins, so the groups are split:

| Ref | Pins | Order |
|---|---|---|
| J2, J3 | 10 each | IN1-IN8 (IN9-IN16), 24V sensor supply (through a 0.5 A PTC), 0V_IO |
| J4 | 10 | OUT1-OUT8, 24V_IO in, 0V_IO in |
| J5 | 10 | OUT9-OUT16, 0V_IO, 0V_IO (load return) |
| J6 | 12 | AI1, AI2, 0V, AI3, AI4, 0V, ... AI7, AI8, 0V |
| J7 | 8 | OUT1, COM1 ... OUT4, COM4 |
| J8 | 9 | OUT5, COM5 ... OUT8, COM8, 0V |
| J1 | 3 | +24 V, 0 V, PE |
| J9 | 3 | A, B, GND_485 |

## Board

- **Size and layers:** **230 x 147 mm**, **4 layers** (GND and power planes; better for the analog section, and cheap at JLCPCB now). The spec guessed 200 x 120; the placement needs more. The 32 field channels sit at the terminals' 3.81 mm pitch, about 45 mm deep with their optos. Each analog channel needs a cell 11 mm (input) or 12.5 mm (output) wide and about 22 mm deep.
- **Bands, top to bottom:** field digital (terminals on the top edge), logic (CPU row; 24 V input on the left edge), then analog (terminals on the bottom edge) with RS-485 in the bottom-right corner. The optos, isolators, DC-DC converters and the RS-485 chip straddle the 3 mm gaps between them.
- **Isolation:** four copper areas (logic, field digital, analog, RS-485), each with its own planes on all 4 layers. A ≥3 mm gap separates them, crossed only under the optos, digital isolators, DC-DC converters and the RS-485 chip.
- **B0505XT orientation:** its output 0V (pin 4) is in the same row as the input pins 1 and 2, so its barrier runs between pins 2 and 4, not between the rows. It is turned 270 degrees with the gap between pins 2 and 4. Pin 8 (NC, "isolated from circuitry") ends up on the logic side: leave it unconnected with plane clearance around it.
- **Mounting:** 4 M3 holes, at the left and right edges of the logic band and in the bottom corners. H1 is plated and on PE, with 1 nF 2 kV from PE to logic 0 V. The others are bare. A DIN-rail mount can clip onto the holes.

## Cost notes

- **JLCPCB assembly:** 475 SMD parts of 75 types (513 parts in all). Each JLCPCB *extended* part type adds a ~$3 loading fee, and most of the ICs here are extended. The WDC chips aren't stocked by JLCPCB, and neither are some of the others: the VNI4140K, TL16C2552, CA-IS3082WX, ISO7741/ISO7720 and B0505XT-1WR3 need checking in JLCPCB's library. Missing ones can be bought through JLCPCB's global sourcing or soldered by you.
- **Analog isolation** adds roughly $15-20 per board: the isolated converter (about $8-10) and the two digital isolators.
- **Hand-soldered by you:** the CPU and VIA sockets (DIP-40), the flash socket (PLCC-32), the URB2424YMD-6WR3 (through-hole, 25.4 mm square), and the terminal and pin headers.

## Changes from the datasheet check (2026-11-20)

| Was | Now | Why |
|---|---|---|
| DAC7568**C**, 0-5 V, 249 Ω sense, 10k/10k divider | DAC7568**A**, 0-2.5 V, 124 Ω sense, 30k/10k divider | The C grade gives 0-5 V only with AVDD 5.0-5.5 V; a 78L05 can be 4.75 V. |
| CA-IS3082W | CA-IS3082W**X** | The plain W part was dropped from the datasheet (v1.04/1.05). |
| B0505S-1WR3 (SIP-4) | B0505XT-1WR3 (SMD) + 330 Ω load | Same electrical part in SMD; 20 mA minimum load. |
| URB2424YMD-6WR3 assumed SMD | Through-hole, 25.4 mm | It is a DIP module; added to the hand-soldered list. |
| `RTS` drives DE and `/RE` directly | `/RTS` inverted first | Otherwise the transmitter is on after reset. |
| VNI4140K STATUS (one) | STAT1-4 per chip, all 16 wire-ORed | One per channel; over-temperature only. Slug is Vcc. |
| TLP291 singles for fault / field power | a ninth TLP291-4 (U35), 2 channels spare | The single TLP291 is "not recommended for new design". |
| UART INT to `/IRQ` | through BC847s | INTA/B are active high and 3-state until OUT2. |
| LMR36520 fixed 5 V | adjustable, 100k/24.9k | Rev. C lists no fixed version. Its pin table is the same as the 2020 one. |
| 74HC123 | CD74HC123, 100k/2.2 µF ≈ 100 ms (tW = 0.45 RC) | TI's 74HC123 is the CD74HC123. Kick it at least every 25 ms. |
| reset supervisor not chosen | DS1813R-10 (SOT-23) | Documented pushbutton input, 150 ms stretch. |

## Files

| File | What it is |
|---|---|
| `board.py` | **The design.** Every part, footprint, pin connection, position and rotation, and the isolated areas. Edit this, then regenerate the rest. |
| `check_board.py` | Plain Python. Checks the netlist: pinouts, buses, decoding, isolation, every channel. |
| `check_place.py` | Plain Python + matplotlib. Checks the placement and draws `place.png` (`python check_place.py png`). |
| `mk_fp.py` | Writes the two Mornsun footprints into `c02io.pretty`, from the datasheets' top-view layouts. |
| `fpgeom.py` | Reads courtyards and pads from the KiCad libraries; prints the `CRT` table in `board.py`. |

## Still to do

- **KiCad board and schematic:** `mk_pcb.py` (4 layers, per-area planes, net classes, JLCPCB rules), `mk_sch.py` (one sheet per block), then routing and `mk_fab.py` (Gerbers, BOM with LCSC numbers, pick-and-place file).
- **Datasheet details still open:**
  - **SST39SF010A:** only use the Rev F (May 2025) datasheet. It corrected the PLCC pin table.
  - **CJ78L05 (LCSC C2079):** the pin order (1 OUT, 2 GND, 3 IN) came from a mirror of JSCJ's datasheet; check it against LCSC's copy. The SOT-23 version has a different pinout.
  - **SM712, DS1813:** read from third-party copies of the manufacturer PDFs (Semtech 2017, Maxim 2006). Newer revisions weren't reachable.
  - **Oscillator:** `board.py` assumes the common 4-pad 7 x 5 mm layout (1 OE, 2 GND, 3 OUT, 4 VDD). Check it against the part chosen.
- **Stock:**
  - **TL16C2552FN:** listed as active by TI, but Mouser doesn't normally stock it. DigiKey had some.
  - **Fallbacks:** the SC16C2552B (discontinued) and XR16L2552 (obsolete) are ruled out. If the TL16C2552 can't be had, use two W65C51N chips (their transmit-empty flag is stuck).
  - **Also check:** JLCPCB/LCSC numbers for every SMD part, and choose the PTCs (50 mA hold, 30 V+, 1812; 0.5 A for the sensor supply).
- **Output stage stability:** simulate the op-amp, the emitter follower and a long cable with the compensation values in `board.py`.
- **Field supply current:** up to 8 A through J4 pin 9 and the 24V_IO copper with every output on. That is at the terminal's limit: size the copper for it, or split the supply across both DO blocks.
