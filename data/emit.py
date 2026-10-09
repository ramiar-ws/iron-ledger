import json, re
exec(open('build.py').read().split('# ============================== ANALYSIS')[0])

MUS = ['Chest','Back','Front delts','Side delts','Rear delts','Triceps','Biceps',
       'Quads','Hamstrings','Glutes','Calves','Abs','Forearms','Traps']
MI  = {m:i for i,m in enumerate(MUS)}
IDS = list(CANON.keys())
XI  = {k:i for i,k in enumerate(IDS)}

EXLIB = [[k, CANON[k][0], MI[CANON[k][1]], 1 if CANON[k][2]=='lower' else 0,
          1 if CANON[k][3] else 0, [MI[m] for m in CANON[k][4]]] for k in IDS]

DAYIDX   = {'push1':0,'pull':1,'push2':2,'legs':3,'mix':4}
PHASEIDX = {'strength':0,'hypertrophy':1,'deload':2}

ARCH = []
for s in sorted(sessions, key=lambda x: x['date']):
    ents = []
    for e in s['entries']:
        w   = e['sets'][0]['w']
        rir = e['sets'][0]['rir']
        lo, hi = e['range']
        ents.append([XI[e['exId']], w, rir, lo, hi, len(e['sets'])])
    ARCH.append([s['date'], DAYIDX[s['dayId']], PHASEIDX[s['phase']], ents])

# --- current program, taken from his most recent session of each day ---
def latest(day):
    for s in sorted(sessions, key=lambda x: x['date'], reverse=True):
        if s['dayId'] == day and len(s['entries']) >= 5:
            return s
PROG = []
for day, name, focus in [('push1','Push 1','Incline-led chest, delts, triceps'),
                         ('pull','Pull','Back, rear delts, arms'),
                         ('push2','Push 2','Flat-bench chest, shoulders, triceps'),
                         ('legs','Legs','Quads, hamstrings, arms')]:
    s = latest(day)
    PROG.append({'id':day,'name':name,'focus':focus,'from':s['date'],
                 'ex':[[e['exId'], len(e['sets'])] for e in s['entries']]})

out = {'MUS':MUS,'EX':EXLIB,'ARCH':ARCH,'PROG':PROG}
blob = json.dumps(out, separators=(',',':'))
open('seed.json','w').write(blob)
print('seed bytes:', len(blob))
print('sessions:', len(ARCH), 'exercises in lib:', len(EXLIB))
for p in PROG:
    print(f"\n{p['name']}  (from {p['from']})")
    for cid, n in p['ex']:
        print(f"    {n} x {CANON[cid][0]}")
