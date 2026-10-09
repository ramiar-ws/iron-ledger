import re, json, sys
from collections import Counter, OrderedDict
from datetime import date

RAW = open('raw-log.txt').read()
DAYS = r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
DATE_RE = re.compile(r'\b(\d{1,2})\.(\d{1,2})\b')
# a rep spec: 4*8, 4*8-10, 3*10, 4x*8-10, 4*810(typo), 4*12-10
REP_RE = re.compile(r'(\d{1,2})\s*x?\s*\*\s*(\d{1,3})(?:\s*-\s*(\d{1,2}))?')
WT_RE  = re.compile(r'(\d+(?:\.\d+)?)\s*(?:-|/)\s*(\d+(?:\.\d+)?)\s*kg|(\d+(?:\.\d+)?)\s*kg')

def is_header(line):
    return re.search(DAYS, line, re.I) is not None

# ---------- pass 1: split into session blocks ----------
blocks = []
cur = None
for line in RAW.split('\n'):
    s = line.strip()
    if not s or s == '/':
        continue
    if s.lower() == 'workout':
        continue
    if is_header(s):
        cur = {'hdr': s, 'lines': []}
        blocks.append(cur)
    elif cur is not None:
        cur['lines'].append(s)

print('session blocks:', len(blocks))

# ---------- pass 2: dates with year rollover + typo repair ----------
sessions = []
year = 2024
prev = None
for b in blocks:
    m = DATE_RE.search(b['hdr'])
    if not m:
        print('NO DATE:', b['hdr']); continue
    d, mo = int(m.group(1)), int(m.group(2))
    if prev and mo < prev[1] - 6:
        year += 1
    try:
        dt = date(year, mo, d)
    except ValueError:
        print('BAD DATE:', b['hdr']); continue
    b['date'] = dt
    b['rawmd'] = (d, mo)
    prev = (d, mo)
    sessions.append(b)

print('dated:', len(sessions), 'range:', sessions[0]['date'], '->', sessions[-1]['date'])
yrs = Counter(s['date'].year for s in sessions)
print('per year:', dict(sorted(yrs.items())))

# ---------- pass 3: exercises ----------
def split_fragments(line):
    """A line can hold several exercises: split after each complete rep spec."""
    out, last = [], 0
    for m in REP_RE.finditer(line):
        out.append(line[last:m.end()])
        last = m.end()
    tail = line[last:].strip()
    if tail:
        if out: out[-1] = out[-1] + ' ' + tail
        else: out.append(tail)
    return [f.strip() for f in out if f.strip()]

names = Counter()
for b in sessions:
    b['ex'] = []
    for line in b['lines']:
        for frag in split_fragments(line):
            rm = REP_RE.search(frag)
            nm = REP_RE.sub('', frag)
            wm = WT_RE.search(nm)
            nm = WT_RE.sub('', nm)
            nm = re.sub(r'>\s*', '', nm)
            nm = re.sub(r'\(.*?\)', '', nm)
            nm = re.sub(r'[~\-–]+\s*(tough|doable)?\s*$', '', nm, flags=re.I)
            nm = re.sub(r'\b(tough|doable)\b', '', nm, flags=re.I)
            nm = re.sub(r'[\s,+*]+$', '', nm).strip(' -–~/')
            nm = re.sub(r'\s{2,}', ' ', nm).strip()
            if not nm: continue
            names[nm] += 1
            b['ex'].append({'raw': nm, 'rep': rm.groups() if rm else None,
                            'wt': wm.groups() if wm else None, 'frag': frag})

print('\ndistinct raw names:', len(names))
for n, c in names.most_common():
    print(f'{c:4d}  {n}')
