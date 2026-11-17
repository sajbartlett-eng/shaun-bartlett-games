"""Step 19: one table from a ux_capture.js measures file, and resized copies of the key screens for the report.

python3 tools/ux_summary.py <capture folder> <out folder> [key screen names...]"""
import json
import os
import subprocess
import sys

KEY = ['laptop_01_start', 'laptop_03_path_computer', 'laptop_13_table_start', 'laptop_14_piece_selected', 'laptop_15_pass_choice',
       'laptop_16_coverage', 'laptop_21_end_dialog', 'phone_01_start', 'phone_13_table_start', 'phone_14_piece_selected',
       'phone_15_pass_choice', 'phone_21_end_dialog']


def rows(m):
    out = {}
    for k, v in m.items():
        if not isinstance(v, dict) or 'axe' not in v:
            continue
        sz = v['textSizes_px_by_characters']
        tot = sum(sz.values()) or 1
        small = sum(c for s, c in sz.items() if int(s) < 14)
        out[k] = dict(note=v['note'], axe=[a['id'] for a in v['axe']], words=v['wordsOnScreen'], under14=round(100 * small / tot),
                      targets=v['smallTargetCount'], height=v['pageHeight'], hscroll=v['horizontalScroll'])
    return out


def main(src, dst, keys):
    m = json.load(open(os.path.join(src, 'measures.json')))
    os.makedirs(dst, exist_ok=True)
    r = rows(m)
    json.dump(r, open(os.path.join(dst, 'summary.json'), 'w'), indent=1)
    lines = ['| Screen | What it shows | axe issues | Words | Text under 14 px | Targets under 44 px | Page height (px) |', '|---|---|---|---|---|---|---|']
    for k, v in r.items():
        lines.append(f"| {k} | {v['note']} | {', '.join(v['axe']) or '0'} | {v['words']} | {v['under14']}% | {v['targets']} | {v['height']} |")
    open(os.path.join(dst, 'summary.md'), 'w').write('\n'.join(lines) + '\n')
    for k in keys or KEY:
        f = os.path.join(src, 'screens', k + '.png')
        if os.path.exists(f):
            subprocess.run(['convert', f, '-resize', '900x>', '-crop', 'x2600+0+0', '+repage', '-strip', os.path.join(dst, k + '.png')], check=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
