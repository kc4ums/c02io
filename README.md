# C02IO: W65C02S industrial I/O board (design spec)

Status: **design spec only.** Nothing is generated yet. The next step is `board.py`, built the same way as C02COMM (`C:\Projects\mymensch\hardware\c02board`), with every pinout checked against its datasheet as it is written.

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
           |                                                  ||  24V_IO IN --PTC--> VNI4140K, 78L05 (+5V_IO),
           |                                                  ||                     sensor supply terminals
           +-- TL16C2552 dual UART -- A --> CA-IS3082W -------||---- RS-485 A/B (GND_485, from B0505S)
           |                       -- B --> FTDI 6-pin header
           +-- W65C22 VIA -- SPI --> ISO7741 + ISO7720 -------|| ANALOG (AGND_ISO)
                                                              ||-- MCP3208 ADC <-- 8 x (divider, 499R mA jumper, PTC, TVS)
                                                              ||-- DAC7568C --> 8 x (LM324 + NPN, V/I jumper) --> AO
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
| `$7F60`, `$7F70` | `/CS6`, `/CS7` on the expansion header |
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

**RS-485 direction:** the UART's channel-A `RTS` drives DE and `/RE`.

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
- **Faults:** the open-drain STATUS pins are wire-ORed through one opto to VIA PB4.
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
- **DAC:** DAC7568**C**, 12-bit, 8 channels, internal 2.5 V reference with gain 2, giving 0-5 V. Its outputs drive an LM324 (2 chips, on +24VA), and the op-amp drives an NPN emitter follower (BCX56, SOT-89) from +24VA.
- **Current limit:** a 22 Ω resistor with a sensing transistor limits the output to about 26-29 mA.
- **2x3 jumper:** both shunts left = **0-10 V**: feedback from a 10k/10k divider on OUT (gain 2), and COM tied to AGND_ISO. Both shunts right = **4-20 mA**: feedback from COM, which returns through a 249 Ω (0.1 %) sense resistor, so 5 V gives 20 mA.
- **Compliance:** about 850 Ω at 20 mA, from the isolated 24 V.
- **Protection:** a PTC and an SMAJ15A TVS at each terminal.
- **Wiring:** in mA mode the load goes between OUT and COM. In V mode, COM is 0 V (AGND_ISO).

**Power:**
- **Input:** 24 V nominal (18-32 V) → 2 A fuse → SS34 reverse diode → SMBJ33A TVS.
- **Regulators:** the LMR36520 (4.2-65 V, 2 A, HSOIC-8) makes the logic +5 V. The analog supply comes from its own isolated converter (see Analog isolation).
- **Field supply:** 24V_IO is a separate pair of terminals. It can come from the same supply, but isolation only helps if it doesn't.

**RS-485:**
- **Chips:** CA-IS3082W (isolated transceiver, SOIC-16 wide), powered on the bus side by a B0505S-1WR3 isolated DC-DC converter.
- **Bus side:** a 120 Ω termination jumper, bias resistors, and an SM712 TVS on A/B.

## Terminals

Pluggable 3.81 mm blocks along the two long edges (headers on the board, plugs in the BOM):

| Group | Pins |
|---|---|
| Digital inputs | 16 inputs, 2 x 24V_IO (sensor supply, PTC), 2 x 0V_IO |
| Digital outputs | 16 outputs, 2 x 0V_IO (load return), 24V_IO in, 0V_IO in |
| Analog inputs | 8 inputs, 4 x AGND_ISO |
| Analog outputs | 8 x OUT, 8 x COM, 1 x AGND_ISO |
| Power | 24 V, 0 V, PE |
| RS-485 | A, B, GND_485 |

## Board

- **Size and layers:** about **200 x 120 mm**, **4 layers** (GND and power planes; better for the analog section, and cheap at JLCPCB now).
- **Isolation:** four copper areas (logic, field digital, analog, RS-485), each with its own planes on all 4 layers. A ≥3 mm gap separates them, crossed only under the optos, digital isolators, DC-DC converters and the RS-485 chip.
- **Mounting:** 4 M3 holes. A DIN-rail mount can clip onto the holes.

## Cost notes

- **JLCPCB assembly:** about 350 SMD parts. Each JLCPCB *extended* part type adds a ~$3 loading fee, and most of the ICs here are extended. The WDC chips aren't stocked by JLCPCB, and neither are some of the others: the VNI4140K, TL16C2552, CA-IS3082W, ISO7741/ISO7720 and URB2424YMD-6WR3 need checking in JLCPCB's library. Missing ones can be bought through JLCPCB's global sourcing or soldered by you.
- **Analog isolation** adds roughly $15-20 per board: the isolated converter (about $8-10) and the two digital isolators.
- **Hand-soldered by you:** the CPU and VIA sockets (DIP-40), the flash socket (PLCC-32), and the terminal headers.

## To check before `board.py` is written

- **Pinouts** for each chip, from its datasheet: VNI4140K, DAC7568, TL16C2552 (PLCC-44), MCP3208 (confirmed: CH0-7 on 1-8, DGND 9, /CS 10, DIN 11, DOUT 12, CLK 13, AGND 14, VREF 15, VDD 16), LMR36520 (pin table taken from the 2020 datasheet revision; check it against Rev. C, Nov 2025), CA-IS3082W, TLP291-4, REF3040, 74HC123, ISO7741, ISO7720, URB2424YMD-6WR3.
- **Stock:**
  - **TL16C2552FN:** listed as active by TI, but Mouser doesn't normally stock it. DigiKey had some.
  - **Fallbacks:** the SC16C2552B (discontinued) and XR16L2552 (obsolete) are ruled out. If the TL16C2552 can't be had, use two W65C51N chips (their transmit-empty flag is stuck).
  - **Also check:** JLCPCB/LCSC numbers for every SMD part.
- **Output stage stability:** the op-amp plus emitter follower driving long cables. Add a compensation capacitor and a base resistor, and check them in a simulation.
