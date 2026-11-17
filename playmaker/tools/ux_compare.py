"""Step 19: the before-and-after tables from tools/ux_capture.js runs.

python3 tools/ux_compare.py <capture folder> [<capture folder> ...]   (labels are the folder names)"""
import json
import os
import sys

PLAY = ['13_table_start', '14_piece_selected', '15_pass_choice', '16_coverage', '18_contest', '19_step_bar', '21_end_dialog', '26_scenario_card']


def load(d):
    m = json.load(open(os.path.join(d, 'measures.json')))
    out = {}
    for k, v in m.items():
        if isinstance(v, dict) and 'axe' in v:
            sz = v['textSizes_px_by_characters']
            tot = sum(sz.values()) or 1
            out[k] = dict(axe=len(v['axe']), words=v['wordsOnScreen'], under14=100 * sum(c for s, c in sz.items() if int(s) < 14) / tot,
                          targets=v['smallTargetCount'], height=v['pageHeight'], hscroll=v['horizontalScroll'])
    return out


def summary(d):
    r = load(d)
    play = [r[f'{dev}_{k}'] for dev in ('laptop', 'phone') for k in PLAY if f'{dev}_{k}' in r]
    return dict(screens=len(r), axe_screens=sum(1 for v in r.values() if v['axe']), axe=sum(v['axe'] for v in r.values()),
                under14_play=round(sum(v['under14'] for v in play) / max(1, len(play))),
                phone_targets=round(sum(r[k]['targets'] for k in r if k.startswith('phone_')) / max(1, sum(1 for k in r if k.startswith('phone_'))), 1),
                phone_table=r.get('phone_13_table_start', {}).get('height'), start_words_laptop=r.get('laptop_03_path_computer', {}).get('words'),
                hscroll=sum(1 for v in r.values() if v['hscroll']))


if __name__ == '__main__':
    rows = [(os.path.basename(d.rstrip('/')), summary(d)) for d in sys.argv[1:]]
    keys = ['screens', 'axe_screens', 'axe', 'under14_play', 'phone_targets', 'phone_table', 'start_words_laptop', 'hscroll']
    print('| Capture | ' + ' | '.join(keys) + ' |')
    print('|' + '---|' * (len(keys) + 1))
    for name, s in rows:
        print(f'| {name} | ' + ' | '.join(str(s[k]) for k in keys) + ' |')
    json.dump({n: s for n, s in rows}, open('/dev/stdout', 'w') if False else open(os.devnull, 'w'))
