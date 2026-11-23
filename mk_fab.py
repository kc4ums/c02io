"""Route (optional), check and export the C02IO board for ordering.

    python mk_fab.py                     DRC + Gerbers/drill zip (board must be routed)
    python mk_fab.py --route [EXE]       first autoroute with Freerouting
    python mk_fab.py --route --passes 3  a short trial route (to see that it runs)

EXE defaults to Freerouting 2.5.0's installed freerouting.exe. Run the
routing from a normal PowerShell window, not inside Claude Code: it takes
a long time and a lot of memory.

Steps:
  1. (--route) mk_pcb.py writes c02io.dsn; Freerouting writes c02io.ses;
     mk_pcb.py builds the board again, imports the tracks and adds the
     ground pours on the outer layers. Freerouting's output goes to
     route_log.txt as well as the screen.
  2. kicad-cli DRC (errors only): must show no errors and no unconnected
     pads. The report goes to drc.txt.
  3. Gerbers (4 copper layers) and Excellon drill into fab/, zipped as
     fab/c02io_gerbers.zip.
The BOM and pick-and-place files for JLCPCB assembly come later, once the
LCSC part numbers are chosen.
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD = r'C:\Program Files\KiCad\10.0\bin'
CLI = os.path.join(KICAD, 'kicad-cli.exe')
KPY = os.path.join(KICAD, 'python.exe')
FREEROUTING = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'freerouting', 'freerouting.exe')
NAME = 'c02io'
PCB = os.path.join(HERE, NAME + '.kicad_pcb')
FAB = os.path.join(HERE, 'fab')


def run(*cmd, log=None):
    print('>', ' '.join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd)), flush=True)
    if log is None:
        r = subprocess.run(cmd, cwd=HERE)
        code = r.returncode
    else:
        with open(log, 'w', encoding='utf-8') as f:
            p = subprocess.Popen(cmd, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding='utf-8', errors='replace')
            for line in p.stdout:
                sys.stdout.write(line)
                f.write(line)
            code = p.wait()
    if code:
        sys.exit('failed: %s' % os.path.basename(cmd[0]))


def route(exe, passes):
    for f in (NAME + '.ses', NAME + '.dsn'):
        if os.path.exists(os.path.join(HERE, f)):
            os.remove(os.path.join(HERE, f))
    run(KPY, 'mk_pcb.py')                                   # writes the .dsn
    cmd = ['java', '-jar', exe] if exe.lower().endswith('.jar') else [exe]
    run(*cmd, '-de', NAME + '.dsn', '-do', NAME + '.ses', '-mp', str(passes), '-mt', '2',
        '--gui.enabled=false', log=os.path.join(HERE, 'route_log.txt'))
    if not os.path.exists(os.path.join(HERE, NAME + '.ses')):
        sys.exit('Freerouting wrote no %s.ses (see route_log.txt)' % NAME)
    run(KPY, 'mk_pcb.py')                                   # imports the .ses, adds the pours


def drc():
    rpt = os.path.join(HERE, 'drc.txt')
    subprocess.run([CLI, 'pcb', 'drc', '--severity-error', '--output', rpt, PCB], cwd=HERE,
                   capture_output=True)
    text = open(rpt, encoding='utf-8', errors='replace').read()
    errs = re.search(r'\*\* Found (\d+) DRC violations', text)
    unc = re.search(r'\*\* Found (\d+) unconnected pads', text)
    n_err = int(errs.group(1)) if errs else len(re.findall(r'^\[', text, re.M))
    n_unc = int(unc.group(1)) if unc else text.count('[unconnected_items]')
    kinds = {}
    for k in re.findall(r'^\[(\w+)\]', text, re.M):
        kinds[k] = kinds.get(k, 0) + 1
    print('DRC: %d errors, %d unconnected pads %s (details in drc.txt)' % (n_err, n_unc, kinds or ''))
    return n_err == 0 and n_unc == 0


def gerbers():
    os.makedirs(FAB, exist_ok=True)
    for f in glob.glob(os.path.join(FAB, '*')):
        os.remove(f)
    run(CLI, 'pcb', 'export', 'gerbers', '--output', FAB + os.sep, '--layers',
        'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts',
        '--subtract-soldermask', PCB)
    run(CLI, 'pcb', 'export', 'drill', '--output', FAB + os.sep, '--format', 'excellon',
        '--excellon-separate-th', '--generate-map', '--map-format', 'pdf', PCB)
    z = os.path.join(FAB, NAME + '_gerbers.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(glob.glob(os.path.join(FAB, '*'))):
            if not f.endswith(('.zip', '.pdf')):
                zf.write(f, os.path.basename(f))
    print('wrote', os.path.relpath(z, HERE))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--route', nargs='?', const=FREEROUTING, metavar='EXE',
                    help='autoroute first, with freerouting.exe or a Freerouting .jar')
    ap.add_argument('--passes', type=int, default=40, help='maximum routing passes (default 40)')
    a = ap.parse_args()
    if a.route:
        route(a.route, a.passes)
    if not drc():
        sys.exit('fix the DRC report before ordering (is the board routed?)')
    gerbers()


if __name__ == '__main__':
    main()
