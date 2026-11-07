/* Renders web/data/site.json and traces_seed<k>.json (built by scripts/build_web.py from results/).
   No number on this page is typed by hand: everything shown comes from those files. */
"use strict";

const AGENTS = ["slateq", "learned_myopic", "oracle_myopic", "random"];
const LABEL = { slateq: "SlateQ", learned_myopic: "Learned myopic", oracle_myopic: "Oracle myopic", random: "Random" };
const SYMBOL = { slateq: "circle", learned_myopic: "square", oracle_myopic: "diamond", random: "triangle-up" };
const PRIMARY = "SlateQ - learned-myopic";
const RUNGS = ["matched", "mild_noclick3", "moderate_logit", "severe_cascade"];
const RUNG_LABEL = { matched: "matched", mild_noclick3: "mild: more skipping", moderate_logit: "moderate: logit", severe_cascade: "severe: cascade" };
const PRIMARY_CELL = [10, 3];

let SITE = null;
const traceCache = {};
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const color = (a) => css(`--series-${a}`);
const fmt = (x, d = 2) => (x === null || x === undefined || Number.isNaN(x) ? "n/a" : Number(x).toFixed(d));
const sgn = (x, d = 2) => (x === null || x === undefined ? "n/a" : (x >= 0 ? "+" : "") + Number(x).toFixed(d));
const el = (id) => document.getElementById(id);
const seedCols = (row, prefix) =>
  Object.keys(row).filter((k) => k.startsWith(prefix) && /\d+$/.test(k) && row[k] !== null)
    .map((k) => ({ seed: Number(k.slice(prefix.length)), v: row[k] }));
const isCell = (r, n, k) => r.num_candidates === n && r.slate_size === k;

function layout(extra = {}) {
  return Object.assign({
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: css("--font"), color: css("--text-secondary"), size: 12 },
    margin: { l: 56, r: 16, t: 10, b: 48 }, showlegend: false,
    xaxis: { gridcolor: css("--border"), zerolinecolor: css("--text-muted"), automargin: true },
    yaxis: { gridcolor: css("--border"), zerolinecolor: css("--text-muted"), automargin: true },
    hoverlabel: { bgcolor: css("--surface-1"), bordercolor: css("--border"), font: { color: css("--text-primary") } },
  }, extra);
}
const CONFIG = { displayModeBar: false, responsive: true };
const plot = (id, data, lay) => Plotly.react(el(id), data, layout(lay), CONFIG);

/* ------------------------------------------------------------------ tabs */
function initTabs() {
  const buttons = document.querySelectorAll(".tabs button");
  const show = (name) => {
    buttons.forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === name)));
    document.querySelectorAll(".panel").forEach((p) => (p.hidden = p.id !== name));
    try { localStorage.setItem("tab", name); } catch (e) { /* storage unavailable */ }
    window.dispatchEvent(new Event("resize"));
    if (name === "replay") renderReplay();
  };
  buttons.forEach((b) => b.addEventListener("click", () => show(b.dataset.tab)));
  let start = "overview";
  try { start = localStorage.getItem("tab") || start; } catch (e) { /* ignore */ }
  if (!el(start)) start = "overview";
  show(start);
}

/* ------------------------------------------------------------------ overview */
function primaryGap(gaps, cond = "matched", cell = PRIMARY_CELL) {
  return gaps.find((g) => g.condition === cond && g.comparison === PRIMARY && isCell(g, ...cell));
}
function verdictText(v) {
  return { "A higher": "SlateQ higher", "A lower": "SlateQ lower", "no clear difference": "no clear difference",
    "insufficient seeds": "too few seeds yet", missing: "not run yet" }[v] || v || "not run yet";
}
function renderOverview() {
  const g = primaryGap(SITE.rq2.gaps);
  const kpis = [];
  if (g) kpis.push({ label: "RQ1: SlateQ - learned myopic (N=10, k=3)", value: sgn(g.mean_diff),
    detail: `watch time per session · 95% CI [${sgn(g.ci95_low)}, ${sgn(g.ci95_high)}] · ${g.n_seeds} seeds · ${verdictText(g.verdict)}` });
  const og = SITE.rq2.gaps.find((r) => r.condition === "matched" && r.comparison === "SlateQ - oracle-myopic" && isCell(r, ...PRIMARY_CELL));
  if (og) kpis.push({ label: "SlateQ - oracle myopic (privileged)", value: sgn(og.mean_diff),
    detail: `95% CI [${sgn(og.ci95_low)}, ${sgn(og.ci95_high)}] · ${verdictText(og.verdict)}` });
  const grid = SITE.rq2.gaps.filter((r) => r.condition === "matched" && r.comparison === PRIMARY && !r.control && r.mean_diff !== null);
  if (grid.length) {
    const higher = grid.filter((r) => r.verdict === "A higher").length;
    kpis.push({ label: "RQ2: cells where SlateQ is clearly higher", value: `${higher} / ${grid.length}`,
      detail: "clear = 95% CI above 0 and every seed agrees (pre-registered rule)" });
  }
  const r3 = SITE.rq3.gaps.filter((r) => r.comparison === PRIMARY && r.condition !== "matched" && r.mean_diff !== null);
  if (r3.length) {
    const sev = r3.find((r) => r.condition === "severe_cascade");
    if (sev) kpis.push({ label: "RQ3: gap under the most wrong user model", value: sgn(sev.mean_diff),
      detail: `cascade users · 95% CI [${sgn(sev.ci95_low)}, ${sgn(sev.ci95_high)}] · ${verdictText(sev.verdict)}` });
  }
  el("kpis").innerHTML = kpis.map((k) =>
    `<div class="kpi"><div class="label">${k.label}</div><div class="value">${k.value}</div><div class="detail">${k.detail}</div></div>`).join("") ||
    `<p class="note">Results are not available yet.</p>`;
  const runs = SITE.runs.rq2 || {};
  el("overview-note").textContent = `Runs completed: ${runs.ok || 0} of ${Object.values(runs).reduce((a, b) => a + b, 0)} (RQ1/RQ2 sweep). Pages update when the analysis is re-run.`;
}

/* ------------------------------------------------------------------ RQ1 */
function renderRQ1() {
  const rows = SITE.rq2.agents.filter((r) => r.condition === "matched" && isCell(r, ...PRIMARY_CELL));
  const ag = AGENTS.map((a) => rows.find((r) => r.agent === a)).filter(Boolean);
  const nSeeds = Math.max(0, ...ag.map((r) => r.n_seeds));
  el("rq1-sub").textContent = `Catalog N=10 candidates, slate k=3. ${nSeeds} run seeds × ${SITE.frozen.eval_episodes} evaluation sessions each; learned agents trained for ${SITE.frozen.budget.toLocaleString()} steps.`;
  const data = [];
  ag.forEach((r, i) => {
    const seeds = seedCols(r, "mean_total_reward_seed");
    data.push({ type: "scatter", mode: "markers", x: seeds.map((_, j) => i + (j - (seeds.length - 1) / 2) * 0.06), y: seeds.map((s) => s.v),
      marker: { color: color(r.agent), size: 7, opacity: 0.5 }, hovertemplate: seeds.map((s) => `seed ${s.seed}: %{y:.2f}<extra></extra>`) });
    data.push({ type: "scatter", mode: "markers+text", x: [i], y: [r.mean_total_reward], text: [fmt(r.mean_total_reward, 1)], textposition: "middle right",
      marker: { color: color(r.agent), size: 13, symbol: SYMBOL[r.agent], line: { color: css("--surface-1"), width: 2 } },
      error_y: { type: "data", symmetric: false, array: [r.mean_total_reward_ci95_high - r.mean_total_reward], arrayminus: [r.mean_total_reward - r.mean_total_reward_ci95_low], color: color(r.agent), thickness: 2, width: 6 },
      hovertemplate: `${LABEL[r.agent]}<br>mean %{y:.2f}<br>95% CI [${fmt(r.mean_total_reward_ci95_low)}, ${fmt(r.mean_total_reward_ci95_high)}]<extra></extra>`, textfont: { color: css("--text-primary") } });
  });
  plot("rq1-agents", data, { xaxis: { range: [-0.5, ag.length - 0.2], tickvals: ag.map((_, i) => i), ticktext: ag.map((r) => LABEL[r.agent]), gridcolor: "rgba(0,0,0,0)" }, yaxis: { title: "mean total reward (watch time)", gridcolor: css("--border") } });

  const gaps = SITE.rq2.gaps.filter((r) => r.condition === "matched" && isCell(r, ...PRIMARY_CELL) && r.mean_diff !== null)
    .sort((a, b) => (b.primary - a.primary) || a.comparison.localeCompare(b.comparison));
  const gd = [];
  gaps.forEach((r, i) => {
    const y = gaps.length - 1 - i;
    const seeds = seedCols(r, "diff_seed");
    gd.push({ type: "scatter", mode: "markers", x: seeds.map((s) => s.v), y: seeds.map((_, j) => y + (j - (seeds.length - 1) / 2) * 0.06),
      marker: { color: css("--text-muted"), size: 6, opacity: 0.6 }, hovertemplate: seeds.map((s) => `seed ${s.seed}: %{x:.2f}<extra></extra>`) });
    gd.push({ type: "scatter", mode: "markers", x: [r.mean_diff], y: [y], marker: { color: r.primary ? css("--accent") : css("--text-secondary"), size: 11 },
      error_x: { type: "data", symmetric: false, array: [r.ci95_high - r.mean_diff], arrayminus: [r.mean_diff - r.ci95_low], color: r.primary ? css("--accent") : css("--text-secondary"), thickness: 2, width: 6 },
      hovertemplate: `${r.comparison}<br>mean %{x:.2f}<br>95% CI [${sgn(r.ci95_low)}, ${sgn(r.ci95_high)}]<br>${verdictText(r.verdict).replace("SlateQ", r.agent_a === "slateq" ? "SlateQ" : LABEL[r.agent_a])}<extra></extra>` });
  });
  plot("rq1-gaps", gd, { margin: { l: 210, r: 16, t: 10, b: 48 }, yaxis: { tickvals: gaps.map((_, i) => gaps.length - 1 - i), ticktext: gaps.map((r) => (r.primary ? "<b>PRIMARY</b> " : "") + r.comparison), gridcolor: "rgba(0,0,0,0)" },
    xaxis: { title: "difference in mean total reward (A - B)", zeroline: true, zerolinewidth: 2, zerolinecolor: css("--text-muted"), gridcolor: css("--border") } });

  // learning curves
  const cv = SITE.rq2.curves.filter((r) => r.condition === "matched" && isCell(r, ...PRIMARY_CELL));
  const cd = [];
  ["slateq", "learned_myopic"].forEach((a) => {
    const bySeed = {};
    cv.filter((r) => r.agent === a).forEach((r) => (bySeed[r.seed] = bySeed[r.seed] || []).push(r));
    const seeds = Object.values(bySeed).map((rs) => rs.sort((x, y) => x.train_steps - y.train_steps));
    if (!seeds.length) return;
    const n = Math.min(...seeds.map((s) => s.length));
    const x = [...Array(n).keys()].map((i) => seeds.reduce((t, s) => t + s[i].train_steps, 0) / seeds.length / 1000);
    const m = x.map((_, i) => seeds.reduce((t, s) => t + s[i].mean_total_reward, 0) / seeds.length);
    const sd = x.map((_, i) => seeds.length > 1 ? Math.sqrt(seeds.reduce((t, s) => t + (s[i].mean_total_reward - m[i]) ** 2, 0) / (seeds.length - 1)) : 0);
    cd.push({ x: [...x, ...x.slice().reverse()], y: [...m.map((v, i) => v + sd[i]), ...m.map((v, i) => v - sd[i]).reverse()], fill: "toself", fillcolor: color(a), opacity: 0.15, line: { width: 0 }, hoverinfo: "skip", type: "scatter" });
    cd.push({ x, y: m, type: "scatter", mode: "lines+markers", name: LABEL[a], line: { color: color(a), width: 2 }, marker: { symbol: SYMBOL[a], size: 7 }, hovertemplate: `${LABEL[a]}<br>%{x:.0f}K steps: %{y:.2f}<extra></extra>` });
  });
  plot("rq1-curves", cd, { showlegend: true, legend: { orientation: "h", y: -0.25 }, xaxis: { title: "training steps (thousands)", gridcolor: css("--border") }, yaxis: { title: "mean total reward", gridcolor: css("--border") }, margin: { l: 56, r: 16, t: 10, b: 70 } });

  // session lengths
  const sl = SITE.rq2.session_lengths.filter((r) => r.condition === "matched");
  const ld = AGENTS.map((a) => {
    const counts = {};
    sl.filter((r) => r.agent === a).forEach((r) => (counts[r.length] = (counts[r.length] || 0) + r.episodes));
    const xs = Object.keys(counts).map(Number).sort((p, q) => p - q);
    const tot = xs.reduce((t, x) => t + counts[x], 0);
    let c = 0;
    return { x: xs, y: xs.map((x) => (c += counts[x]) / tot), type: "scatter", mode: "lines", line: { shape: "hv", color: color(a), width: 2 }, name: LABEL[a], hovertemplate: `${LABEL[a]}<br>%{y:.0%} of sessions end by step %{x}<extra></extra>` };
  }).filter((t) => t.x.length);
  plot("rq1-lengths", ld, { showlegend: true, legend: { orientation: "h", y: -0.25 }, xaxis: { title: "session length (steps)", gridcolor: css("--border") }, yaxis: { title: "fraction of sessions", tickformat: ".0%", gridcolor: css("--border") }, margin: { l: 56, r: 16, t: 10, b: 70 } });

  const cols = [["mean_total_reward", "Total reward", 2], ["mean_length", "Session length", 1], ["mean_clicks", "Clicks", 1], ["mean_clicked_quality", "Clicked quality", 3], ["mean_reward_per_step", "Reward / step", 3]];
  el("rq1-table").innerHTML = `<table><thead><tr><th>Policy</th>${cols.map((c) => `<th>${c[1]}</th>`).join("")}<th>Seeds</th></tr></thead><tbody>${
    ag.map((r) => `<tr><td>${LABEL[r.agent]}</td>${cols.map((c) => `<td>${fmt(r[c[0]], c[2])} <span class="note">± ${fmt(r[c[0] + "_std"], c[2])}</span></td>`).join("")}<td>${r.n_seeds}</td></tr>`).join("")}</tbody></table><p class="cap">Mean over run seeds ± SD over seeds. Clicked quality is hidden from every agent.</p>`;
}

/* ------------------------------------------------------------------ RQ2 */
function renderRQ2() {
  const sel = el("rq2-cmp");
  if (!sel.options.length) {
    const cmps = [...new Set(SITE.rq2.gaps.map((g) => g.comparison))].sort((a, b) => (b === PRIMARY) - (a === PRIMARY));
    sel.innerHTML = cmps.map((c) => `<option value="${c}">${c === PRIMARY ? "PRIMARY: " : ""}${c}</option>`).join("");
    sel.addEventListener("change", renderRQ2);
  }
  const cmp = sel.value;
  const rows = SITE.rq2.gaps.filter((g) => g.condition === "matched" && g.comparison === cmp && !g.control);
  const ns = [...new Set(rows.map((r) => r.num_candidates))].sort((a, b) => a - b);
  const ks = [...new Set(rows.map((r) => r.slate_size))].sort((a, b) => a - b);
  const z = ks.map((k) => ns.map((n) => { const r = rows.find((q) => isCell(q, n, k)); return r && r.mean_diff !== null ? r.mean_diff : null; }));
  const txt = ks.map((k) => ns.map((n) => { const r = rows.find((q) => isCell(q, n, k)); return r && r.mean_diff !== null ? sgn(r.mean_diff) : (k >= n ? "—" : "missing"); }));
  const hov = ks.map((k) => ns.map((n) => { const r = rows.find((q) => isCell(q, n, k)); return r && r.mean_diff !== null ? `N=${n}, k=${k}<br>${sgn(r.mean_diff)} [${sgn(r.ci95_low)}, ${sgn(r.ci95_high)}]<br>${r.n_seeds} seeds · ${verdictText(r.verdict)}` : `N=${n}, k=${k}: no data`; }));
  const lim = Math.max(1e-9, ...z.flat().filter((v) => v !== null).map(Math.abs));
  plot("rq2-heat", [{ type: "heatmap", x: ns.map(String), y: ks.map(String), z, text: txt, texttemplate: "%{text}", customdata: hov, hovertemplate: "%{customdata}<extra></extra>",
    zmin: -lim, zmax: lim, colorscale: [[0, css("--neg")], [0.5, css("--mid")], [1, css("--pos")]], xgap: 2, ygap: 2, colorbar: { title: { text: "gap" }, thickness: 12 } }],
    { xaxis: { title: "catalog size N (candidates per step)", type: "category" }, yaxis: { title: "slate size k", type: "category" } });
  const ramp = ["#86b6ef", "#2a78d6", "#104281"];
  const ld = ks.map((k, i) => {
    const rs = rows.filter((r) => r.slate_size === k && r.mean_diff !== null).sort((a, b) => a.num_candidates - b.num_candidates);
    return { type: "scatter", mode: "lines+markers", name: `k=${k}`, x: rs.map((r) => r.num_candidates), y: rs.map((r) => r.mean_diff), line: { color: ramp[i % 3], width: 2 }, marker: { size: 8 },
      error_y: { type: "data", symmetric: false, array: rs.map((r) => r.ci95_high - r.mean_diff), arrayminus: rs.map((r) => r.mean_diff - r.ci95_low), thickness: 1.5, width: 4 },
      hovertemplate: rs.map((r) => `k=${k}, N=${r.num_candidates}<br>${sgn(r.mean_diff)} [${sgn(r.ci95_low)}, ${sgn(r.ci95_high)}]<extra></extra>`) };
  });
  plot("rq2-lines", ld, { showlegend: true, legend: { orientation: "h", y: -0.22 }, xaxis: { title: "catalog size N (log scale)", type: "log", tickvals: ns, ticktext: ns.map(String), gridcolor: css("--border") },
    yaxis: { title: `gap: ${cmp}`, zeroline: true, zerolinewidth: 2, gridcolor: css("--border") }, margin: { l: 64, r: 16, t: 10, b: 70 } });
}

/* ------------------------------------------------------------------ RQ3 */
function renderRQ3() {
  const gaps = SITE.rq3.gaps.filter((g) => g.comparison === PRIMARY && g.mean_diff !== null);
  const rungs = RUNGS.filter((r) => gaps.some((g) => g.condition === r));
  if (!rungs.length) { el("rq3-note").textContent = "RQ3 runs are not available yet."; return; }
  const d = [];
  rungs.forEach((rung, i) => {
    const r = gaps.find((g) => g.condition === rung);
    const seeds = seedCols(r, "diff_seed");
    d.push({ type: "scatter", mode: "markers", x: seeds.map((_, j) => i + (j - (seeds.length - 1) / 2) * 0.05), y: seeds.map((s) => s.v), marker: { color: css("--text-muted"), size: 6, opacity: 0.6 }, hovertemplate: seeds.map((s) => `seed ${s.seed}: %{y:.2f}<extra></extra>`) });
    d.push({ type: "scatter", mode: "markers+text", x: [i], y: [r.mean_diff], text: [sgn(r.mean_diff)], textposition: "middle right", marker: { color: css("--accent"), size: 12 },
      error_y: { type: "data", symmetric: false, array: [r.ci95_high - r.mean_diff], arrayminus: [r.mean_diff - r.ci95_low], color: css("--accent"), thickness: 2, width: 6 },
      hovertemplate: `${RUNG_LABEL[rung]}<br>${sgn(r.mean_diff)} [${sgn(r.ci95_low)}, ${sgn(r.ci95_high)}]<br>${verdictText(r.verdict)}<extra></extra>`, textfont: { color: css("--text-primary") } });
  });
  plot("rq3-gap", d, { xaxis: { tickvals: rungs.map((_, i) => i), ticktext: rungs.map((r) => RUNG_LABEL[r]), gridcolor: "rgba(0,0,0,0)" }, yaxis: { title: "SlateQ - learned myopic", zeroline: true, zerolinewidth: 2, gridcolor: css("--border") } });
  const ad = AGENTS.map((a, j) => {
    const rs = rungs.map((rung) => SITE.rq3.agents.find((r) => r.condition === rung && r.agent === a)).filter(Boolean);
    return { type: "scatter", mode: "markers", name: LABEL[a], x: rs.map((r) => rungs.indexOf(r.condition) + (j - 1.5) * 0.12), y: rs.map((r) => r.mean_total_reward),
      marker: { color: color(a), size: 10, symbol: SYMBOL[a] }, error_y: { type: "data", symmetric: false, array: rs.map((r) => r.mean_total_reward_ci95_high - r.mean_total_reward), arrayminus: rs.map((r) => r.mean_total_reward - r.mean_total_reward_ci95_low), color: color(a), thickness: 1.5, width: 4 },
      hovertemplate: rs.map((r) => `${LABEL[a]} · ${RUNG_LABEL[r.condition]}<br>%{y:.2f}<extra></extra>`) };
  });
  plot("rq3-abs", ad, { showlegend: true, legend: { orientation: "h", y: -0.22 }, xaxis: { tickvals: rungs.map((_, i) => i), ticktext: rungs.map((r) => RUNG_LABEL[r]), gridcolor: "rgba(0,0,0,0)" }, yaxis: { title: "mean total reward", gridcolor: css("--border") }, margin: { l: 56, r: 16, t: 10, b: 70 } });
  el("rq3-note").textContent = "The 'matched' condition reuses the RQ1 runs. Reward scales differ between conditions because users click at different rates.";
}

/* ------------------------------------------------------------------ replay */
let playing = null;
async function loadTraces(seed) {
  if (!traceCache[seed]) traceCache[seed] = await (await fetch(`data/traces_seed${seed}.json`)).json();
  return traceCache[seed];
}
function qualityColor(q) {
  const t = Math.max(-1, Math.min(1, q / 3));
  const mix = (a, b, f) => a.map((x, i) => Math.round(x + (b[i] - x) * f));
  const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const rgb = t < 0 ? mix(hex("#f0efec"), hex("#e34948"), -t) : mix(hex("#f0efec"), hex("#2a78d6"), t);
  return `rgb(${rgb.join(",")})`;
}
function interestColor(u) {
  const t = Math.max(-1, Math.min(1, u));
  const a = Math.abs(t);
  return t >= 0 ? `rgba(42,120,214,${0.15 + 0.85 * a})` : `rgba(227,73,72,${0.15 + 0.85 * a})`;
}
async function renderReplay() {
  if (!SITE || !SITE.trace_seeds.length) { el("rp-cols").innerHTML = `<p class="note">No traces available yet.</p>`; return; }
  const seedSel = el("rp-seed"), epSel = el("rp-ep"), step = el("rp-step");
  if (!seedSel.options.length) {
    seedSel.innerHTML = SITE.trace_seeds.map((s) => `<option value="${s}">${s}${s === SITE.case_study_seed ? " (case study)" : ""}</option>`).join("");
    if (SITE.trace_seeds.includes(SITE.case_study_seed)) seedSel.value = String(SITE.case_study_seed);
    seedSel.addEventListener("change", () => { epSel.innerHTML = ""; step.value = 0; renderReplay(); });
    epSel.addEventListener("change", () => { step.value = 0; renderReplay(); });
    step.addEventListener("input", () => drawStep());
    el("rp-play").addEventListener("click", togglePlay);
  }
  const tr = await loadTraces(seedSel.value);
  if (!epSel.options.length) {
    const eps = (tr[AGENTS.find((a) => tr[a])] || []).map((e) => e.episode);
    epSel.innerHTML = eps.map((e) => `<option value="${e}">user ${e}</option>`).join("");
  }
  const ep = Number(epSel.value || 0);
  const series = AGENTS.filter((a) => tr[a]).map((a) => ({ a, e: tr[a].find((x) => x.episode === ep) })).filter((s) => s.e);
  const maxLen = Math.max(...series.map((s) => s.e.budget.length));
  step.max = String(maxLen - 1);
  window.__replay = series;
  plot("rp-budget", series.map((s) => ({ type: "scatter", mode: "lines", name: LABEL[s.a], x: s.e.budget.map((_, i) => i), y: s.e.budget, line: { color: color(s.a), width: 2 },
    hovertemplate: `${LABEL[s.a]}<br>step %{x}: %{y:.1f} left<extra></extra>` })),
    { showlegend: true, legend: { orientation: "h", x: 0, y: 1.12 }, margin: { l: 56, r: 16, t: 28, b: 44 }, xaxis: { title: "step", gridcolor: css("--border") }, yaxis: { title: "time budget left", gridcolor: css("--border") }, shapes: [] });
  drawStep();
}
function drawStep() {
  const series = window.__replay || [];
  const t = Number(el("rp-step").value);
  el("rp-step-out").textContent = String(t);
  Plotly.relayout(el("rp-budget"), { shapes: [{ type: "line", x0: t, x1: t, yref: "paper", y0: 0, y1: 1, line: { color: css("--text-muted"), width: 1, dash: "dot" } }] });
  el("rp-cols").innerHTML = series.map(({ a, e }) => {
    const n = e.budget.length;
    const i = Math.min(t, n - 1);
    const cum = e.reward.slice(0, i + 1).reduce((x, y) => x + y, 0);
    const ended = t >= n;
    const slate = e.clusters[i].map((c, j) => `<div class="doc ${e.clicked[i] === j ? "clicked" : ""}" style="background:${qualityColor(e.quality[i][j])}" title="topic ${c}, quality ${fmt(e.quality[i][j])}">topic ${c}<small>q ${fmt(e.quality[i][j], 1)}</small></div>`).join("");
    const interest = e.interests[i].map((u, k) => `<span style="background:${interestColor(u)}" title="topic ${k}: ${fmt(u)}"></span>`).join("");
    return `<div class="agent-col" style="--c:${color(a)}"><h3><span>${LABEL[a]}</span><span class="stat">${n} steps</span></h3>
      <div class="stat">reward so far <b>${fmt(cum, 1)}</b> · budget ${fmt(e.budget[i], 1)}</div>
      ${ended ? `<div class="ended">Session ended at step ${n - 1}. Final reward ${fmt(e.reward.reduce((x, y) => x + y, 0), 1)}.</div>` : `<div class="slate">${slate}</div>
      <div class="stat">${e.clicked[i] >= 0 ? `clicked topic ${e.clusters[i][e.clicked[i]]} (+${fmt(e.reward[i], 2)})` : "no click"}</div>`}
      <div class="stat" style="margin-top:8px">user interests (20 topics)</div><div class="interest">${interest}</div></div>`;
  }).join("");
}
function togglePlay() {
  const btn = el("rp-play"), step = el("rp-step");
  if (playing) { clearInterval(playing); playing = null; btn.innerHTML = "&#9654; Play"; return; }
  btn.innerHTML = "&#10073;&#10073; Pause";
  playing = setInterval(() => {
    if (Number(step.value) >= Number(step.max)) { togglePlay(); return; }
    step.value = Number(step.value) + 1;
    drawStep();
  }, 180);
}

/* ------------------------------------------------------------------ method */
function renderMethod() {
  const f = SITE.frozen;
  const sel = (a) => f.selected[a] ? `learning rate ${f.selected[a].learning_rate}, target-network period ${f.selected[a].target_update_period}` : "n/a";
  el("method-protocol").innerHTML = [
    `Training budget ${f.budget.toLocaleString()} environment steps for every learned agent (rule fixed in advance).`,
    `Hyperparameters tuned on separate tuning users with an identical grid for both learned agents: SlateQ ${sel("slateq")}; learned myopic ${sel("learned_myopic")}.`,
    `${f.eval_episodes} evaluation sessions per run on users never used for training or tuning; every policy meets the same users.`,
    "Confidence intervals bootstrap over run seeds (10,000 resamples); a difference is called clear only if the CI excludes 0 and every seed agrees.",
  ].map((s) => `<li>${s}</li>`).join("");
  el("method-sha").textContent = SITE.git_sha ? `Results built from commit ${SITE.git_sha.slice(0, 7)}.` : "";
}

/* ------------------------------------------------------------------ boot */
async function main() {
  try {
    SITE = await (await fetch("data/site.json")).json();
  } catch (e) {
    el("kpis").innerHTML = `<p class="note">Could not load data/site.json. Run <code>python scripts/build_web.py</code> and serve this folder over HTTP.</p>`;
    return;
  }
  el("pilot-banner").hidden = !SITE.pilot;
  renderOverview();
  renderRQ1();
  renderRQ2();
  renderRQ3();
  renderMethod();
  initTabs();
}
window.addEventListener("DOMContentLoaded", main);
