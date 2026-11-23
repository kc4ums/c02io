"""Build c02io.kicad_pcb from board.py (run with KiCad's Python).

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" mk_pcb.py

Writes:
  c02io.kicad_pro    project: JLCPCB 4-layer rules and net classes
  c02io.kicad_dru    custom rules (PE clearance)
  fp-lib-table       the project footprint library (c02io.pretty)
  c02io.kicad_pcb    4 layers. Parts placed and connected (ratsnest), outline,
                     terminal labels, and per area:
                       In1.Cu  ground plane (GND, 0V_IO, AGND_ISO, GND_485)
                       In2.Cu  routing + power pours (24V_IO plane; +5V, +24VA, +5V_485 poured after routing)
                     Keep-out strips over the 3 mm gaps between the areas:
                     no track, via or copper pour may cross them.
                     After routing, the outer layers get a ground pour per area.
  c02io.dsn          Specctra file for Freerouting (inner layers as planes)
If c02io.ses exists (Freerouting's result), its tracks are imported.
"""
import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board  # noqa: E402

NAME = 'c02io'
PCB = os.path.join(HERE, NAME + '.kicad_pcb')
PRO = os.path.join(HERE, NAME + '.kicad_pro')
DSN = os.path.join(HERE, NAME + '.dsn')
SES = os.path.join(HERE, NAME + '.ses')
FPDIR = r'C:\Program Files\KiCad\10.0\share\kicad\footprints'

MM = pcbnew.FromMM

PLANES = {                      # area: (In1.Cu ground, In2.Cu power)
    'field': ('0V_IO', '24V_IO'),
    'logic': ('GND', '+5V'),
    'analog': ('AGND_ISO', '+24VA'),
    'rs485': ('GND_485', '+5V_485'),
}
# In2.Cu is a routing layer as well as the power pours: only the field area's
# 24V_IO pour (heavy output current) goes to Freerouting as a plane; the other
# areas' power pours on In2 are added after routing, around the tracks.
PLANE_BEFORE_ROUTE = {'field'}
OUT_NETS = ['OUT%d' % n for n in range(1, 17)]
WIDE = ['24V_IO', '0V_IO', '24V_RAW', '24V_F', '+24V']


def netclass(name, width, clearance=0.2, via=0.6, drill=0.3, priority=0):
    return {'name': name, 'clearance': clearance, 'track_width': width, 'via_diameter': via,
            'via_drill': drill, 'wire_width': 6, 'bus_width': 12, 'line_style': 0,
            'schematic_color': 'rgba(0, 0, 0, 0.000)', 'pcb_color': 'rgba(0, 0, 0, 0.000)',
            'diff_pair_gap': 0.25, 'diff_pair_via_gap': 0.25, 'diff_pair_width': 0.2,
            'microvia_diameter': 0.3, 'microvia_drill': 0.1, 'priority': priority}


def write_project():
    """JLCPCB 4-layer standard: 0.09 mm track, 0.3 mm drill. Tracks are 0.2 mm or
    more except Freerouting's short 0.1 mm neck-downs at fine-pitch pads."""
    pats = ([{'netclass': 'Supply', 'pattern': n} for n in sorted(board.POWER_NETS - set(WIDE) - {'PE'})]
            + [{'netclass': 'Field', 'pattern': n} for n in WIDE]
            + [{'netclass': 'Output', 'pattern': n} for n in OUT_NETS]
            + [{'netclass': 'PE', 'pattern': 'PE'}])
    pro = {
        'board': {'design_settings': {
            'rules': {'min_clearance': 0.15, 'min_track_width': 0.1, 'min_via_diameter': 0.5,
                      'min_via_annular_width': 0.1, 'min_through_hole_diameter': 0.3,
                      'min_copper_edge_clearance': 0.3, 'min_hole_clearance': 0.25,
                      'min_hole_to_hole': 0.25, 'min_resolved_spokes': 1,
                      'min_text_height': 0.6, 'min_text_thickness': 0.1},
            'track_widths': [0.0, 0.2, 0.3, 0.5, 0.8, 1.5, 2.5],
            'via_dimensions': [{'diameter': 0.0, 'drill': 0.0}, {'diameter': 0.6, 'drill': 0.3},
                               {'diameter': 1.0, 'drill': 0.5}],
        }},
        'net_settings': {
            'classes': [netclass('Default', 0.2, priority=2147483647),
                        netclass('Supply', 0.5, via=0.8, drill=0.4),
                        netclass('Output', 0.8, via=1.0, drill=0.5),
                        netclass('Field', 1.5, via=1.0, drill=0.5),
                        netclass('PE', 0.8, clearance=1.0, via=1.0, drill=0.5)],
            'netclass_patterns': pats,
            'meta': {'version': 4},
        },
        'meta': {'filename': NAME + '.kicad_pro', 'version': 3},
    }
    with open(PRO, 'w') as f:
        json.dump(pro, f, indent=2)
    with open(os.path.join(HERE, NAME + '.kicad_dru'), 'w') as f:
        f.write('(version 1)\n'
                '(rule "pe_clearance"\n'
                '  (condition "A.NetName == \'PE\' && B.NetName != \'PE\'")\n'
                '  (constraint clearance (min 1.0)))\n')
    with open(os.path.join(HERE, 'fp-lib-table'), 'w') as f:
        f.write('(fp_lib_table\n  (version 7)\n'
                '  (lib (name "c02io")(type "KiCad")(uri "${KIPRJMOD}/c02io.pretty")(options "")(descr "C02IO project footprints"))\n'
                ')\n')


def load_fp(key):
    lib, name = board.FP[key].split(':')
    d = os.path.join(HERE, 'c02io.pretty') if lib == 'c02io' else os.path.join(FPDIR, lib + '.pretty')
    fp = pcbnew.FootprintLoad(d, name)
    if fp is None:
        raise SystemExit('footprint not found: ' + board.FP[key])
    return fp


def text(b, s, x, y, size=1.0, layer=pcbnew.F_SilkS, angle=0):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s)
    t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(max(0.1, size * 0.15)))
    if angle:
        t.SetTextAngleDegrees(angle)
    b.Add(t)


def rect_outline(z, x0, y0, x1, y1):
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(MM(x), MM(y))


def zone(b, layer, net, rect, m=0.5):
    """A copper pour over one area's rectangle, pulled in m mm from its edges."""
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetLocalClearance(MM(0.3))
    z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.4))
    z.SetThermalReliefSpokeWidth(MM(0.5))
    x0, y0, x1, y1 = rect
    rect_outline(z, max(x0, m), max(y0, m), min(x1, board.BOARD_W - m), min(y1, board.BOARD_H - m))
    b.Add(z)


def keepout(b, rect, name):
    """Rule area on every copper layer: no tracks, vias or pours. Parts may straddle it."""
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetLayerSet(pcbnew.LSET.AllCuMask())
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    rect_outline(z, *rect)
    b.Add(z)


def gaps():
    """The 3 mm strips between the areas."""
    W, H, G = board.BOARD_W, board.BOARD_H, board.GAP
    return [((0, board.Y_FIELD, W, board.Y_FIELD + G), 'gap field/logic'),
            ((0, board.Y_LOW, W, board.Y_LOW + G), 'gap logic/analog+RS-485'),
            ((board.X_485, board.Y_LOW + G, board.X_485 + G, H), 'gap analog/RS-485')]


def labels(b):
    """Terminal pin names, in the strip between each terminal and the parts."""
    B = board.BOARD_H
    for ref, y, size in (('J2', 11.85, 0.8), ('J3', 11.85, 0.8), ('J4', 11.85, 0.8), ('J5', 11.85, 0.8),
                         ('J6', B - 11.75, 0.8), ('J7', B - 11.75, 0.8), ('J8', B - 11.75, 0.8),
                         ('J9', B - 11.75, 0.8)):
        p = board.P_BY_REF[ref]
        step = -3.81 if p['rot'] == 180 else 3.81
        for k in sorted(p['pins'], key=int):
            net = p['pins'][k]
            s = {'24V_SNS': '24V', '0V_IO': '0V', '24V_IO': '24V', 'AGND_ISO': '0V', 'GND_485': '0V',
                 'RS485_A': 'A', 'RS485_B': 'B'}.get(net)
            if s is None:
                s = net.replace('OUT', '').replace('DI', '').replace('AOC', 'C').replace('AO', 'O').replace('AI', '')
            text(b, s, p['x'] + step * (int(k) - 1), y, size)
    # J1 on the left edge, pins going down
    p = board.P_BY_REF['J1']
    for k, s in (('1', '+24V'), ('2', '0V'), ('3', 'PE')):
        text(b, s, 13.3, p['y'] + 3.81 * (int(k) - 1), 0.8)
    text(b, 'C02IO  CM5 I/O  rev B', 105.0, 36.0, 1.5)
    text(b, 'KC4UMS  2026', 105.0, 39.0, 1.0)
    text(b, 'FIELD 24 V (0V_IO)', 105.0, 43.0, 1.0)
    text(b, 'ANALOG (isolated)', 140.0, 110.5, 1.0)
    text(b, 'AO jumpers: 1-3 + 2-4 = 0-10 V,  3-5 + 4-6 = 4-20 mA', 140.0, 113.0, 0.8)
    text(b, 'AI jumper fitted = 4-20 mA', 140.0, 115.0, 0.8)
    text(b, 'RS-485', 212.0, 135.0, 1.0)
    text(b, 'TERM', 222.5, 122.0, 0.7)
    text(b, 'ETH', 216.0, 61.5, 0.8)
    text(b, 'USB-C (flash)', 214.0, 82.6, 0.7)
    text(b, 'RPIBOOT', 138.0, 95.5, 0.7)
    text(b, 'POWER', 7.0, 59.5, 0.7)


def build():
    write_project()
    b = pcbnew.NewBoard(PCB)
    b.SetCopperLayerCount(4)
    b.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    b.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_MIXED)
    ds = b.GetDesignSettings()
    ds.m_CopperEdgeClearance = MM(0.3)

    r = pcbnew.PCB_SHAPE(b)
    r.SetShape(pcbnew.SHAPE_T_RECT)
    r.SetStart(pcbnew.VECTOR2I(0, 0))
    r.SetEnd(pcbnew.VECTOR2I(MM(board.BOARD_W), MM(board.BOARD_H)))
    r.SetLayer(pcbnew.Edge_Cuts)
    r.SetWidth(MM(0.1))
    b.Add(r)

    netinfo = {}
    for name in sorted(board.nets()):
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
        netinfo[name] = n

    for p in board.PARTS:
        fp = load_fp(p['fp'])
        fp.SetReference(p['ref'])
        fp.SetValue(p['value'])
        fp.SetPosition(pcbnew.VECTOR2I(MM(p['x']), MM(p['y'])))
        if p['rot']:
            fp.SetOrientationDegrees(p['rot'])
        if p['dnp']:
            fp.SetDNP(True)
            fp.SetExcludedFromBOM(True)
        for pad in fp.Pads():
            net = p['pins'].get(pad.GetNumber())
            if net:
                pad.SetNet(netinfo[net])
        small = p['fp'] in ('R', 'C', 'R0805', 'C0805', 'LED', 'SOT23', 'SOD123', 'F1206')
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.6 if small else 0.9), MM(0.6 if small else 0.9)))
        fp.Reference().SetTextThickness(MM(0.1 if small else 0.14))
        fp.Value().SetLayer(pcbnew.F_Fab)
        if p['fp'].startswith('HOLE'):
            fp.Reference().SetVisible(False)
        b.Add(fp)

    # LMR36520 exposed pad: six 0.3 mm vias to the GND plane (the library's
    # thermal-via footprint uses 0.2 mm drills, below JLCPCB's standard)
    u = board.P_BY_REF['U13']
    for dx in (-0.6, 0.6):
        for dy in (-1.0, 0.0, 1.0):
            rx, ry = board.rotate(dx, dy, u['rot'])
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(MM(u['x'] + rx), MM(u['y'] + ry)))
            v.SetDrill(MM(0.3))
            v.SetWidth(MM(0.6))
            v.SetNet(netinfo['GND'])
            b.Add(v)

    # split ground planes on In1, one per area; the field area's 24V_IO on In2
    for area, (gnd, pwr) in PLANES.items():
        for rect in board.AREA_RECTS[area]:
            zone(b, pcbnew.In1_Cu, netinfo[gnd], rect)
            if area in PLANE_BEFORE_ROUTE:
                zone(b, pcbnew.In2_Cu, netinfo[pwr], rect)
    for rect, name in gaps():
        keepout(b, rect, name)
    labels(b)
    pcbnew.SaveBoard(PCB, b)


def late_pours(b, outer):
    """The other areas' power pours on In2 and, after routing, a ground pour
    per area on both outer layers."""
    for area, (gnd, pwr) in PLANES.items():
        for rect in board.AREA_RECTS[area]:
            if area not in PLANE_BEFORE_ROUTE:
                zone(b, pcbnew.In2_Cu, b.FindNet(pwr), rect)
            if outer:
                for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                    zone(b, layer, b.FindNet(gnd), rect)


VIA_DRILL = {0.6: 0.3, 0.8: 0.4, 1.0: 0.5}


def tidy_routes(b):
    """The .ses import gives every via its net class drill whatever its
    size (0.6 mm vias on OUT nets got 0.5 mm drills). Freerouting also necks
    some tracks down to 0.1 mm for a fraction of a mm between fine-pitch
    pads; that is allowed (JLCPCB 4-layer minimum 0.09 mm)."""
    nv = 0
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            d = VIA_DRILL.get(round(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)), 2))
            if d and abs(pcbnew.ToMM(t.GetDrillValue()) - d) > 1e-3:
                t.SetDrill(MM(d))
                nv += 1
    print('fixed %d via drills' % nv)


def main():
    build()
    b = pcbnew.LoadBoard(PCB)                   # with the project's net classes
    if os.path.exists(SES):
        if not pcbnew.ImportSpecctraSES(b, SES):
            raise SystemExit('could not import ' + SES)
        print('imported tracks from', os.path.basename(SES))
        tidy_routes(b)
        late_pours(b, outer=True)
    else:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        if not pcbnew.ExportSpecctraDSN(b, DSN):
            raise SystemExit('could not write ' + DSN)
        late_pours(b, outer=False)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    print('%s: %d parts, %d nets, %d pads, %.0f x %.0f mm, 4 layers' % (
        os.path.basename(PCB), len(board.PARTS), len(board.nets()),
        sum(len(v) for v in board.nets().values()), board.BOARD_W, board.BOARD_H))


if __name__ == '__main__':
    main()
