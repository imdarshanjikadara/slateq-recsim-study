/* SlateStream: a streaming-style view of the SlateQ study.
   Data: ../data/site.json and ../data/traces_seed<k>.json, both written by scripts/build_web.py from results/.
   No result number is typed by hand in this file: every value shown is read from those files.
   The replays are recorded evaluation sessions (N = 10 candidates, k = 3 shown); nothing is simulated here. */
"use strict";

const AGENTS = ["slateq", "learned_myopic", "oracle_myopic", "random"];
const NAME = { slateq: "SlateQ", learned_myopic: "Learned myopic", oracle_myopic: "Oracle myopic", random: "Random" };
const ROLE = {
  slateq: "Plans ahead for the whole session (reinforcement learning, γ = 0.99)",
  learned_myopic: "Learns to chase the next click (same network, γ = 0)",
  oracle_myopic: "Perfect click-chaser: it is allowed to see the viewer's hidden tastes",
  random: "Shows random videos",
};
const PRIMARY = "SlateQ - learned-myopic";
const CELL = [10, 3];
const RUNGS = ["matched", "mild_noclick3", "moderate_logit", "severe_cascade"];
const RUNG = { matched: "Users behave as assumed", mild_noclick3: "Mild: users skip more", moderate_logit: "Moderate: different choice formula", severe_cascade: "Severe: users scan top-down (cascade)", paper_cascade: "SlateQ paper's cascade" };

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const MINUS = "−";
const fmt = (x, d = 2) => (x === null || x === undefined || Number.isNaN(x) ? "n/a" : Number(x).toFixed(d).replace("-", MINUS));
const sgn = (x, d = 2) => (x === null || x === undefined || Number.isNaN(x) ? "n/a" : (x >= 0 ? "+" : MINUS) + Math.abs(x).toFixed(d));
const pct = (x, d = 1) => (x === null || x === undefined ? "n/a" : (x >= 0 ? "+" : MINUS) + Math.abs(100 * x).toFixed(d) + "%");
const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const agentColor = (a) => cssVar(`--a-${a}`) || "#888";
const isCell = (r, n, k) => r.num_candidates === n && r.slate_size === k;
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

let SITE = null;
const TRACES = {};
const S = { taste: "abs", view: "watch", seed: 0, ep: 0, left: "slateq", right: "learned_myopic", t: 0, playing: false, speed: 1, timer: null, max: 1 };
let BMAX = 1;

/* ================================================================ data */
async function getJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
}
async function loadTrace(seed) {
  if (!TRACES[seed]) {
    const tr = await getJSON(`data/traces_seed${seed}.json`);
    for (const a of Object.keys(tr)) for (const e of tr[a]) prep(e);
    TRACES[seed] = tr;
  }
  return TRACES[seed];
}
function prep(e) {
  let c = 0, k = 0;
  e.cum = e.reward.map((r) => (c += r));
  e.clk = e.clicked.map((i) => (k += i >= 0 ? 1 : 0));
  e.len = e.reward.length;
  e.total = c;
  e.clicks = k;
}
const sess = (agent) => TRACES[S.seed] && TRACES[S.seed][agent] ? TRACES[S.seed][agent][S.ep] : null;
const viewerCount = () => (SITE.trace_seeds || []).length * 5;

/* ================================================================ covers */
function rng(seed) {
  let s = (seed * 2654435761) >>> 0;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
}
function topicHue(topic) { return (topic * 47 + 200) % 360; }
function coverBg(topic) {
  const h = topicHue(topic), h2 = (h + 55) % 360;
  return `linear-gradient(135deg, hsl(${h} 72% 48%), hsl(${h2} 70% 22%))`;
}
/* Generated artwork: pattern and colours depend on the topic; small variations per video. */
function coverSVG(topic, variant) {
  const r = rng(topic * 997 + variant * 31 + 7);
  const kind = topic % 5;
  let s = "";
  if (kind === 0) for (let i = 0; i < 4; i++) s += `<circle cx="${(r() * 160).toFixed(1)}" cy="${(r() * 90).toFixed(1)}" r="${(10 + r() * 34).toFixed(1)}" fill="#fff" fill-opacity="${(0.06 + r() * 0.14).toFixed(2)}"/>`;
  if (kind === 1) for (let i = -2; i < 10; i++) s += `<rect x="${i * 22 + r() * 6}" y="-20" width="${6 + r() * 6}" height="140" fill="#fff" fill-opacity="${(0.05 + r() * 0.1).toFixed(2)}" transform="rotate(25 80 45)"/>`;
  if (kind === 2) { let p = "0,90"; for (let x = 0; x <= 160; x += 20 + r() * 20) p += ` ${x.toFixed(0)},${(30 + r() * 50).toFixed(0)}`; s += `<polygon points="${p} 160,90" fill="#000" fill-opacity=".28"/>`; s += `<circle cx="${(30 + r() * 100).toFixed(0)}" cy="${(14 + r() * 18).toFixed(0)}" r="9" fill="#fff" fill-opacity=".55"/>`; }
  if (kind === 3) for (let j = 0; j < 4; j++) { const y = 20 + j * 18 + r() * 6, a = 4 + r() * 8; s += `<path d="M0 ${y} Q 20 ${y - a} 40 ${y} T 80 ${y} T 120 ${y} T 160 ${y}" stroke="#fff" stroke-opacity="${(0.12 + r() * 0.2).toFixed(2)}" stroke-width="${(1.5 + r() * 3).toFixed(1)}" fill="none"/>`; }
  if (kind === 4) for (let x = 8; x < 160; x += 14) for (let y = 8; y < 90; y += 14) if (r() > 0.35) s += `<circle cx="${x}" cy="${y}" r="${(1 + r() * 2.4).toFixed(1)}" fill="#fff" fill-opacity=".35"/>`;
  s += `<text x="150" y="82" text-anchor="end" font-size="30" font-weight="800" fill="#fff" fill-opacity=".22" font-family="Inter,system-ui,sans-serif">${String(topic + 1).padStart(2, "0")}</text>`;
  return `<svg viewBox="0 0 160 90" preserveAspectRatio="xMidYMid slice" width="100%" height="100%" aria-hidden="true" style="display:block">${s}</svg>`;
}
const topicName = (c) => `Topic ${String(c + 1).padStart(2, "0")}`;
function avatarBg(i) { const h = (i * 67 + 20) % 360; return `linear-gradient(135deg, hsl(${h} 70% 55%), hsl(${(h + 60) % 360} 65% 35%))`; }

/* ================================================================ viewers */
function renderViewers() {
  const box = $("#viewers");
  box.innerHTML = "";
  let i = 0;
  for (const seed of SITE.trace_seeds) {
    for (let ep = 0; ep < 5; ep++) {
      i++;
      const b = document.createElement("button");
      b.className = "viewer";
      b.setAttribute("role", "option");
      b.dataset.seed = seed; b.dataset.ep = ep;
      b.setAttribute("aria-selected", String(seed === S.seed && ep === S.ep));
      const isCase = seed === SITE.case_study_seed && ep === 0;
      b.innerHTML = `<span class="av" style="background:${avatarBg(i)}">V${i}</span><span>Viewer ${i}</span>${isCase ? '<span class="case">case study</span>' : ""}`;
      b.title = `Run seed ${seed}, recorded test viewer ${ep + 1}`;
      b.addEventListener("click", () => selectViewer(seed, ep));
      box.appendChild(b);
    }
  }
  $("#vb-note").textContent = `${viewerCount()} recorded test viewers (5 per run seed), N = ${CELL[0]} candidates, k = ${CELL[1]} shown. Each is one real recorded session per recommender.`;
}
async function selectViewer(seed, ep) {
  pause();
  S.seed = seed; S.ep = ep; S.t = 0;
  $$(".viewer").forEach((b) => b.setAttribute("aria-selected", String(+b.dataset.seed === seed && +b.dataset.ep === ep)));
  await loadTrace(seed);
  BMAX = Math.max(BMAX, ...AGENTS.map((a) => Math.ceil(sess(a).budget[0] / 10) * 10));
  buildSession();
}

/* ================================================================ watch */
function paneShell(side) {
  const p = $(side === "L" ? "#paneL" : "#paneR");
  const cur = side === "L" ? S.left : S.right;
  p.innerHTML = `
    <div class="pane-h"><span class="dot"></span>
      <select class="agent-sel" aria-label="Recommender">${AGENTS.map((a) => `<option value="${a}" ${a === cur ? "selected" : ""}>${NAME[a]}</option>`).join("")}</select>
      <span class="role"></span></div>
    <div class="screen"></div>
    <div class="slate-label"><span>On screen now</span><span class="sl-r"></span></div>
    <div class="slate"></div>
    <div class="stats">
      <div class="stat main"><div class="k">Watch time</div><div class="v w">0</div></div>
      <div class="stat"><div class="k">Videos watched</div><div class="v c">0</div></div>
      <div class="stat"><div class="k">Steps</div><div class="v s">0</div></div>
    </div>
    <div class="battery"><div class="bl"><span>Viewer's time budget</span><span class="bv"></span></div><div class="bt"><i></i></div></div>
    <div class="film" title="Session history: each bar is one step. Tall = watched; colour = quality of the watched video. Click to jump."></div>
    <div class="film-l"><span>session history</span><span class="fl-r"></span></div>`;
  $(".agent-sel", p).addEventListener("change", (ev) => {
    if (side === "L") S.left = ev.target.value; else S.right = ev.target.value;
    buildSession();
  });
  $(".film", p).addEventListener("click", (ev) => {
    const r = ev.currentTarget.getBoundingClientRect();
    seek(Math.round(((ev.clientX - r.left) / r.width) * S.max));
  });
}
function qualityColor(q) {
  const t = Math.max(-1, Math.min(1, q / 2));
  return t >= 0 ? `hsl(152 65% ${40 + 15 * t}%)` : `hsl(350 85% ${62 - 10 * t}%)`;
}
function buildFilm(p, e) {
  const film = $(".film", p);
  const maxR = Math.max(...e.reward, 1e-9);
  let h = "";
  for (let i = 0; i < S.max; i++) {
    if (i >= e.len) { h += `<b style="height:2px;background:transparent"></b>`; continue; }
    const c = e.clicked[i];
    const ht = c >= 0 ? 25 + 75 * (e.reward[i] / maxR) : 12;
    const col = c >= 0 ? qualityColor(e.quality[i][c]) : "#3a3a4c";
    h += `<b data-i="${i}" style="height:${ht.toFixed(0)}%;background:${col}"></b>`;
  }
  film.innerHTML = h + `<span class="ph"></span>`;
  $(".fl-r", p).textContent = `${e.len} steps`;
}
function paneSetup(side) {
  const p = $(side === "L" ? "#paneL" : "#paneR");
  const a = side === "L" ? S.left : S.right;
  p.style.setProperty("--c", agentColor(a));
  $(".dot", p).style.setProperty("--c", agentColor(a));
  $(".role", p).textContent = ROLE[a];
  $(".agent-sel", p).value = a;
  buildFilm(p, sess(a));
}
function renderPane(side, animate) {
  const p = $(side === "L" ? "#paneL" : "#paneR");
  const a = side === "L" ? S.left : S.right;
  const e = sess(a);
  const t = S.t;
  const screen = $(".screen", p);
  const ended = t >= e.len;
  const i = Math.min(t, e.len - 1);
  screen.className = "screen";
  if (ended) {
    screen.classList.add("ended");
    screen.innerHTML = `<div class="overlay"><span class="tag">Session over</span><div class="big">Viewer left after ${e.len} steps</div><div class="sub">Total watch time <b>${fmt(e.total)}</b> &middot; ${e.clicks} videos watched</div></div>`;
    $(".slate", p).innerHTML = "";
    $(".sl-r", p).textContent = "";
  } else {
    const c = e.clicked[i];
    const clusters = e.clusters[i], qs = e.quality[i], ints = e.interests[i];
    if (c >= 0) {
      const topic = clusters[c];
      screen.classList.add(animate ? "playing" : "still");
      screen.innerHTML = `<div class="cover" style="background:${coverBg(topic)}">${coverSVG(topic, i * 3 + c)}</div>
        <div class="overlay"><span class="tag live">&#9654; Watching</span><div class="big">${topicName(topic)}</div>
        <div class="sub">quality ${fmt(qs[c])} &middot; viewer's taste for this topic ${fmt(ints[topic])}</div></div>
        <span class="delta">+${fmt(e.reward[i])}</span><div class="prog"><i></i></div>`;
      if (!animate) $(".prog i", screen).style.width = "100%";
    } else {
      screen.classList.add("idle");
      const topic = clusters[0];
      screen.innerHTML = `<div class="cover" style="background:${coverBg(topic)}">${coverSVG(topic, i * 3)}</div>
        <div class="overlay"><span class="tag">Scrolled past</span><div class="big">Nothing watched this step</div><div class="sub">The viewer skipped all ${clusters.length} videos; skipping still costs time budget.</div></div>`;
    }
    $(".sl-r", p).textContent = `step ${i + 1}`;
    $(".slate", p).innerHTML = clusters.map((topic, j) => {
      const q = qs[j], it = ints[topic];
      const w = Math.min(50, Math.abs(it) * 50).toFixed(0);
      const cls = c === j ? "clicked" : c >= 0 ? "skipped" : "skipped";
      return `<div class="vcard ${cls}"><div class="thumb" style="background:${coverBg(topic)}">${coverSVG(topic, i * 3 + j)}${c === j ? '<span class="badge">WATCHED</span>' : ""}</div>
        <div class="meta"><div class="title">${topicName(topic)}</div>
        <span class="q ${q >= 0 ? "pos" : "neg"}" title="Hidden quality. Watching high-quality videos gives time budget back; low quality costs extra."><span class="qw">${q >= 0 ? "good for session" : "drains session"} </span>${fmt(q)}</span>
        <div class="match" title="Viewer's current taste for this topic (−1 to 1)"><i class="${it >= 0 ? "p" : "n"}" style="width:${w}%"></i></div>
        <div class="match-l">taste ${fmt(it)}</div></div></div>`;
    }).join("");
  }
  const cum = ended ? e.total : e.cum[i];
  const clicks = ended ? e.clicks : e.clk[i];
  const steps = ended ? e.len : i + 1;
  const bud = ended ? Math.max(0, e.budget[e.len - 1]) : Math.max(0, e.budget[i]);
  $(".w", p).textContent = fmt(cum);
  $(".c", p).textContent = clicks;
  $(".s", p).textContent = steps;
  const frac = Math.max(0, Math.min(1, bud / BMAX));
  const bar = $(".bt i", p);
  bar.style.width = (frac * 100).toFixed(1) + "%";
  bar.style.background = `hsl(${(frac * 130).toFixed(0)} 70% 52%)`;
  $(".bv", p).textContent = `${fmt(bud, 1)} left`;
  const film = $(".film", p);
  $$("b", film).forEach((b) => b.classList.toggle("on", b.dataset.i !== undefined && +b.dataset.i <= Math.min(t, e.len - 1)));
  const ph = $(".ph", film);
  ph.style.left = `calc(4px + ${(Math.min(t, S.max) / S.max) * 100}% - ${(Math.min(t, S.max) / S.max) * 8}px)`;
}
function renderDuelVerdict() {
  const box = $("#duel-verdict");
  const L = sess(S.left), R = sess(S.right);
  if (S.t < Math.max(L.len, R.len)) { box.hidden = true; return; }
  box.hidden = false;
  if (S.left === S.right) { box.innerHTML = "Pick two different recommenders to compare."; return; }
  const d = L.total - R.total;
  const win = d >= 0 ? S.left : S.right, lose = d >= 0 ? S.right : S.left;
  const g = gapFor(S.left, S.right);
  const avg = g ? `<span class="small">Over all ${SITE.frozen.eval_episodes} test viewers and 5 seeds (N = ${CELL[0]}, k = ${CELL[1]}), the average difference ${esc(NAME[S.left])} ${MINUS} ${esc(NAME[S.right])} is <b>${sgn(g.v)}</b> watch time per session (${verdictWords(g.verdict, g.flip)}). One viewer is an example; the averages are the evidence.</span>` : `<span class="small">One viewer is an example; the averages on the Findings page are the evidence.</span>`;
  box.innerHTML = Math.abs(d) < 1e-9
    ? `<b>Tie:</b> both recommenders gave this viewer ${fmt(L.total)} watch time.${avg}`
    : `<b>${esc(NAME[win])}</b> kept this viewer watching <b>${fmt(Math.abs(d))}</b> longer than ${esc(NAME[lose])} (${fmt(Math.max(L.total, R.total))} vs ${fmt(Math.min(L.total, R.total))}).${avg}`;
}
/* Average gap between two agents in the replay cell, from the rq2 table (either sign order). */
function gapFor(a, b) {
  const lab = { slateq: "SlateQ", learned_myopic: "learned-myopic", oracle_myopic: "oracle-myopic", random: "random" };
  const rows = SITE.rq2.gaps.filter((r) => r.condition === "matched" && isCell(r, ...CELL));
  let r = rows.find((x) => x.comparison === `${lab[a]} - ${lab[b]}`);
  if (r) return { v: r.mean_diff, verdict: r.verdict, flip: false };
  r = rows.find((x) => x.comparison === `${lab[b]} - ${lab[a]}`);
  if (r) return { v: -r.mean_diff, verdict: r.verdict, flip: true };
  const ma = SITE.rq2.agents.find((x) => x.condition === "matched" && isCell(x, ...CELL) && x.agent === a);
  const mb = SITE.rq2.agents.find((x) => x.condition === "matched" && isCell(x, ...CELL) && x.agent === b);
  return ma && mb ? { v: ma.mean_total_reward - mb.mean_total_reward, verdict: null } : null;
}
function verdictWords(v, flip) {
  if (!v) return "no paired test for this pair";
  if (v === "no clear difference") return "no clear difference by the pre-registered rule";
  const hi = (v === "A higher") !== !!flip;
  return `clear by the pre-registered rule: the first is ${hi ? "higher" : "lower"}`;
}

/* ================================================================ race */
function buildRace() {
  $("#lanes").innerHTML = AGENTS.map((a) => `
    <div class="lane" data-a="${a}" style="--c:${agentColor(a)}">
      <div class="who"><span class="dot"></span><div>${NAME[a]}<small>${ROLE[a].split(" (")[0]}</small></div></div>
      <div class="track"><div class="rail"></div><div class="trail"></div><div class="runner"></div><div class="bud"><i></i></div></div>
      <div class="score"><div class="v">0</div><small>watch time</small></div>
      <div class="status"></div>
    </div>`).join("");
}
function renderRace() {
  const top = Math.max(...AGENTS.map((a) => sess(a).total));
  for (const a of AGENTS) {
    const e = sess(a), lane = $(`.lane[data-a="${a}"]`);
    const ended = S.t >= e.len, i = Math.min(S.t, e.len - 1);
    const cum = ended ? e.total : e.cum[i];
    const x = (cum / top) * 100;
    $(".runner", lane).style.left = x + "%";
    $(".runner", lane).classList.toggle("done", ended);
    $(".trail", lane).style.width = x + "%";
    const bud = Math.max(0, ended ? 0 : e.budget[i]);
    $(".bud i", lane).style.width = ((bud / BMAX) * 100).toFixed(1) + "%";
    $(".score .v", lane).textContent = fmt(cum);
    let st;
    if (ended) st = `Left after ${e.len} steps · ${e.clicks} videos watched`;
    else if (e.clicked[i] >= 0) { const tp = e.clusters[i][e.clicked[i]]; st = `Step ${i + 1}: watching ${topicName(tp)} (quality ${fmt(e.quality[i][e.clicked[i]])})`; }
    else st = `Step ${i + 1}: skipped all ${e.clusters[i].length} videos`;
    $(".status", lane).textContent = st;
  }
  const pod = $("#podium");
  if (S.t >= S.max) {
    const order = [...AGENTS].sort((a, b) => sess(b).total - sess(a).total);
    pod.hidden = false;
    pod.innerHTML = order.map((a, r) => `<div class="pl" style="--c:${agentColor(a)};animation-delay:${r * 0.08}s"><div class="rk">#${r + 1}</div><div class="nm">${NAME[a]}</div><div class="vv">${fmt(sess(a).total)}</div><div class="ss">${sess(a).len} steps · ${sess(a).clicks} watched</div></div>`).join("")
      + `<p class="fineprint" style="grid-column:1/-1">This ranking is for this one viewer. Some viewers favour a different recommender; the averages over all test viewers are on the Findings page.</p>`;
  } else pod.hidden = true;
}

/* ================================================================ taste */
function interestColor(v) {
  const t = Math.max(-1, Math.min(1, v));
  if (t >= 0) return [30 + (245 - 30) * t, 30 + (158 - 30) * t, 44 + (11 - 44) * t];
  return [30 + (37 - 30) * -t, 30 + (99 - 30) * -t, 44 + (235 - 44) * -t];
}
/* Value drawn in the taste view: the interest itself, or its change since step 1 scaled to the
   largest change among the four sessions of this viewer (so small drifts are visible). */
function tasteScale() {
  let m = 1e-9;
  for (const a of AGENTS) { const I = sess(a).interests; for (const row of I) row.forEach((v, k) => { m = Math.max(m, Math.abs(v - I[0][k])); }); }
  return m;
}
function tasteVal(e, x, y, D) { return S.taste === "abs" ? e.interests[x][y] : (e.interests[x][y] - e.interests[0][y]) / D; }
function buildTaste() {
  const D = tasteScale();
  $("#lg-lo").textContent = S.taste === "abs" ? "dislike" : "likes less than at start";
  $("#lg-hi").textContent = S.taste === "abs" ? "like" : `likes more (largest change ${fmt(D)})`;
  $("#tastes").innerHTML = AGENTS.map((a) => `
    <div class="taste" data-a="${a}" style="--c:${agentColor(a)}">
      <h3><span class="dot"></span>${NAME[a]}<small></small></h3>
      <div class="heat"><canvas></canvas><span class="ph"></span></div>
      <div class="now"></div><div class="nowl">taste right now, topic 01 → 20</div>
    </div>`).join("");
  for (const a of AGENTS) {
    const e = sess(a), box = $(`.taste[data-a="${a}"]`), cv = $("canvas", box);
    const W = S.max, H = 20, sc = 4;
    cv.width = W * sc; cv.height = H * sc;
    const ctx = cv.getContext("2d");
    ctx.fillStyle = "#0c0c13"; ctx.fillRect(0, 0, cv.width, cv.height);
    for (let x = 0; x < e.len; x++) for (let y = 0; y < H; y++) {
      const [r, g, b] = interestColor(tasteVal(e, x, y, D));
      ctx.fillStyle = `rgb(${r | 0},${g | 0},${b | 0})`;
      ctx.fillRect(x * sc, y * sc, sc, sc);
    }
    ctx.fillStyle = "#fff";
    for (let x = 0; x < e.len; x++) {
      const c = e.clicked[x];
      if (c >= 0) { const y = e.clusters[x][c]; ctx.beginPath(); ctx.arc(x * sc + sc / 2, y * sc + sc / 2, sc * 0.38, 0, 7); ctx.fill(); }
    }
    $("h3 small", box).textContent = `${e.len} steps · total watch ${fmt(e.total)}`;
  }
}
function renderTaste() {
  const D = tasteScale();
  for (const a of AGENTS) {
    const e = sess(a), box = $(`.taste[data-a="${a}"]`);
    const i = Math.min(S.t, e.len - 1);
    $(".ph", box).style.left = ((Math.min(S.t, S.max) / S.max) * 100).toFixed(2) + "%";
    $(".now", box).innerHTML = e.interests[i].map((v, k) => { const [r, g, b] = interestColor(tasteVal(e, i, k, D)); return `<i title="${topicName(k)}: taste ${fmt(v)}, change ${sgn(v - e.interests[0][k])}" style="background:rgb(${r | 0},${g | 0},${b | 0})"></i>`; }).join("");
  }
}

/* ================================================================ session + transport */
function buildSession() {
  const lens = S.view === "watch" ? [sess(S.left).len, sess(S.right).len] : AGENTS.map((a) => sess(a).len);
  S.max = Math.max(...lens);
  if (S.t > S.max) S.t = S.max;
  $("#tp-scrub").max = S.max;
  if (S.view === "watch") { paneSetup("L"); paneSetup("R"); }
  if (S.view === "race") buildRace();
  if (S.view === "taste") buildTaste();
  render(false);
}
function render(animate) {
  if (!sess(S.left)) return;
  $("#tp-scrub").value = S.t;
  $("#tp-step").textContent = S.t >= S.max ? "session over" : `step ${S.t + 1} / ${S.max}`;
  if (S.view === "watch") { renderPane("L", animate); renderPane("R", animate); renderDuelVerdict(); }
  if (S.view === "race") renderRace();
  if (S.view === "taste") renderTaste();
}
const stepMs = () => (reduceMotion ? 700 : 900) / S.speed;
function tick() {
  if (!S.playing) return;
  if (S.t >= S.max) { pause(); return; }
  S.t++;
  render(true);
  S.timer = setTimeout(tick, stepMs());
}
function play() {
  if (S.t >= S.max) S.t = 0;
  S.playing = true;
  $("#tp-play").classList.add("on");
  $("#tp-play").setAttribute("aria-label", "Pause");
  document.documentElement.style.setProperty("--step-ms", stepMs() * 0.9 + "ms");
  render(true);
  clearTimeout(S.timer);
  S.timer = setTimeout(tick, stepMs());
}
function pause() {
  S.playing = false;
  clearTimeout(S.timer);
  $("#tp-play").classList.remove("on");
  $("#tp-play").setAttribute("aria-label", "Play");
}
function seek(t) { S.t = Math.max(0, Math.min(S.max, t)); render(false); }
function initTasteMode() {
  $$("#taste-mode .chip").forEach((b) => b.addEventListener("click", () => {
    S.taste = b.dataset.mode;
    $$("#taste-mode .chip").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    if (S.view === "taste") buildSession();
  }));
}
function initTransport() {
  $("#tp-play").addEventListener("click", () => (S.playing ? pause() : play()));
  $("#tp-back").addEventListener("click", () => { pause(); seek(S.t - 1); });
  $("#tp-fwd").addEventListener("click", () => { pause(); seek(S.t + 1); });
  $("#tp-restart").addEventListener("click", () => { pause(); seek(0); });
  $("#tp-scrub").addEventListener("input", (e) => { pause(); seek(+e.target.value); });
  $("#tp-speed").addEventListener("change", (e) => {
    S.speed = +e.target.value;
    document.documentElement.style.setProperty("--step-ms", stepMs() * 0.9 + "ms");
  });
  document.addEventListener("keydown", (e) => {
    if ($("#modal").open || !["watch", "race", "taste"].includes(S.view)) return;
    const tag = document.activeElement.tagName;
    if (["INPUT", "SELECT", "TEXTAREA"].includes(tag) && e.key !== " ") return;
    if (e.key === " " && ["BUTTON", "SELECT"].includes(tag)) return;
    if (e.key === " ") { e.preventDefault(); S.playing ? pause() : play(); }
    if (e.key === "ArrowRight") { pause(); seek(S.t + 1); }
    if (e.key === "ArrowLeft") { pause(); seek(S.t - 1); }
  });
}

/* ================================================================ views */
function showView(v) {
  if (!document.getElementById(v)) v = "watch";
  pause();
  S.view = v;
  $$(".view").forEach((s) => (s.hidden = s.id !== v));
  $$(".nav button").forEach((b) => (b.getAttribute("data-view") === v ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current")));
  const replay = ["watch", "race", "taste"].includes(v);
  $("#viewer-bar").hidden = !replay;
  $("#transport").hidden = !replay;
  document.body.style.paddingBottom = replay ? "" : "0";
  if (location.hash.slice(1) !== v) history.replaceState(null, "", "#" + v);
  if (replay && sess(S.left)) buildSession();
  window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
}
function initNav() {
  $$("[data-view]").forEach((b) => b.addEventListener("click", (e) => { e.preventDefault(); showView(b.getAttribute("data-view")); }));
  window.addEventListener("hashchange", () => showView(location.hash.slice(1)));
}

/* ================================================================ findings: lookups */
const gaps = (sec) => SITE[sec].gaps;
const findGap = (sec, cmp, n, k, cond = "matched") => gaps(sec).find((r) => r.condition === cond && r.comparison === cmp && isCell(r, n, k));
const findAgent = (sec, a, n, k, cond = "matched") => SITE[sec].agents.find((r) => r.condition === cond && r.agent === a && isCell(r, n, k));
function pill(v, aLabel) {
  if (v === "A higher") return `<span class="pill yes">clear: ${esc(aLabel || "first")} higher</span>`;
  if (v === "A lower") return `<span class="pill lo">clear: ${esc(aLabel || "first")} lower</span>`;
  if (v === "no clear difference") return `<span class="pill no">no clear difference</span>`;
  return `<span class="pill no">${esc(v || "n/a")}</span>`;
}
const ci = (r) => `95% CI [${sgn(r.ci95_low)}, ${sgn(r.ci95_high)}]`;

/* ================================================================ charts (inline SVG) */
/* Horizontal bars with 95% CI whiskers. rows: {label, sub, mean, lo, hi, color} */
function hbars(rows, opt = {}) {
  const W = 640, L = opt.labelW || 230, R = 70, rowH = 40, top = 10;
  const H = top + rows.length * rowH + 26;
  const vals = rows.flatMap((r) => [r.mean, r.lo, r.hi, 0]).filter((v) => v !== null && v !== undefined);
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.08 || 1; lo -= lo < 0 ? pad : 0; hi += pad;
  const X = (v) => L + ((v - lo) / (hi - lo)) * (W - L - R);
  let s = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opt.aria || "bar chart")}">`;
  s += `<line class="zero" x1="${X(0)}" x2="${X(0)}" y1="${top - 4}" y2="${H - 22}"/>`;
  rows.forEach((r, i) => {
    const y = top + i * rowH + 8, c = r.color || "#22d3ee";
    s += `<text class="lab" x="0" y="${y + 9}">${esc(r.label)}</text>`;
    if (r.sub) s += `<text x="0" y="${y + 24}" font-size="11">${esc(r.sub)}</text>`;
    if (r.mean === null || r.mean === undefined) return;
    const x0 = X(Math.min(0, r.mean)), x1 = X(Math.max(0, r.mean));
    s += `<rect x="${x0}" y="${y}" width="${Math.max(1, x1 - x0)}" height="18" rx="4" fill="${c}" fill-opacity=".85"><title>${esc(r.label)}: ${sgn(r.mean)}${r.lo !== undefined ? ` (95% CI ${sgn(r.lo)} to ${sgn(r.hi)})` : ""}</title></rect>`;
    if (r.lo !== undefined && r.lo !== null) {
      s += `<line x1="${X(r.lo)}" x2="${X(r.hi)}" y1="${y + 9}" y2="${y + 9}" stroke="#fff" stroke-width="1.6"/>`;
      s += `<line x1="${X(r.lo)}" x2="${X(r.lo)}" y1="${y + 3}" y2="${y + 15}" stroke="#fff" stroke-width="1.6"/><line x1="${X(r.hi)}" x2="${X(r.hi)}" y1="${y + 3}" y2="${y + 15}" stroke="#fff" stroke-width="1.6"/>`;
    }
    const tx = Math.max(X(r.mean), r.hi !== undefined && r.hi !== null ? X(r.hi) : 0) + 6;
    s += `<text class="val" x="${Math.min(tx, W - 4)}" y="${y + 14}" ${tx > W - 60 ? 'text-anchor="end"' : ""}>${opt.fmt ? opt.fmt(r.mean) : sgn(r.mean)}</text>`;
  });
  s += `<text x="${X(0)}" y="${H - 6}" text-anchor="middle" font-size="11">0</text>`;
  if (opt.axis) s += `<text x="${W - R}" y="${H - 6}" text-anchor="end" font-size="11">${esc(opt.axis)}</text>`;
  return s + "</svg>";
}
/* Vertical grouped bars: groups [{label, bars:[{mean, lo, hi, color, name}]}] */
function vbars(groups, opt = {}) {
  const W = opt.w || 640, H = opt.h || 280, L = 46, B = 40, T = 16, R = 10;
  const vals = groups.flatMap((g) => g.bars.flatMap((b) => [b.mean, b.lo, b.hi])).filter((v) => v !== null && v !== undefined);
  let lo = Math.min(0, ...vals), hi = Math.max(0, ...vals);
  hi += (hi - lo) * 0.12 || 1;
  const Y = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  const gw = (W - L - R) / groups.length;
  let s = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opt.aria || "bar chart")}">`;
  for (let k = 0; k <= 4; k++) { const v = lo + ((hi - lo) * k) / 4; s += `<line class="axis" x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}"/><text x="${L - 6}" y="${Y(v) + 4}" text-anchor="end" font-size="11">${fmt(v, Math.abs(hi - lo) < 5 ? 2 : 0)}</text>`; }
  s += `<line class="zero" x1="${L}" x2="${W - R}" y1="${Y(0)}" y2="${Y(0)}"/>`;
  groups.forEach((g, gi) => {
    const n = g.bars.length, bw = Math.min(46, (gw - 16) / n);
    const x0 = L + gi * gw + (gw - bw * n) / 2;
    g.bars.forEach((b, bi) => {
      if (b.mean === null || b.mean === undefined) return;
      const x = x0 + bi * bw + 2, y = Math.min(Y(0), Y(b.mean)), h = Math.abs(Y(b.mean) - Y(0));
      s += `<rect x="${x}" y="${y}" width="${bw - 4}" height="${Math.max(1, h)}" rx="4" fill="${b.color}" fill-opacity="${g.dim ? 0.35 : 0.9}"><title>${esc(g.label)} ${esc(b.name || "")}: ${sgn(b.mean)}</title></rect>`;
      if (b.lo !== undefined) s += `<line x1="${x + (bw - 4) / 2}" x2="${x + (bw - 4) / 2}" y1="${Y(b.lo)}" y2="${Y(b.hi)}" stroke="#fff" stroke-width="1.5"/>`;
      if (opt.labels !== false) s += `<text class="val" x="${x + (bw - 4) / 2}" y="${(b.mean >= 0 ? Math.min(Y(b.mean), b.hi !== undefined ? Y(b.hi) : 1e9) - 5 : Math.max(Y(b.mean), b.lo !== undefined ? Y(b.lo) : 0) + 14)}" text-anchor="middle" font-size="11">${opt.fmt ? opt.fmt(b.mean) : sgn(b.mean, 1)}</text>`;
    });
    s += `<text class="lab" x="${L + gi * gw + gw / 2}" y="${H - 16}" text-anchor="middle">${esc(g.label)}</text>`;
    if (g.sub) s += `<text x="${L + gi * gw + gw / 2}" y="${H - 3}" text-anchor="middle" font-size="10">${esc(g.sub)}</text>`;
  });
  if (opt.y) s += `<text x="4" y="10" font-size="11">${esc(opt.y)}</text>`;
  return s + "</svg>";
}
/* Line chart with categorical x. series [{name, color, pts:[{x, mean, lo, hi}]}] */
function lines(xs, series, opt = {}) {
  const W = 640, H = 290, L = 50, B = 40, T = 16, R = 120;
  const vals = series.flatMap((s) => s.pts.flatMap((p) => [p.mean, p.lo, p.hi])).filter((v) => v !== null && v !== undefined);
  let lo = Math.min(0, ...vals), hi = Math.max(0, ...vals); hi += (hi - lo) * 0.08;
  const X = (i) => L + (i / (xs.length - 1)) * (W - L - R);
  const Y = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  let s = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opt.aria || "line chart")}">`;
  for (let k = 0; k <= 4; k++) { const v = lo + ((hi - lo) * k) / 4; s += `<line class="axis" x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}"/><text x="${L - 6}" y="${Y(v) + 4}" text-anchor="end" font-size="11">${fmt(v, 0)}</text>`; }
  s += `<line class="zero" x1="${L}" x2="${W - R}" y1="${Y(0)}" y2="${Y(0)}"/>`;
  xs.forEach((x, i) => (s += `<text class="lab" x="${X(i)}" y="${H - 16}" text-anchor="middle">${esc(x)}</text>`));
  if (opt.x) s += `<text x="${(L + W - R) / 2}" y="${H - 2}" text-anchor="middle" font-size="11">${esc(opt.x)}</text>`;
  series.forEach((se) => {
    const pts = se.pts.map((p, i) => (p ? { ...p, i } : null)).filter((p) => p && p.mean !== null && p.mean !== undefined);
    s += `<polyline fill="none" stroke="${se.color}" stroke-width="2.5" points="${pts.map((p) => `${X(p.i)},${Y(p.mean)}`).join(" ")}"/>`;
    pts.forEach((p) => {
      if (p.lo !== undefined) s += `<line x1="${X(p.i)}" x2="${X(p.i)}" y1="${Y(p.lo)}" y2="${Y(p.hi)}" stroke="${se.color}" stroke-width="1.5" stroke-opacity=".7"/>`;
      s += `<circle cx="${X(p.i)}" cy="${Y(p.mean)}" r="5" fill="${se.color}"><title>${esc(se.name)} at ${esc(xs[p.i])}: ${sgn(p.mean)}</title></circle>`;
    });
    const last = pts[pts.length - 1];
    if (last) s += `<text x="${X(last.i) + 10}" y="${Y(last.mean) + 4}" class="lab" style="fill:${se.color}">${esc(se.name)}</text>`;
  });
  if (opt.y) s += `<text x="4" y="10" font-size="11">${esc(opt.y)}</text>`;
  return s + "</svg>";
}

/* ================================================================ findings: cards */
function artSVG(seed) {
  const r = rng(seed * 101 + 3);
  const h = (seed * 53 + 250) % 360;
  let s = `<svg class="bg" viewBox="0 0 320 160" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><linearGradient id="ga${seed}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="hsl(${h} 70% 42%)"/><stop offset="1" stop-color="hsl(${(h + 70) % 360} 75% 14%)"/></linearGradient></defs><rect width="320" height="160" fill="url(#ga${seed})"/>`;
  for (let i = 0; i < 6; i++) s += `<circle cx="${(r() * 320).toFixed(0)}" cy="${(r() * 160).toFixed(0)}" r="${(20 + r() * 70).toFixed(0)}" fill="#fff" fill-opacity="${(0.03 + r() * 0.07).toFixed(2)}"/>`;
  return s + `<rect y="80" width="320" height="80" fill="#000" fill-opacity=".25"/></svg>`;
}
const CARDS = [];
function card(row, id, o) { CARDS.push({ row, id, ...o }); }

function defineCards() {
  const [n0, k0] = CELL;
  const g1 = findGap("rq2", PRIMARY, n0, k0);
  const g1o = findGap("rq2", "SlateQ - oracle-myopic", n0, k0);
  const g1lo = findGap("rq2", "learned-myopic - oracle-myopic", n0, k0);

  card("main", "rq1", {
    kicker: "RQ1", title: "Planning beats click-chasing", blurb: "Does SlateQ keep viewers watching longer than a recommender that chases the next click?",
    num: () => sgn(g1.mean_diff), unit: `watch time per session (N=${n0}, k=${k0})`, verdict: () => pill(g1.verdict, "SlateQ"),
    detail: () => {
      const ags = AGENTS.map((a) => findAgent("rq2", a, n0, k0)).filter(Boolean);
      return `<p class="eyebrow">RQ1 &middot; replication of the SlateQ paper's simulation setting</p><h2 id="modal-title">Planning beats click-chasing, by a small but consistent margin</h2>
      <div class="bignum"><span class="n">${sgn(g1.mean_diff)}</span><span class="d">watch time per session, SlateQ ${MINUS} learned myopic<br>${ci(g1)} &middot; ${pct(g1.relative_to_b)} of the myopic baseline &middot; ${pill(g1.verdict, "SlateQ")}</span></div>
      ${hbars([
        { label: "SlateQ vs learned myopic", sub: "the fair comparison", mean: g1.mean_diff, lo: g1.ci95_low, hi: g1.ci95_high, color: agentColor("slateq") },
        { label: "SlateQ vs oracle myopic", sub: "vs the perfect click-chaser", mean: g1o.mean_diff, lo: g1o.ci95_low, hi: g1o.ci95_high, color: agentColor("oracle_myopic") },
        { label: "Learned vs oracle myopic", sub: "is the click-chaser well trained?", mean: g1lo.mean_diff, lo: g1lo.ci95_low, hi: g1lo.ci95_high, color: agentColor("learned_myopic") },
      ], { axis: "difference in watch time per session", aria: "RQ1 gaps" })}
      <h4>Average per test viewer</h4>${agentTable(ags)}
      <h4>What it shows</h4><ul>
        <li>SlateQ is clearly ahead of the learned click-chaser (${ci(g1)}, all 5 seeds agree) and of the perfect click-chaser (${sgn(g1o.mean_diff)}).</li>
        <li>The learned and perfect click-chasers are ${g1lo.verdict === "no clear difference" ? "not clearly different" : "different"} (${sgn(g1lo.mean_diff)}), so the gap is about planning, not a weak baseline.</li>
        <li>How: SlateQ's watched videos have higher hidden quality, which gives time back, so sessions last a little longer.</li></ul>
      <h4>What it does not show</h4><p class="not">The gain is small in relative terms, and it says nothing about real users or any real platform. The comparison repeats the SlateQ paper's own setting on purpose (a replication with stricter statistics).</p>`;
    },
  });

  const g80 = findGap("rq2", PRIMARY, 80, 3);
  card("main", "rq2", {
    kicker: "RQ2 · new", title: "More choice, bigger gap", blurb: "How does the advantage change with more candidates (N) and more videos shown (k)?",
    num: () => sgn(g80.mean_diff), unit: "watch time per session at N=80, k=3", verdict: () => {
      const grid = gaps("rq2").filter((r) => r.comparison === PRIMARY && !r.control);
      return `<span class="pill yes">clear in ${grid.filter((r) => r.verdict === "A higher").length} of ${grid.length} settings</span>`;
    },
    detail: () => rq2Detail(),
    after: () => rq2Wire(),
  });

  const r3 = RUNGS.map((c) => findGap("rq3", PRIMARY, n0, k0, c));
  const sev = r3[3];
  card("main", "rq3", {
    kicker: "RQ3", title: "When viewers behave differently", blurb: "SlateQ assumes how viewers choose. What if they choose differently?",
    num: () => sgn(sev.mean_diff), unit: "gap under the most different behaviour", verdict: () => pill(sev.verdict, "SlateQ"),
    detail: () => `<p class="eyebrow">RQ3 &middot; stretch goal</p><h2 id="modal-title">The advantage survives mild and moderate mismatch, not the severe one</h2>
      ${hbars(r3.map((r, i) => ({ label: RUNG[RUNGS[i]], sub: r.verdict === "A higher" ? "clear" : "no clear difference", mean: r.mean_diff, lo: r.ci95_low, hi: r.ci95_high, color: i < 3 ? agentColor("slateq") : "#94a3b8" })), { labelW: 270, axis: "SlateQ − learned myopic", aria: "RQ3 ladder" })}
      <h4>What it shows</h4><ul>${r3.map((r, i) => `<li><b>${RUNG[RUNGS[i]]}:</b> ${sgn(r.mean_diff)} (${ci(r)}), ${r.verdict === "A higher" ? "clear" : "no clear difference"}.</li>`).join("")}
      <li>Under the severe cascade, watch time drops for every recommender (random: ${fmt(findAgent("rq3", "random", n0, k0, "severe_cascade").mean_total_reward)} vs ${fmt(findAgent("rq3", "random", n0, k0, "matched").mean_total_reward)} when users behave as assumed).</li></ul>
      <h4>What it does not show</h4><p class="not">Only one cascade setting was run, so it does not show which part of the cascade removes the advantage. It does not mean the SlateQ paper was wrong: the paper's cascade is different and milder (see the E4 card).</p>`,
  });

  /* ---- exploratory follow-ups ---- */
  const e1 = (c, n) => findGap("phase6b", c, n, 3);
  const E1a = "E1: SlateQ - learned-myopic, both lr 1e-3", E1b = "E1: SlateQ - learned-myopic, both lr 2.5e-4";
  card("follow", "e1", {
    kicker: "E1", explo: true, title: "Same learning speed", blurb: "Is the win only because the two agents used different learning rates?",
    num: () => sgn(e1(E1b, 80).mean_diff), unit: "N=80, k=3, both at the same learning rate", verdict: () => {
      const all = [e1(E1a, 10), e1(E1b, 10), e1(E1a, 80), e1(E1b, 80)];
      return `<span class="pill ${all.every((r) => r.verdict === "A higher") ? "yes" : "no"}">clear in ${all.filter((r) => r.verdict === "A higher").length} of ${all.length}</span>`;
    },
    detail: () => {
      const rows = [10, 80].flatMap((n) => [
        { label: `N=${n}: both lr 1e-3`, mean: e1(E1a, n).mean_diff, lo: e1(E1a, n).ci95_low, hi: e1(E1a, n).ci95_high, color: agentColor("slateq"), sub: e1(E1a, n).verdict },
        { label: `N=${n}: both lr 2.5e-4`, mean: e1(E1b, n).mean_diff, lo: e1(E1b, n).ci95_low, hi: e1(E1b, n).ci95_high, color: "#a78bfa", sub: e1(E1b, n).verdict },
        { label: `N=${n}: own tuned lr (RQ2)`, mean: findGap("rq2", PRIMARY, n, 3).mean_diff, lo: findGap("rq2", PRIMARY, n, 3).ci95_low, hi: findGap("rq2", PRIMARY, n, 3).ci95_high, color: "#64748b", sub: "main result, for reference" },
      ]);
      return `<p class="eyebrow">E1 &middot; exploratory follow-up</p><h2 id="modal-title">The win is not a learning-rate artefact</h2>
      ${hbars(rows, { axis: "SlateQ − learned myopic", aria: "E1" })}
      <h4>What it shows</h4><ul><li>With both agents at the same learning rate, SlateQ is still clearly ahead at N=10 and N=80, at both learning rates.</li></ul>
      <h4>What it does not show</h4><p class="not">The <i>size</i> of the gap at N=80 still depends on the learning rate; only its direction is robust.</p>`;
    },
  });

  const GAM = ["0", "0.5", "0.9", "0.95", "0.99"];
  const e2 = (g, n) => g === "0" ? findGap("phase6b", "E1: learned-myopic (lr 1e-3) - oracle-myopic", n, 3) : findGap("phase6b", `E2: gamma ${g} - oracle-myopic`, n, 3);
  card("follow", "e2", {
    kicker: "E2", explo: true, title: "How far to look ahead", blurb: "SlateQ with different planning horizons (γ), compared with the perfect click-chaser.",
    num: () => sgn(e2("0.95", 80).mean_diff), unit: "γ = 0.95 vs perfect click-chaser, N=80", verdict: () => pill(e2("0.95", 80).verdict, "γ 0.95"),
    detail: () => `<p class="eyebrow">E2 &middot; exploratory follow-up</p><h2 id="modal-title">More look-ahead helps, then levels off</h2>
      ${lines(GAM.map((g) => "γ " + g), [80, 10].map((n) => ({ name: `N=${n}, k=3`, color: n === 80 ? agentColor("slateq") : "#a78bfa", pts: GAM.map((g) => { const r = e2(g, n); return r ? { mean: r.mean_diff, lo: r.ci95_low, hi: r.ci95_high } : null; }) })), { y: "watch time vs perfect click-chaser", x: "planning horizon γ (0 = no planning)", aria: "E2 horizon curve" })}
      <div class="tbl-wrap"><table class="tbl"><tr><th class="nocase">γ</th>${GAM.map((g) => `<th>${g}</th>`).join("")}</tr>${[10, 80].map((n) => `<tr><td>N=${n}</td>${GAM.map((g) => { const r = e2(g, n); return `<td>${r ? sgn(r.mean_diff) : "n/a"}</td>`; }).join("")}</tr>`).join("")}</table></div>
      <h4>What it shows</h4><ul><li>Every γ above 0 is clearly ahead of the perfect click-chaser in both settings.</li><li>The gain rises with γ and levels off between 0.95 and 0.99.</li></ul>
      <h4>What it does not show</h4><p class="not">No "best γ" is claimed: only these five values were run and no curve is fitted.</p>`,
  });

  const E3 = ["E3: SlateQ - learned-myopic, both 600K steps", "E3: SlateQ (600K) - oracle-myopic", "E3: learned-myopic (600K) - oracle-myopic", "E3: learned-myopic 600K - 300K", "E3: SlateQ 600K - 300K"];
  const E3L = ["SlateQ vs learned myopic (600K)", "SlateQ (600K) vs oracle", "Learned myopic (600K) vs oracle", "Learned myopic: 600K vs 300K", "SlateQ: 600K vs 300K"];
  card("follow", "e3", {
    kicker: "E3", explo: true, title: "Twice the training", blurb: "Was the click-chaser just under-trained with 80 candidates?",
    num: () => sgn(findGap("phase6b", E3[2], 80, 3).mean_diff), unit: "learned vs perfect click-chaser after 600K steps", verdict: () => pill(findGap("phase6b", E3[2], 80, 3).verdict, "learned"),
    detail: () => {
      const lmo = findGap("rq2", "learned-myopic - oracle-myopic", 80, 3);
      return `<p class="eyebrow">E3 &middot; exploratory follow-up (N=80, k=3)</p><h2 id="modal-title">Partly under-training; the main result holds</h2>
      ${hbars(E3.map((c, i) => { const r = findGap("phase6b", c, 80, 3); return { label: E3L[i], sub: r.verdict, mean: r.mean_diff, lo: r.ci95_low, hi: r.ci95_high, color: i < 2 ? agentColor("slateq") : i < 4 ? agentColor("learned_myopic") : "#a78bfa" }; }), { labelW: 270, axis: "difference in watch time", aria: "E3" })}
      <h4>What it shows</h4><ul><li>With 300K steps the learned click-chaser was ${sgn(lmo.mean_diff)} behind the perfect one; with 600K it is ${sgn(findGap("phase6b", E3[2], 80, 3).mean_diff)} (${findGap("phase6b", E3[2], 80, 3).verdict}).</li>
      <li>SlateQ barely changes with more training, and stays clearly ahead of both click-chasers.</li></ul>
      <h4>What it does not show</h4><p class="not">Two training budgets only. Most seeds still put the learned click-chaser behind, so under-training may not be the whole story.</p>`;
    },
  });

  const e4 = (c) => findGap("phase6b", c, n0, k0, "paper_cascade");
  card("follow", "e4", {
    kicker: "E4", explo: true, title: "The paper's own cascade", blurb: "The SlateQ paper used a milder top-down viewer model. Does the win come back?",
    num: () => sgn(e4("E4: SlateQ - learned-myopic").mean_diff), unit: "SlateQ vs learned myopic, paper's cascade", verdict: () => pill(e4("E4: SlateQ - learned-myopic").verdict, "SlateQ"),
    detail: () => {
      const pr = SITE.phase6b.agents.find((r) => r.condition === "paper_cascade" && r.agent === "random");
      return `<p class="eyebrow">E4 &middot; exploratory follow-up</p><h2 id="modal-title">Under the paper's cascade the advantage is clear again</h2>
      ${hbars([
        { label: "RecSim's cascade (RQ3)", sub: sev.verdict, mean: sev.mean_diff, lo: sev.ci95_low, hi: sev.ci95_high, color: "#94a3b8" },
        { label: "Paper's cascade: vs learned", sub: e4("E4: SlateQ - learned-myopic").verdict, mean: e4("E4: SlateQ - learned-myopic").mean_diff, lo: e4("E4: SlateQ - learned-myopic").ci95_low, hi: e4("E4: SlateQ - learned-myopic").ci95_high, color: agentColor("slateq") },
        { label: "Paper's cascade: vs oracle", sub: e4("E4: SlateQ - oracle-myopic").verdict, mean: e4("E4: SlateQ - oracle-myopic").mean_diff, lo: e4("E4: SlateQ - oracle-myopic").ci95_low, hi: e4("E4: SlateQ - oracle-myopic").ci95_high, color: agentColor("oracle_myopic") },
      ], { labelW: 250, axis: "SlateQ advantage", aria: "E4" })}
      <h4>Why the two cascades differ</h4><ul><li>Random recommender's watch time: ${fmt(findAgent("rq3", "random", n0, k0, "matched").mean_total_reward)} (as assumed), ${fmt(pr ? pr.mean_total_reward : null)} (paper's cascade), ${fmt(findAgent("rq3", "random", n0, k0, "severe_cascade").mean_total_reward)} (RecSim's cascade). RecSim's cascade makes clicks rare; the paper's keeps them common, so quality can still extend sessions.</li></ul>
      <h4>What it does not show</h4><p class="not">Two cascades are two data points; this is our implementation of the paper's description, not a numerical replication. It does not show SlateQ is robust to any wrong viewer model.</p>`;
    },
  });

  card("follow", "e5", {
    kicker: "E5", explo: true, title: "Clicks vs watch time", blurb: "Does the click-chaser get more clicks but less watch time?",
    num: () => { const r = cwRow("oracle_myopic", 80, 3, "matched"), s = cwRow("slateq", 80, 3, "matched"); return `${fmt(r.clicks_per_session, 1)} vs ${fmt(s.clicks_per_session, 1)}`; },
    unit: "videos watched per session: perfect click-chaser vs SlateQ (N=80)", verdict: () => {
      const g = SITE.phase6b.clicks_watch_gaps.filter((r) => r.comparison === "oracle-myopic - SlateQ");
      return `<span class="pill no">same click rate in ${g.filter((r) => r.click_rate_verdict === "no clear difference").length} of ${g.length}</span>`;
    },
    detail: () => e5Detail(), after: () => e5Wire(),
  });
}
function agentTable(ags) {
  return `<div class="tbl-wrap"><table class="tbl"><tr><th>Recommender</th><th>Watch time</th><th>Videos watched</th><th>Session steps</th><th>Watched quality</th></tr>${ags.map((r) => `<tr><td><span style="color:${agentColor(r.agent)}">●</span> ${NAME[r.agent]}</td><td>${fmt(r.mean_total_reward)}</td><td>${fmt(r.mean_clicks, 1)}</td><td>${fmt(r.mean_length, 1)}</td><td>${fmt(r.mean_clicked_quality, 3)}</td></tr>`).join("")}</table></div>`;
}

/* ---- RQ2 explorer ---- */
const RQ2 = { n: 80, k: 3 };
function rq2Ns() { return [...new Set(gaps("rq2").map((r) => r.num_candidates))].sort((a, b) => a - b); }
function rq2Ks() { return [...new Set(gaps("rq2").map((r) => r.slate_size))].sort((a, b) => a - b); }
function rq2Detail() {
  return `<p class="eyebrow">RQ2 &middot; this project's own contribution</p><h2 id="modal-title">The more videos there are to choose from, the more planning pays</h2>
    <div class="chips" id="rq2-k"><span>videos shown (k)</span>${rq2Ks().map((k) => `<button class="chip" data-k="${k}" aria-pressed="${k === RQ2.k}">k = ${k}</button>`).join("")}</div>
    <div class="chips" id="rq2-n"><span>candidates (N)</span>${rq2Ns().map((n) => `<button class="chip" data-n="${n}" aria-pressed="${n === RQ2.n}">N = ${n}</button>`).join("")}</div>
    <div id="rq2-big"></div><div id="rq2-chart"></div>
    <h4>What it shows</h4><ul>
      <li>SlateQ is clearly ahead of the learned click-chaser in every setting with a real choice, and the gap grows steeply with N.</li>
      <li>At a fixed N, showing more videos at once (bigger k) makes the gap smaller.</li>
      <li>When every candidate is shown (k = N) there is nothing to choose, and the gap is not clearly different from zero, as it must be.</li>
      <li>Two things happen at large N: SlateQ improves against the perfect click-chaser, <i>and</i> the learned click-chaser falls behind the perfect one. The comparison against the perfect click-chaser (lighter bars) is the cleaner measure of planning.</li></ul>
    <h4>What it does not show</h4><p class="not">It does not show the trend beyond N = 80. "Catalog size" here means fresh candidates drawn every step (RecSim has no fixed catalogue). The training budget was set once at N = 10.</p>`;
}
function rq2Wire() {
  const upd = () => {
    const ns = rq2Ns().filter((n) => n > RQ2.k || (n === RQ2.k && gaps("rq2").some((r) => isCell(r, n, RQ2.k))));
    if (!gaps("rq2").some((r) => isCell(r, RQ2.n, RQ2.k))) RQ2.n = ns[ns.length - 1];
    $$("#rq2-k .chip").forEach((b) => b.setAttribute("aria-pressed", String(+b.dataset.k === RQ2.k)));
    $$("#rq2-n .chip").forEach((b) => { const ok = gaps("rq2").some((r) => isCell(r, +b.dataset.n, RQ2.k)); b.disabled = !ok; b.style.opacity = ok ? 1 : 0.35; b.setAttribute("aria-pressed", String(+b.dataset.n === RQ2.n)); });
    const p = findGap("rq2", PRIMARY, RQ2.n, RQ2.k), o = findGap("rq2", "SlateQ - oracle-myopic", RQ2.n, RQ2.k);
    $("#rq2-big").innerHTML = p ? `<div class="bignum"><span class="n" id="rq2-n-val">${sgn(p.mean_diff)}</span><span class="d">SlateQ ${MINUS} learned myopic at N=${RQ2.n}, k=${RQ2.k}${p.control ? " (control: every candidate shown)" : ""}<br>${ci(p)} &middot; ${pill(p.verdict, "SlateQ")}${o ? ` &middot; vs perfect click-chaser ${sgn(o.mean_diff)}` : ""}</span></div>` : "";
    const groups = ns.filter((n) => gaps("rq2").some((r) => isCell(r, n, RQ2.k))).map((n) => {
      const a = findGap("rq2", PRIMARY, n, RQ2.k), b = findGap("rq2", "SlateQ - oracle-myopic", n, RQ2.k);
      return { label: `N=${n}`, sub: a.control ? "control" : "", dim: false, bars: [
        { name: "vs learned", mean: a.mean_diff, lo: a.ci95_low, hi: a.ci95_high, color: n === RQ2.n ? agentColor("slateq") : "rgba(34,211,238,.55)" },
        { name: "vs oracle", mean: b.mean_diff, lo: b.ci95_low, hi: b.ci95_high, color: n === RQ2.n ? "#a78bfa" : "rgba(167,139,250,.5)" }] };
    });
    $("#rq2-chart").innerHTML = vbars(groups, { y: `SlateQ advantage (k=${RQ2.k}); cyan: vs learned, violet: vs perfect click-chaser`, aria: "RQ2 gaps by N", fmt: (v) => sgn(v, 1) });
  };
  $$("#rq2-k .chip").forEach((b) => b.addEventListener("click", () => { RQ2.k = +b.dataset.k; upd(); }));
  $$("#rq2-n .chip").forEach((b) => b.addEventListener("click", () => { RQ2.n = +b.dataset.n; upd(); }));
  upd();
}

/* ---- E5 explorer ---- */
const cwRow = (a, n, k, cond) => SITE.phase6b.clicks_watch.find((r) => r.agent === a && r.condition === cond && isCell(r, n, k));
const E5 = { key: "matched|80|3" };
function e5Conds() {
  const seen = new Map();
  for (const r of SITE.phase6b.clicks_watch_gaps) { const key = `${r.condition}|${r.num_candidates}|${r.slate_size}`; if (!seen.has(key)) seen.set(key, r); }
  return [...seen.entries()].map(([key, r]) => ({ key, label: r.condition === "matched" ? `N=${r.num_candidates}, k=${r.slate_size}${r.control ? " (control)" : ""}` : `${RUNG[r.condition] || r.condition}` }));
}
function e5Detail() {
  const g = SITE.phase6b.clicks_watch_gaps;
  const pats = {};
  for (const r of g) { pats[r.comparison] = pats[r.comparison] || {}; pats[r.comparison][r.pattern] = (pats[r.comparison][r.pattern] || 0) + 1; }
  return `<p class="eyebrow">E5 &middot; exploratory, no new runs</p><h2 id="modal-title">Same click rate, shorter sessions</h2>
    <label class="chips"><span>setting</span><select id="e5-sel" class="agent-sel" style="font-size:.9rem">${e5Conds().map((c) => `<option value="${c.key}" ${c.key === E5.key ? "selected" : ""}>${esc(c.label)}</option>`).join("")}</select></label>
    <div id="e5-chart"></div>
    <h4>Pattern across all settings</h4><div class="tbl-wrap"><table class="tbl"><tr><th>Comparison</th><th>Pattern</th><th>Settings</th></tr>${Object.entries(pats).flatMap(([c, ps]) => Object.entries(ps).map(([p, n]) => `<tr><td>${esc(c.replace(" - ", " vs "))}</td><td>${esc(p)}</td><td>${n}</td></tr>`)).join("")}</table></div>
    <h4>What it shows</h4><ul><li>The click-chasers and SlateQ get the <b>same click rate</b> per recommendation in almost every setting.</li>
    <li>The cost of chasing clicks shows up as <b>shorter sessions</b>: fewer videos watched and less watch time in total, not fewer clicks per recommendation.</li>
    <li>The motivating idea "more clicks, less watch time" appeared only rarely; it is reported as it came out.</li></ul>
    <h4>What it does not show</h4><p class="not">Nothing about real platforms. In this simulator every video has the same length, so watch time per click can hardly differ by design.</p>`;
}
function e5Wire() {
  const upd = () => {
    const [cond, n, k] = E5.key.split("|"); const N = +n, K = +k;
    const rows = AGENTS.map((a) => ({ a, r: cwRow(a, N, K, cond) })).filter((x) => x.r);
    const metric = (m, label, d) => ({ label, bars: rows.map(({ a, r }) => ({ name: NAME[a], mean: r[m], lo: r[`${m}_ci95_low`], hi: r[`${m}_ci95_high`], color: agentColor(a) })), d });
    const legend = rows.map(({ a }) => `<span style="color:${agentColor(a)}">●</span> ${NAME[a]}`).join(" &nbsp; ");
    $("#e5-chart").innerHTML = `<p class="muted" style="font-size:.82rem;margin:6px 0">${legend}</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px">
      ${[metric("click_rate", "Click rate", 3), metric("clicks_per_session", "Videos watched / session", 1), metric("watch_per_session", "Watch time / session", 1)].map((m) =>
        `<div><h4 style="margin:4px 0">${m.label}</h4>${vbars([{ label: "", bars: m.bars }], { w: 300, h: 230, fmt: (v) => fmt(v, m.d), aria: m.label })}</div>`).join("")}</div>`;
  };
  $("#e5-sel").addEventListener("change", (e) => { E5.key = e.target.value; upd(); });
  upd();
}

/* ---- render rows + modal ---- */
function renderFindings() {
  const g1 = findGap("rq2", PRIMARY, ...CELL);
  $("#findings-lede").innerHTML = `Every number here is an average over ${SITE.frozen.eval_episodes} test viewers per run and 5 run seeds, with a 95% confidence interval. A result is called <b>clear</b> only if the interval excludes zero <b>and</b> all 5 seeds agree (rule fixed before any run). Headline: SlateQ ${sgn(g1.mean_diff)} watch time per session at N=${CELL[0]}, k=${CELL[1]}.`;
  const ROWS = [["main", "The main questions", "pre-registered before any result"], ["follow", "Stress tests", "exploratory: planned after the main results, registered before their runs"]];
  $("#rows").innerHTML = ROWS.map(([id, title, sub]) => `<section class="row"><div class="row-h"><h2>${title}</h2><span>${sub}</span></div><div class="shelf">${CARDS.filter((c) => c.row === id).map((c, i) => {
    let num = "n/a", ver = "";
    try { num = c.num(); ver = c.verdict(); } catch (e) { console.warn(c.id, e); }
    return `<button class="tile" data-card="${c.id}"><div class="art">${artSVG(i + (id === "follow" ? 7 : 0))}<span class="kicker">${esc(c.kicker)}</span>${c.explo ? '<span class="kicker explo">exploratory</span>' : ""}<span class="num${String(num).length > 8 ? " long" : ""}">${num}</span><span class="unit">${esc(c.unit)}</span></div><div class="body"><h3>${esc(c.title)}</h3><p>${esc(c.blurb)}</p>${ver}</div></button>`;
  }).join("")}</div></section>`).join("");
  $$(".tile").forEach((t) => t.addEventListener("click", () => openCard(t.dataset.card)));
  $("#findings-fine").textContent = "Simulated viewers only (RecSim Interest Evolution). SlateQ is the project's own PyTorch port of RecSim's agent. Exploratory results make many comparisons without correction, so single verdicts should be read with care. Full details: docs/RESULTS.md in the repository.";
}
function openCard(id) {
  const c = CARDS.find((x) => x.id === id);
  if (!c) return;
  let html;
  try { html = c.detail(); } catch (e) { console.error(e); html = `<p>Could not render this card: ${esc(e.message)}</p>`; }
  $("#modal-body").innerHTML = html;
  const m = $("#modal");
  if (!m.open) m.showModal();
  if (c.after) c.after();
  m.querySelector(".modal-in").scrollTop = 0;
}
function initModal() {
  const m = $("#modal");
  $("#modal-x").addEventListener("click", () => m.close());
  m.addEventListener("click", (e) => { if (e.target === m) m.close(); });
}

/* ================================================================ about */
function renderAbout() {
  const f = SITE.frozen;
  $("#about-grid").innerHTML = `
    <div class="box"><h3>The pretend platform</h3><p>SlateStream is a front end for Google's RecSim "Interest Evolution" simulator. Each simulated viewer has hidden tastes for 20 topics and a limited time budget. Every step, the recommender sees ${CELL[0]} fresh candidate videos and puts ${CELL[1]} on screen (a "slate"). The viewer watches at most one.</p></div>
    <div class="box"><h3>Why planning can help</h3><p>Viewers click on topics they like. But each video also has a hidden <b>quality</b>: good videos give some time budget back, poor ones ("clickbait") use extra. A recommender that only chases the next click ignores quality. One that plans ahead can pick equally clickable but better videos, so the session lasts longer.</p></div>
    <div class="box"><h3>The four recommenders</h3>${AGENTS.map((a) => `<div class="agent-line" style="--c:${agentColor(a)}"><span class="dot"></span><p><b>${NAME[a]}:</b> ${ROLE[a]}.</p></div>`).join("")}</div>
    <div class="box"><h3>Fair rules</h3><ul><li>Each learned recommender trained for ${f.budget.toLocaleString("en-US")} steps; settings were tuned once and then frozen.</li><li>All are tested on the same ${f.eval_episodes.toLocaleString("en-US")} new viewers, repeated with 5 run seeds.</li><li>"Clear" means the 95% interval excludes zero and all 5 seeds agree. The rule was written down before any result.</li></ul></div>
    <div class="box"><h3>What the replays are</h3><p>The Watch, Race and Taste pages replay <b>recorded</b> test sessions: ${viewerCount()} viewers (5 per run seed), each served once by every recommender, at N = ${CELL[0]}, k = ${CELL[1]}. Nothing is simulated in your browser. For other settings only averages were saved, so those appear on the Findings page as charts.</p></div>
    <div class="box"><h3>Limits</h3><ul><li>Simulated viewers only; nothing here is a claim about any real platform.</li><li>SlateQ is the project's own PyTorch port, checked with unit tests and a calibration against the perfect click-chaser, not run side by side with Google's original.</li><li>The topic names and cover art are generated decoration: topics in the simulator are just numbers.</li></ul></div>`;
}

/* ================================================================ boot */
async function boot() {
  initNav(); initTransport(); initModal(); initTasteMode();
  try {
    SITE = await getJSON("data/site.json");
  } catch (e) {
    $("main").innerHTML = `<div class="wrap" style="padding:40px 16px"><h1>Could not load the data</h1><p class="lede">${esc(e.message)}. Serve the <code>web/</code> folder over HTTP (for example <code>python -m http.server -d web</code>) and open <code>/stream.html</code>.</p></div>`;
    return;
  }
  const g1 = findGap("rq2", PRIMARY, ...CELL);
  $("#watch-lede").innerHTML = `Pick a recorded viewer, choose two recommenders and press play. Each step shows the ${CELL[1]} videos put on screen, which one was watched, and how much of the viewer's time budget is left. Over all ${SITE.frozen.eval_episodes.toLocaleString("en-US")} test viewers, SlateQ adds <b>${sgn(g1.mean_diff)}</b> watch time per session over the learned click-chaser (${pct(g1.relative_to_b)}); single viewers vary.`;
  renderViewers();
  paneShell("L"); paneShell("R");
  defineCards(); renderFindings(); renderAbout();
  await selectViewer(SITE.case_study_seed || 0, 0);
  showView(location.hash.slice(1) || "watch");
}
boot();
