import re, json
from collections import Counter, defaultdict
from datetime import date, timedelta

RAW = open('raw-log.txt').read()
DAYS = r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
DATE_RE = re.compile(r'\b(\d{1,2})\.(\d{1,2})\b')
REP_RE  = re.compile(r'(\d{1,2})\s*x?\s*[\*x]\s*(\d{1,3})(?:\s*-\s*(\d{1,2}))?')
WT_RE   = re.compile(r'(\d+(?:\.\d+)?)\s*(?:-|/)\s*(\d+(?:\.\d+)?)\s*kg|(\d+(?:\.\d+)?)\s*kg')

# ------------------------------------------------------------------ library
# canonical: (display name, muscle, load class, compound?, secondary[])
CANON = {
 'bench-press':            ('Bench Press','Chest','upper',True,['Triceps','Front delts']),
 'incline-bench-press':    ('Incline Bench Press','Chest','upper',True,['Front delts','Triceps']),
 'db-bench-press':         ('DB Bench Press','Chest','upper',True,['Triceps','Front delts']),
 'db-incline-bench-press': ('DB Incline Bench Press','Chest','upper',True,['Front delts','Triceps']),
 'db-chest-opener':        ('DB Chest Opener','Chest','upper',False,[]),
 'incline-db-flye':        ('Incline DB Flye','Chest','upper',False,[]),
 'bench-pullover':         ('Bench Pullover','Back','upper',False,['Chest']),
 'dips':                   ('Dips','Chest','upper',True,['Triceps','Front delts']),
 'push-up':                ('Push-up','Chest','upper',True,['Triceps']),
 'bb-standing-shoulder-press':('BB Standing Shoulder Press','Front delts','upper',True,['Triceps']),
 'db-shoulder-press':      ('DB Shoulder Press','Front delts','upper',True,['Triceps']),
 'db-arnold-press':        ('DB Arnold Press','Front delts','upper',True,['Side delts','Triceps']),
 'db-shoulder-opener':     ('DB Shoulder Opener','Side delts','upper',False,[]),
 'total-lateral-raise':    ('Total Lateral Raise','Side delts','upper',False,[]),
 'z-bar-straight-lift':    ('Z Bar Straight Lift','Front delts','upper',False,[]),
 'z-bar-elbow-raise':      ('Z Bar Elbow Raise','Side delts','upper',False,['Traps']),
 'db-seated-t-shape':      ('DB Seated T-Shape','Rear delts','upper',False,[]),
 'db-laid-flye':           ('DB Laid Flye','Rear delts','upper',False,[]),
 'db-seated-shoulder-flye':('DB Seated Shoulder Flye','Side delts','upper',False,[]),
 'db-full-shoulder-opener':('DB Full Shoulder Opener','Side delts','upper',False,[]),
 'reverse-fly':            ('Reverse Fly','Rear delts','upper',False,[]),
 'face-pull':              ('Face Pull','Rear delts','upper',False,['Traps']),
 'bb-row':                 ('BB Row','Back','upper',True,['Rear delts','Biceps']),
 'db-bench-row':           ('DB Bench Row','Back','upper',True,['Biceps']),
 'standing-lat-pulldown':  ('Standing Lat Pulldown','Back','upper',True,['Biceps']),
 'lat-machine':            ('Lat Machine','Back','upper',True,['Biceps']),
 'pull-up':                ('Pull-up','Back','upper',True,['Biceps','Forearms']),
 'reverse-row':            ('Reverse Row','Back','upper',False,['Rear delts']),
 'bb-landmine-row':        ('BB Landmine Row','Back','upper',True,['Rear delts']),
 'z-bar-row':              ('Z Bar Row','Back','upper',True,['Rear delts']),
 'machine-row':            ('Machine Row','Back','upper',True,['Rear delts']),
 'z-bar-tricep-press':     ('Z Bar Tricep Press','Triceps','upper',False,[]),
 'tricep-pushdown':        ('Tricep Pushdown','Triceps','upper',False,[]),
 'arm-extension':          ('Arm Extension (machine)','Triceps','upper',False,[]),
 'db-single-tricep':       ('DB Single Tricep Extension','Triceps','upper',False,[]),
 'bb-bicep-curl':          ('BB Bicep Curl','Biceps','upper',False,['Forearms']),
 'z-bar-bicep-curl':       ('Z Bar Bicep Curl','Biceps','upper',False,['Forearms']),
 'incline-db-curl':        ('Incline DB Curl','Biceps','upper',False,[]),
 'db-curl':                ('DB Curl','Biceps','upper',False,['Forearms']),
 'preacher-curl':          ('Preacher Curl','Biceps','upper',False,[]),
 'arm-curl':               ('Arm Curl (machine)','Biceps','upper',False,[]),
 'deadlift':               ('Deadlift','Hamstrings','lower',True,['Glutes','Back']),
 'romanian-deadlift':      ('Romanian Deadlift','Hamstrings','lower',True,['Glutes','Back']),
 'bb-high-bar-squat':      ('BB High Bar Squat','Quads','lower',True,['Glutes','Hamstrings']),
 'db-lunge':               ('DB Lunge','Quads','lower',True,['Glutes']),
 'leg-press':              ('Leg Press','Quads','lower',True,['Glutes']),
 'quad-extension':         ('Quad Extension','Quads','lower',False,[]),
 'prone-leg-curl':         ('Prone Leg Curl','Hamstrings','lower',False,[]),
 'calf-raise':             ('Calf Raise','Calves','lower',False,[]),
 'plate-wheel':            ('Plate Wheel','Abs','upper',False,[]),
}

ALIAS = {
 'bench press':'bench-press','bench press +bar':'bench-press',
 'incline bench press':'incline-bench-press',
 'db bench press':'db-bench-press','db bench press -10':'db-bench-press',
 'db seated bench press':'db-bench-press',
 'db incline bench press':'db-incline-bench-press','db incline press':'db-incline-bench-press',
 'db bench / incline press':'db-incline-bench-press',
 'db chest opener':'db-chest-opener','bench chest opener':'db-chest-opener',
 'chest opener resistant band':'db-chest-opener','db chest drop':'db-chest-opener',
 'db chest opener / incline':'db-chest-opener','chest opener / incline flyer':'db-chest-opener',
 'incline flyer/db chest opener':'db-chest-opener','incline / chest opener':'db-chest-opener',
 'incline flyer':'incline-db-flye','incline db flyes':'incline-db-flye',
 'db chest pull over':'bench-pullover','bench pullover':'bench-pullover',
 'bench pullover 10':'bench-pullover','db pullover':'bench-pullover','z bar pullover':'bench-pullover',
 'dips':'dips','dips + pulls':'dips',
 'deficit push ups':'push-up','incline push ups':'push-up',
 'bb standing shoulder press':'bb-standing-shoulder-press','bb shoulder press':'bb-standing-shoulder-press',
 'standing bb shoulder press':'bb-standing-shoulder-press','bb seated shoulder press':'bb-standing-shoulder-press',
 'z standing shoulder press':'bb-standing-shoulder-press','shoulder press':'bb-standing-shoulder-press',
 'db shoulder press':'db-shoulder-press',
 'db arnold press':'db-arnold-press','seated arnold press':'db-arnold-press',
 'standing arnold press':'db-arnold-press',
 'db shoulder opener':'db-shoulder-opener','db standing shoulder opener':'db-shoulder-opener',
 'db standing shoulder raise':'db-shoulder-opener','seated t / shoulder opener':'db-shoulder-opener',
 'total lateral raise':'total-lateral-raise','total raise/seated t-shape':'total-lateral-raise',
 'z bar straight lift':'z-bar-straight-lift','db standing straight raise':'z-bar-straight-lift',
 'db straight arm opener':'z-bar-straight-lift',
 'z bar elbow raises':'z-bar-elbow-raise',
 'db seated t-shape':'db-seated-t-shape','db standing t-shape':'db-seated-t-shape',
 'db laid flyer':'db-laid-flye','db bent side-raise':'db-laid-flye',
 'db seated shoulder flyer':'db-seated-shoulder-flye',
 'db full shoulder opener':'db-full-shoulder-opener',
 'reverse fly':'reverse-fly','cable face pull':'face-pull',
 'bb rows':'bb-row','bb row':'bb-row','bb standing row':'bb-row','bb bent standing row':'bb-row',
 'bb bent over standing row':'bb-row',
 'db bench row':'db-bench-row','db split back lift':'db-bench-row',
 'db bench supported pulls':'db-bench-row',
 'standing lat pull down':'standing-lat-pulldown','standing / sitting lat pull down':'standing-lat-pulldown',
 'sitting lat pull down':'standing-lat-pulldown','standing lat pulldown':'standing-lat-pulldown',
 'hoist lat pull down':'standing-lat-pulldown',
 'lat pulldown':'lat-machine','pulldown':'lat-machine','lat machine':'lat-machine',
 'vertical traction':'lat-machine',
 'pull ups':'pull-up','pull-ups':'pull-up',
 'reverse row':'reverse-row','reverse rows':'reverse-row','reverse bench press':'reverse-row',
 'bb landmine row':'bb-landmine-row','z bar rows':'z-bar-row',
 'low row':'machine-row','pullrow':'machine-row',
 'z bar tricep press':'z-bar-tricep-press','z tricep press':'z-bar-tricep-press',
 'z laying tricep press':'z-bar-tricep-press','db laying tricep press':'z-bar-tricep-press',
 'bb triceps press':'z-bar-tricep-press','z triceps press':'z-bar-tricep-press',
 'tricep push down':'tricep-pushdown','standing tricep drags':'tricep-pushdown',
 'overhead tricep drags':'tricep-pushdown',
 'arm extension':'arm-extension',
 'db single tricep pull':'db-single-tricep','db standing tricep press':'db-single-tricep',
 'db tricep push':'db-single-tricep','single dumbbell tricep':'db-single-tricep',
 'db single tricep / bicep':'db-single-tricep',
 'bb bicep curl':'bb-bicep-curl','bb bicep curls':'bb-bicep-curl',
 'bb standing bicep curl':'bb-bicep-curl','bicep bar +bar':'bb-bicep-curl',
 'z bicep curl':'z-bar-bicep-curl','z bicep curls':'z-bar-bicep-curl',
 'z bar bicep curl':'z-bar-bicep-curl','seated z bar bicep curl':'z-bar-bicep-curl',
 'incline db curl':'incline-db-curl',
 'db bicep curl':'db-curl','db seated bicep curl':'db-curl','db seated bicep hammer':'db-curl',
 'db preacher curls':'preacher-curl',
 'arm curl':'arm-curl','bicep curl':'arm-curl','standing bicep curl':'arm-curl',
 'deadlifts':'deadlift','deadlift':'deadlift','deadlift +bar':'deadlift',
 'romanian deadlifts':'romanian-deadlift','db romanian deadlifts':'romanian-deadlift',
 'bb high bar squat':'bb-high-bar-squat','squats':'bb-high-bar-squat',
 'bb back squats':'bb-high-bar-squat','single db squat':'bb-high-bar-squat',
 'db lunges':'db-lunge','db lunges per hand':'db-lunge','db walking lunges':'db-lunge',
 'dumbbell lunge squad':'db-lunge','bench supported lunges':'db-lunge',
 'bench step alternate':'db-lunge',
 'leg press':'leg-press','quad extension':'quad-extension',
 'probe leg curl':'prone-leg-curl','prone leg curl':'prone-leg-curl',
 'wp calf raises':'calf-raise','seated calf':'calf-raise',
 'plate wheeling':'plate-wheel','single weight plate rotation':'plate-wheel',
}

PHASE_RANGES = {'strength':((5,7),(8,10)),
                'hypertrophy':((8,10),(10,12)),
                'deload':((8,10),(10,12))}

def canon(raw):
    k = re.sub(r'\s{2,}',' ', raw.strip().lower())
    return ALIAS.get(k)

# ------------------------------------------------------------------ parse
blocks, cur = [], None
for line in RAW.split('\n'):
    s = line.strip()
    if not s or s == '/' or s.lower() == 'workout':
        continue
    if re.search(DAYS, s, re.I):
        cur = {'hdr': s, 'lines': []}; blocks.append(cur)
    elif cur is not None:
        cur['lines'].append(s)

# dates: year rollover, then repair out-of-order transcription slips
prev, year, repaired = None, 2024, 0
for b in blocks:
    m = DATE_RE.search(b['hdr'])
    d, mo = int(m.group(1)), int(m.group(2))
    cand = date(year, mo, d)
    if prev and (prev - cand).days > 150:            # December -> January
        year += 1; cand = date(year, mo, d)
    if prev and cand < prev - timedelta(days=20):    # month digit slipped
        nm, ny = (mo % 12) + 1, year + (1 if mo == 12 else 0)
        try:
            alt = date(ny, nm, d)
            if prev <= alt <= prev + timedelta(days=20):
                cand = alt; year = ny; repaired += 1
        except ValueError: pass
    if prev and cand <= prev:                        # duplicate / backwards day
        cand = prev + timedelta(days=1); repaired += 1
    b['date'] = cand; prev = cand

print(f'blocks={len(blocks)} repaired_dates={repaired}')
print('range:', blocks[0]['date'], '->', blocks[-1]['date'])

def split_fragments(line):
    out, last = [], 0
    for m in REP_RE.finditer(line):
        out.append(line[last:m.end()]); last = m.end()
    tail = line[last:].strip()
    if tail:
        if out: out[-1] += ' ' + tail
        else: out.append(tail)
    return [f.strip() for f in out if f.strip()]

def clean_name(nm):
    nm = re.sub(r'>\s*','',nm); nm = re.sub(r'\(.*?\)','',nm)
    nm = re.sub(r'\b(tough|doable)\b','',nm,flags=re.I)
    nm = re.sub(r'[\s,+*~\-–/]+$','',nm).strip(' -–~/')
    return re.sub(r'\s{2,}',' ',nm).strip()

sessions, unmapped, dropped = [], Counter(), 0
for b in blocks:
    hdr = b['hdr']
    hl = hdr.lower()
    if   'deload'  in hl: phase = 'deload'
    elif 're-entry' in hl or 'reentry' in hl: phase = 'deload'
    elif 'strength' in hl: phase = 'strength'
    elif 'hypertrophy' in hl: phase = 'hypertrophy'
    else: phase = None

    # header-level default rep scheme
    dm = REP_RE.search(re.sub(DATE_RE,'',hdr))
    dflt = (int(dm.group(1)), int(dm.group(2)), int(dm.group(3)) if dm.group(3) else None) if dm else None

    if phase is None:
        hs = [int(m.group(3) or m.group(2)) for line in b['lines']
              for m in [REP_RE.search(line)] if m]
        if hs: phase = 'strength' if max(hs) <= 8 else 'hypertrophy'

    entries = []
    for line in b['lines']:
        for frag in split_fragments(line):
            rm = REP_RE.search(frag)
            body = REP_RE.sub('', frag)
            wm = WT_RE.search(body)
            body = WT_RE.sub('', body)
            nm = clean_name(body)
            if not nm: continue
            cid = canon(nm)
            if not cid:
                unmapped[nm] += 1; dropped += 1; continue

            if rm:
                nsets = int(rm.group(1)); lo = int(rm.group(2))
                hi = int(rm.group(3)) if rm.group(3) else None
                if hi is None and lo > 30:           # "4*810" typo
                    lo, hi = lo // 100 if lo > 99 else lo // 10, lo % 10 or 10
                    lo, hi = 8, 10
            elif dflt:
                nsets, lo, hi = dflt
            else:
                nsets, lo, hi = 3, 10, None
            if hi is None: hi = lo
            if lo > hi: lo, hi = hi, lo
            nsets = max(1, min(nsets, 8))

            if wm:
                w = max(float(wm.group(1)), float(wm.group(2))) if wm.group(1) else float(wm.group(3))
            else:
                w = 0.0

            rir = 2
            fl = frag.lower()
            if 'tough' in fl or '~' in frag: rir = 1
            elif 'doable' in fl: rir = 3
            if phase == 'deload': rir = 4

            nmz, muscle, loadcls, comp, sec = CANON[cid]
            # A bare "4*7" records the reps hit, not the range worked in. When the
            # session's phase is known and that number sits inside the phase's
            # canonical range, restore the range so progression compares like to like.
            if lo == hi and phase:
                clo, chi = (PHASE_RANGES[phase][0] if comp else PHASE_RANGES[phase][1])
                if clo <= lo <= chi: lo, hi = clo, chi
            sets = [{'w': w, 'reps': max(lo, min(hi, hi - i)), 'rir': rir, 'done': True}
                    for i in range(nsets)]
            entries.append({'exId': cid, 'name': nmz, 'muscle': muscle,
                            'secondary': sec, 'range': [lo, hi], 'sets': sets})
    if not entries: continue

    if phase is None:
        his = [e['range'][1] for e in entries if CANON[e['exId']][3]]
        phase = 'strength' if his and max(his) <= 8 else 'hypertrophy'

    if   'pull' in hl and 'push' not in hl: day, dname = 'pull','Pull'
    elif re.search(r'\bleg', hl):           day, dname = 'legs','Legs'
    elif 'push' in hl:
        first = entries[0]['exId']
        if first in ('bench-press','bb-standing-shoulder-press','total-lateral-raise',
                     'db-incline-bench-press','db-seated-t-shape'):
            day, dname = 'push2','Push 2'
        else:
            day, dname = 'push1','Push 1'
    else: day, dname = 'mix','Mix'

    sessions.append({'id':'h'+b['date'].isoformat()+'-'+day, 'date': b['date'].isoformat(),
                     'dayId': day, 'dayName': dname, 'phase': phase, 'week': 1, 'block': 0,
                     'entries': entries, 'feedback': {}, 'duration': 0, 'notes': '',
                     'arch': True, 'updatedAt': 0})

sessions.sort(key=lambda s: s['date'], reverse=True)
print(f'sessions={len(sessions)} entries={sum(len(s["entries"]) for s in sessions)} dropped_lines={dropped}')
print('phases:', Counter(s['phase'] for s in sessions))
print('days:', Counter(s['dayId'] for s in sessions))
if unmapped:
    print('UNMAPPED:', unmapped.most_common())

json.dump(sessions, open('sessions.json','w'))
print('bytes:', len(open('sessions.json').read()))

# ============================== ANALYSIS =====================================
print('\n================ ANALYSIS ================')
from datetime import datetime
S = sorted(sessions, key=lambda s: s['date'])

def e1rm(w,r,rir):
    eff = r + rir
    return 0 if (not w or eff > 14) else w*(1+eff/30)

def series(cid):
    out=[]
    for s in S:
        for e in s['entries']:
            if e['exId']==cid:
                best=max((st['w'] for st in e['sets']), default=0)
                be=max((e1rm(st['w'],st['reps'],st['rir']) for st in e['sets']), default=0)
                out.append((s['date'],best,be,s['phase']))
    return out

print('\n-- key lift trajectory (first -> last top weight, best e1RM) --')
for cid in ['bench-press','incline-bench-press','db-bench-press','db-incline-bench-press',
            'bb-standing-shoulder-press','db-shoulder-press','db-arnold-press',
            'bb-row','db-bench-row','standing-lat-pulldown','deadlift','bb-high-bar-squat',
            'leg-press','z-bar-tricep-press','incline-db-curl']:
    sr=series(cid)
    if len(sr)<2: continue
    be=max(x[2] for x in sr)
    bd=[x[0] for x in sr if x[2]==be][0]
    print(f'{CANON[cid][0]:<30} {sr[0][1]:>6.1f}kg ({sr[0][0]})  ->  {sr[-1][1]:>6.1f}kg ({sr[-1][0]})   best e1RM {be:5.1f} on {bd}   n={len(sr)}')

print('\n-- bench press year by year (top weight seen per quarter) --')
q=defaultdict(float)
for d,w,be,ph in series('bench-press'):
    y,m=int(d[:4]),int(d[5:7]); q[f'{y}Q{(m-1)//3+1}']=max(q[f'{y}Q{(m-1)//3+1}'],w)
for k in sorted(q): print(f'  {k}: {q[k]:.0f}kg')

print('\n-- sessions per month by day type --')
mm=defaultdict(Counter)
for s in S: mm[s['date'][:7]][s['dayId']]+=1
for k in sorted(mm)[-14:]:
    c=mm[k]; print(f'  {k}  push1={c["push1"]:<2} pull={c["pull"]:<2} push2={c["push2"]:<2} legs={c["legs"]:<2} mix={c["mix"]:<2}  total={sum(c.values())}')

print('\n-- LEGS gap analysis --')
legs=[s['date'] for s in S if s['dayId']=='legs']
print(f'  total legs sessions: {len(legs)} of {len(S)} ({len(legs)/len(S)*100:.0f}%)')
print(f'  last legs session: {legs[-1]}  ({(date(2026,9,16)-date(*map(int,legs[-1].split("-")))).days} days ago)')
lower=[s['date'] for s in S if any(CANON[e["exId"]][2]=='lower' for e in s['entries'])]
print(f'  last session with ANY lower-body work: {lower[-1]}')

print('\n-- weekly hard sets by muscle, last 28 days --')
cut=(date(2026,9,16)-timedelta(days=28)).isoformat()
vol=Counter()
for s in S:
    if s['date']<cut: continue
    for e in s['entries']:
        n=len(e['sets']); vol[e['muscle']]+=n
        for m2 in e['secondary']: vol[m2]+=n*0.5
for m,v in vol.most_common(): print(f'  {m:<14} {v/4:5.1f} sets/week')

print('\n-- current strength block --')
for s in S[-8:]:
    print(f'  {s["date"]}  {s["dayName"]:<7} {s["phase"]:<12} {len(s["entries"])} exercises')

print('\n-- latest working weights per exercise (last seen) --')
last={}
for s in S:
    for e in s['entries']:
        last[e['exId']]=(s['date'],max(st['w'] for st in e['sets']),e['range'],len(e['sets']))
for cid,(d,w,rg,n) in sorted(last.items(), key=lambda kv:-len(series(kv[0]))):
    print(f'  {CANON[cid][0]:<30} {w:>6.1f}kg  {n}x{rg[0]}-{rg[1]}  last {d}   n={len(series(cid))}')
