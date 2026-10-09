import json, re
p = 'index.html'; s = open(p).read()
seed = open('data/seed.json').read()
def rep(old, new, n=1):
    global s
    assert old in s, 'MISSING:\n' + old[:160]
    s = s.replace(old, new, n)

# ---- 1. phases: his rep ranges and a 5/6-week RIR ramp -----------------------
rep("""const PHASE = {
  strength: {
    label:'Strength',
    rirByWeek:[2,2,1,0,0,0],
    comp:[4,6], iso:[8,12],
    note:'Heavy, low reps, sets held flat. Load is the variable.'
  },
  hypertrophy: {
    label:'Hypertrophy',
    rirByWeek:[3,2,2,1,0,0],
    comp:[6,10], iso:[10,15],
    note:'Moderate loads, sets ramp week to week toward your limit.'
  },
  deload: {
    label:'Deload',
    rirByWeek:[4,4,4,4,4,4],
    comp:[6,8], iso:[10,12],
    note:'Half the sets, ~65% of the load. Dissipate fatigue, keep the groove.'
  }
};""",
"""const PHASE = {
  strength: {
    label:'Strength',
    rirByWeek:[2,2,1,1,0,0,0],
    comp:[5,7], iso:[8,10],
    note:'Compounds 5–7, accessories 8–10. Sets held flat; load is the variable.'
  },
  hypertrophy: {
    label:'Hypertrophy',
    rirByWeek:[3,2,2,1,1,0,0],
    comp:[8,10], iso:[10,12],
    note:'Compounds 8–10, accessories 10–12. Sets ramp week to week toward your limit.'
  },
  deload: {
    label:'Deload',
    rirByWeek:[4,4,4,4,4,4,4],
    comp:[8,10], iso:[10,12],
    note:'Half the sets, ~65% of the load. Dissipate fatigue, keep the groove.'
  }
};""")

# ---- 2. seed blob + library built from it ------------------------------------
lib_start = s.index("/* ---------- 2. Exercise library")
lib_end   = s.index("/* ---------- 3. Default program")
s = s[:lib_start] + """/* ---------- 2. Exercise library + archived history -----------------------
   SEED.EX  [id, name, muscleIdx, isLower, isCompound, secondaryIdx[]]
   SEED.ARCH one row per logged session: [date, dayIdx, phaseIdx, entries[]]
             entry = [exIdx, weight, rir, repLo, repHi, setCount]
   Built from Ramiar's written log, 1 Mar 2024 – 15 Sep 2026.
   ------------------------------------------------------------------------ */
const SEED = """ + seed + """;

const LIB = SEED.EX.map(function(r){
  return { id:r[0], name:r[1], muscle:SEED.MUS[r[2]], load:r[3] ? 'lower' : 'upper',
           comp:!!r[4], secondary:r[5].map(function(i){ return SEED.MUS[i]; }) };
});
const LIB_BY_NAME = {}, LIB_BY_ID = {};
LIB.forEach(function(e){ LIB_BY_NAME[e.name] = e; LIB_BY_ID[e.id] = e; });

function mkExId(id, sets){
  const b = LIB_BY_ID[id];
  if(!b) throw new Error('unknown exercise id: ' + id);
  return { id:b.id, name:b.name, muscle:b.muscle, load:b.load, comp:b.comp,
           secondary:b.secondary, sets:sets };
}
function mkEx(name, sets){ return mkExId(LIB_BY_NAME[name].id, sets); }

const DAY_IDS   = ['push1','pull','push2','legs','mix'];
const DAY_NAMES = ['Push 1','Pull','Push 2','Legs','Mix'];
const PHASE_IDS = ['strength','hypertrophy','deload'];

/** Expand the packed archive into full session records. */
function expandArchive(){
  return SEED.ARCH.map(function(a){
    const di = a[1];
    return {
      id:'h' + a[0] + '-' + DAY_IDS[di], date:a[0], dayId:DAY_IDS[di],
      dayName:DAY_NAMES[di], phase:PHASE_IDS[a[2]], week:1, block:0,
      entries:a[3].map(function(e){
        const ex = LIB[e[0]], w = e[1], rir = e[2], lo = e[3], hi = e[4];
        const sets = [];
        for(let i = 0; i < e[5]; i++)
          sets.push({ w:w, reps:Math.max(lo, hi - i), rir:rir, done:true });
        return { exId:ex.id, name:ex.name, muscle:ex.muscle,
                 secondary:ex.secondary, range:[lo, hi], sets:sets };
      }),
      feedback:{}, duration:0, notes:'', arch:true, updatedAt:0
    };
  }).sort(function(x, y){ return x.date < y.date ? 1 : -1; });
}

""" + s[lib_end:]

# ---- 3. his program ----------------------------------------------------------
prog_start = s.index("function defaultProgram(){")
prog_end   = s.index("function defaultState(){")
s = s[:prog_start] + """function defaultProgram(){
  return { days: SEED.PROG.map(function(p){
    return { id:p.id, name:p.name, focus:p.focus,
             exercises: p.ex.map(function(e){ return mkExId(e[0], e[1]); }) };
  })};
}

""" + s[prog_end:]

# ---- 4. default state: his block lengths, current cursor ---------------------
rep("""      blocks:[ {type:'strength',weeks:4}, {type:'deload',weeks:1},
               {type:'hypertrophy',weeks:5}, {type:'deload',weeks:1} ],
      cursor:{ block:0, week:1, day:0 },
      cycle:1""",
"""      blocks:[ {type:'strength',weeks:5}, {type:'deload',weeks:1},
               {type:'hypertrophy',weeks:6}, {type:'deload',weeks:1} ],
      cursor:{ block:0, week:2, day:0 },
      cycle:1""")
rep("    sample: false,\n", "    archived: true,\n")
rep("  S = defaultState();\n  seedSample();", "  S = defaultState();\n  S.sessions = expandArchive();")

# ---- 5. drop the sample seeder ----------------------------------------------
a = s.index("/* ---------- 11. Sample seed")
b = s.index("/* ---------- 12. Rendering helpers")
s = s[:a] + "/* ---------- 11. (history ships with the app — see expandArchive) --------- */\n\n" + s[b:]
rep("""        if(S.sample && (r.sessionCount||0) > 0) S.sample = false;""", "")
rep("""    if(snap.size > 0){
      if(S.sample){ S.sessions = []; S.sample = false; }
      const byId = {};""",
"""    if(snap.size > 0){
      const byId = {};""")
# archived sessions live in the app bundle; never write 371 rows to the store
rep("""      const s = S.sessions.find(function(x){ return x.id === id; });
      if(s) await DB.doc('sessions/' + id).set(s);""",
"""      const s = S.sessions.find(function(x){ return x.id === id; });
      if(s && !s.arch) await DB.doc('sessions/' + id).set(s);""")
rep("""    if(S.sample){ /* keep sample rows until cleared explicitly */ }\n""", "")

# ---- 6. Today: no sample banner ---------------------------------------------
rep("  return (S.sample ? banner() : '') +\n", "  return ")
a = s.index("function banner(){")
b = s.index("function stat(k, v, u){")
s = s[:a] + s[b:]
rep("    case 'clearsample': clearSample(); break;\n", "")

# ---- 7. e1RM chart: range selector, no dot soup on long series ---------------
rep("""      lineChart(sel) +
    '</div>' +""",
"""      '<div class="chipbar" style="padding-bottom:4px;margin-bottom:2px">' +
        [[90,'3 months'],[365,'1 year'],[0,'All 2.5 years']].map(function(r){
          return '<button class="chip" data-range="' + r[0] + '" aria-pressed="' +
            ((S.ui.chartRange === undefined ? 365 : S.ui.chartRange) === r[0]) + '">' +
            r[1] + '</button>'; }).join('') + '</div>' +
      lineChart(sel) +
    '</div>' +""")
rep("""function lineChart(exId){
  const h = history(exId, {skipDeload:false}).slice().reverse();
  const pts = h.map(function(x){ return { d:x.date, v:bestSetE1rm(x) }; })
    .filter(function(p){ return p.v > 0; });""",
"""function lineChart(exId){
  const days = S.ui.chartRange === undefined ? 365 : S.ui.chartRange;
  let cut = '0000';
  if(days){ const c = new Date(); c.setDate(c.getDate() - days); cut = c.toISOString().slice(0,10); }
  const h = history(exId, {skipDeload:false}).slice().reverse();
  const pts = h.map(function(x){ return { d:x.date, v:bestSetE1rm(x) }; })
    .filter(function(p){ return p.v > 0 && p.d >= cut; });""")
rep("""    pts.map(function(p, i){
      return '<circle cx="' + x(i).toFixed(1) + '" cy="' + y(p.v).toFixed(1) + '" r="' +
        (i === pts.length - 1 ? 4 : 2.4) + '" fill="var(--accent)"/>'; }).join('') +""",
"""    pts.map(function(p, i){
      const lastPt = i === pts.length - 1;
      if(!lastPt && pts.length > 40) return '';
      return '<circle cx="' + x(i).toFixed(1) + '" cy="' + y(p.v).toFixed(1) + '" r="' +
        (lastPt ? 4 : 2.4) + '" fill="var(--accent)"/>'; }).join('') +""")
rep("""    '<div class="spread" style="margin-top:8px"><span class="faint" style="font-size:11.5px">' +
      'Epley estimate, reps in reserve counted as reps</span>' +""",
"""    '<div class="spread" style="margin-top:8px"><span class="faint" style="font-size:11.5px">' +
      pts.length + ' sessions · Epley estimate</span>' +""")
rep("""  if(t.dataset.cat){ S.ui.feedCat = t.dataset.cat; render(); return; }""",
"""  if(t.dataset.cat){ S.ui.feedCat = t.dataset.cat; render(); return; }
  if(t.dataset.range !== undefined){ S.ui.chartRange = +t.dataset.range; render(); return; }""")
rep("""[data-act],[data-tab],[data-cat],[data-open],[data-fb],[data-pick],[data-day],[data-sheet-bg]""",
   """[data-act],[data-tab],[data-cat],[data-range],[data-open],[data-fb],[data-pick],[data-day],[data-sheet-bg]""")

# ---- 8. "strongest trend" insight: recent window, not all of 2024 ------------
rep("""  allExercises().forEach(function(ex){
    const h = history(ex.id);
    if(h.length < 2) return;
    const now = bestSetE1rm(h[0]), then = bestSetE1rm(h[h.length-1]);
    if(!then) return;
    const pct = (now - then) / then * 100;
    if(pct > 2 && (!bestGain || pct > bestGain.pct))
      bestGain = { name:ex.name, pct:pct, sessions:h.length };
  });""",
"""  allExercises().forEach(function(ex){
    const h = history(ex.id).slice(0, 12);   // recent form, not 2024
    if(h.length < 4) return;
    const now = bestSetE1rm(h[0]), then = bestSetE1rm(h[h.length-1]);
    if(!then) return;
    const pct = (now - then) / then * 100;
    if(pct > 2 && (!bestGain || pct > bestGain.pct))
      bestGain = { name:ex.name, pct:pct, sessions:h.length };
  });""")
rep("""      take:'Estimated 1RM up ' + bestGain.pct.toFixed(1) + '% across ' + bestGain.sessions + ' logged sessions.',""",
"""      take:'Estimated 1RM up ' + bestGain.pct.toFixed(1) + '% across your last ' +
           bestGain.sessions + ' sessions of it.',""")

# ---- 9. data panel + credits -------------------------------------------------
rep("""      '<span class="mono faint" style="font-size:12px">' + S.sessions.length + ' sessions</span></div>' +""",
"""      '<span class="mono faint" style="font-size:12px">' + S.sessions.length + ' sessions</span></div>' +
      '<div class="faint" style="font-size:11.5px;line-height:1.45;margin-bottom:12px">' +
      SEED.ARCH.length + ' of those were imported from your written log ' +
      '(1 Mar 2024 – 15 Sep 2026) and ship inside the app, so they cannot be lost. ' +
      'Sessions you log from here on sync to your account.</div>' +""")
rep("""    'Iron Ledger · block periodisation after Mike Israetel (volume landmarks, RIR ramp, ' +
    'autoregulated set progression) and Mike Matthews (double progression, compound emphasis).</p>';""",
"""    'Iron Ledger · your rep ranges (5–7 / 8–10 strength, 8–10 / 10–12 hypertrophy), ' +
    'block periodisation after Mike Israetel (volume landmarks, RIR ramp, autoregulated ' +
    'set progression) and Mike Matthews (double progression, compound emphasis).</p>';""")

open(p,'w').write(s)
print('patched. bytes:', len(s))
