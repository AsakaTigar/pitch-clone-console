# -*- coding: utf-8 -*-
"""Listening console for the bounded F0-budget voice-cloning task.

Five channels per pair: the source utterance, the target speaker's pitch-range
reference, and the three rendered variants of the bounded edit (identity,
endpoint, arm). All audio was rendered by the frozen P26 pass; this app only
re-plays it.
"""
import base64
import json
import os

import streamlit as st
import streamlit.components.v1 as components

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")

ROLES = ["ref_src", "ref_tgt", "identity", "endpoint", "arm"]
ROLE_LABEL = {
    "ref_src": "源句子",
    "ref_tgt": "目标音域参考",
    "identity": "identity（零编辑）",
    "endpoint": "endpoint（满预算）",
    "arm": "arm（选择器输出）",
}
ROLE_SUB = {
    "ref_src": "源说话人 A 的原句",
    "ref_tgt": "目标说话人 B 的音域",
    "identity": "零编辑对照（同一渲染链）",
    "endpoint": "满预算投影（α=1）",
    "arm": "冻结选择器的输出候选",
}
COLORS = {
    "ref_src": "#8a93a6",
    "ref_tgt": "#d29922",
    "identity": "#5b7fa6",
    "endpoint": "#9aa7b8",
    "arm": "#2f81f7",
}

st.set_page_config(page_title="音域适配克隆 · 试听调音台", page_icon="🎛️", layout="wide",
                   initial_sidebar_state="collapsed")


@st.cache_data(show_spinner=False)
def load_index():
    with open(os.path.join(DATA, "pairs_index.json"), encoding="utf-8") as fh:
        return json.load(fh)["pairs"]


@st.cache_data(show_spinner=False)
def load_analysis():
    with open(os.path.join(DATA, "clip_analysis.json"), encoding="utf-8") as fh:
        return {p["id"]: p for p in json.load(fh)["pairs"]}


@st.cache_data(show_spinner=False)
def load_audio_b64(pair_id, role):
    path = os.path.join(DATA, "clips", pair_id, role + ".wav")
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def fmt_hz(v):
    return "—" if v is None else f"{v:.1f} Hz"


def build_mixer_html(pair, analysis):
    clips = []
    for role in ROLES:
        c = analysis["clips"].get(role)
        if not c:
            continue
        clips.append({
            "role": role,
            "label": ROLE_LABEL[role],
            "sub": ROLE_SUB[role],
            "color": COLORS[role],
            "b64": load_audio_b64(pair["id"], role),
            "dur": c["dur_s"],
            "contour": c["f0_contour"],
            "hop_ms": c["hop_ms"],
        })
    payload = {
        "pair": pair,
        "clips": clips,
        "armEqualsEndpoint": bool(pair.get("arm_equals_endpoint")),
    }
    js = json.dumps(payload, ensure_ascii=False)
    html = MIXER_TEMPLATE.replace("__PAYLOAD__", js)
    return html


MIXER_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<style>
  :root {
    --bg:#ffffff; --panel:#0d1117; --panel2:#161b22; --line:#2c333d; --txt:#e6edf3;
    --dim:#8b949e; --mono:'SF Mono',Menlo,Consolas,monospace;
  }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:#1f2328;
         font:14px/1.45 -apple-system,'PingFang SC','Noto Sans SC',sans-serif; }
  .wrap { max-width:1000px; margin:0 auto; padding:4px 0 0; }
  .console { background:var(--panel); border-radius:12px; padding:12px 14px 14px; }
  .head { display:flex; align-items:baseline; gap:10px; flex-wrap:wrap; margin-bottom:12px;
          color:var(--txt); }
  .head h2 { font-size:15px; font-weight:650; }
  .head .meta { color:var(--dim); font-size:12px; font-family:var(--mono); }
  .chip { border:1px solid var(--line); border-radius:999px; padding:1px 9px;
          font-size:11.5px; color:var(--dim); font-family:var(--mono); }
  .chip.hot { color:#2f81f7; border-color:#2f81f7; }
  .grid { display:grid; grid-template-columns:repeat(5,1fr); gap:10px; }
  .strip { background:var(--panel2); border:1px solid var(--line); border-radius:10px;
           padding:10px 9px 9px; display:flex; flex-direction:column; gap:8px; color:var(--txt); }
  .strip .top { display:flex; align-items:center; gap:6px; min-height:20px; }
  .dot { width:9px; height:9px; border-radius:50%; flex:0 0 auto; }
  .strip .name { font-size:12.5px; font-weight:600; line-height:1.25; }
  .strip .sub { color:var(--dim); font-size:10px; line-height:1.35; min-height:27px;
                font-family:var(--mono); }
  .row { display:flex; align-items:center; gap:7px; }
  .row label { color:var(--dim); font-size:10px; width:34px; }
  input[type=range] { -webkit-appearance:none; width:100%; height:14px; background:transparent;
                      cursor:pointer; }
  input[type=range]::-webkit-slider-runnable-track { height:3px; border-radius:2px;
      background:linear-gradient(#30363d,#30363d); }
  input[type=range]::-webkit-slider-thumb { -webkit-appearance:none; width:13px; height:13px;
      border-radius:50%; background:#e6edf3; margin-top:-5px; border:none; }
  .btns { display:flex; gap:5px; }
  button { background:#21262d; color:var(--txt); border:1px solid var(--line); border-radius:6px;
           padding:3px 0; font-size:11px; flex:1; cursor:pointer; font-family:var(--mono); }
  button:hover { border-color:#3b4450; }
  button.m.on { background:#8b2c2c; border-color:#b34747; color:#fff; }
  button.s.on { background:#1f6f43; border-color:#2ea043; color:#fff; }
  button.eye { flex:0 0 26px; padding:3px 0; }
  button.eye.off { color:#4a5462; }
  .meter { position:relative; height:9px; background:#0b0f14; border-radius:5px;
           overflow:hidden; border:1px solid var(--line); }
  .meter .fill { position:absolute; inset:0 100% 0 0; background:var(--c,#2f81f7); opacity:.55;
                 transition:none; }
  .time { position:absolute; inset:0; text-align:center; font-size:8.5px; color:#c9d1d9;
          font-family:var(--mono); line-height:9px; }
  .transport { display:flex; align-items:center; gap:12px; margin:14px 0 10px;
               color:var(--txt); }
  .transport .play { width:64px; flex:0 0 64px; padding:6px 0; font-size:12px;
                     background:#21262d; color:var(--txt); }
  .transport .seek { flex:1; }
  .master { display:flex; align-items:center; gap:6px; flex:0 0 auto; }
  .master label { color:var(--dim); font-size:10.5px; white-space:nowrap; }
  .master input[type=range] { width:76px; }
  .master .val { font-family:var(--mono); font-size:10.5px; color:var(--txt);
                 min-width:32px; text-align:right; }
  .transport .clock { font-family:var(--mono); font-size:11.5px; color:var(--dim);
                      min-width:74px; text-align:right; }
  .toggles { display:flex; gap:14px; align-items:center; margin-left:6px; }
  .toggles label { color:var(--dim); font-size:11px; display:flex; gap:5px; align-items:center;
                   cursor:pointer; }
  canvas { width:100%; height:240px; display:block; background:#0b0f14;
           border:1px solid var(--line); border-radius:10px; }
  .legend { display:flex; gap:16px; margin:8px 2px 0; flex-wrap:wrap; }
  .legend span { font-size:11px; color:var(--dim); display:flex; align-items:center; gap:5px; }
  .legend i { width:14px; height:3px; border-radius:2px; display:inline-block; }
  .note { color:var(--dim); font-size:11px; margin-top:8px; }
</style>
</head>
<body>
<div class="console">
<div class="wrap">
  <div class="head">
    <h2 id="title">—</h2>
    <span class="meta" id="subtitle"></span>
    <span class="chip" id="armchip"></span>
  </div>

  <div class="grid" id="strips"></div>

  <div class="transport">
    <button class="play" id="play">▶ 播放</button>
    <div class="master">
      <label>主音量</label>
      <input type="range" id="master" min="0" max="100" value="70">
      <span class="val" id="masterVal">70%</span>
    </div>
    <input type="range" class="seek" id="seek" min="0" max="1000" value="0">
    <span class="clock" id="clock">0.00 / 0.00 s</span>
    <div class="toggles">
      <label><input type="checkbox" id="loopck"> 循环</label>
    </div>
  </div>

  <canvas id="canvas" height="240"></canvas>
  <div class="legend" id="legend"></div>
  <div class="note">F0 轨迹（WORLD/Harvest，10 ms 帧，60–500 Hz；相邻帧跳变 &gt;12 st 处断线）；虚线为满预算 endpoint，粗线为选择器输出 arm。</div>
</div>
</div>

<script>
const DATA = __PAYLOAD__;
const ROLE_ORDER = ["ref_src","ref_tgt","identity","endpoint","arm"];
const clips = DATA.clips;
let ac = null, master = null;
let players = [];          // per clip: {gain, src, buf, volume, mute, solo, eye}
let playing = false, startCtxTime = 0, startOffset = 0, lastB64Key = "";

const $ = id => document.getElementById(id);
const fmt = (t) => t.toFixed(2);

function totalDur() { return Math.max(...clips.map(c => c.dur)); }

function buildStrips() {
  const strips = $("strips"); strips.innerHTML = "";
  clips.forEach((c, i) => {
    const d = document.createElement("div");
    d.className = "strip"; d.style.setProperty("--c", c.color);
    d.innerHTML = `
      <div class="top"><span class="dot" style="background:${c.color}"></span>
        <span class="name">${c.label}</span></div>
      <div class="sub">${c.sub}</div>
      <div class="row"><label>音量</label>
        <input type="range" min="0" max="150" value="${c.role==='arm'?110:100}" data-vol="${i}"></div>
      <div class="btns">
        <button data-mute="${i}">M</button>
        <button data-solo="${i}">S</button>
        <button class="eye" data-eye="${i}" title="在 F0 图中显示">◉</button>
      </div>
      <div class="meter"><div class="fill" id="mf${i}"></div><div class="time" id="mt${i}">0.0s</div></div>`;
    strips.appendChild(d);
  });
  strips.querySelectorAll("[data-vol]").forEach(el => el.oninput = () => {
    players[+el.dataset.vol].volume = +el.value / 100; applyGains();
  });
  strips.querySelectorAll("[data-mute]").forEach(el => el.onclick = () => {
    const p = players[+el.dataset.mute]; p.mute = !p.mute;
    el.classList.toggle("on", p.mute); applyGains();
  });
  strips.querySelectorAll("[data-solo]").forEach(el => el.onclick = () => {
    const p = players[+el.dataset.solo]; p.solo = !p.solo;
    el.classList.toggle("on", p.solo); applyGains();
  });
  strips.querySelectorAll("[data-eye]").forEach(el => el.onclick = () => {
    const p = players[+el.dataset.eye]; p.eye = !p.eye;
    el.classList.toggle("off", !p.eye); drawF0();
  });
}

function applyGains(ramp) {
  const anySolo = players.some(p => p.solo);
  const t = ac ? ac.currentTime : 0;
  players.forEach(p => {
    if (!p.gain) return;
    const base = p.mute ? 0 : p.volume;
    const v = anySolo ? (p.solo ? base : 0) : base;
    if (ramp && ac) {
      p.gain.gain.cancelScheduledValues(t);
      p.gain.gain.setTargetAtTime(v, t, 0.015);
    } else {
      p.gain.gain.value = v;
    }
  });
}

const MASTER_MAX = 0.85;   // 耳朵安全上限：主音量拉到顶 = -1.4 dBFS
const FADE_S = 0.08;       // 播放/暂停淡入淡出，消除 click
let limiter = null, masterVal = 0.7;

function ensureCtx() {
  if (ac) return;
  ac = new (window.AudioContext || window.webkitAudioContext)();
  master = ac.createGain(); master.gain.value = masterVal * MASTER_MAX;
  limiter = ac.createDynamicsCompressor();
  limiter.threshold.value = -3;    // 软限幅：超过 -3 dBFS 的峰一律压住
  limiter.knee.value = 0;
  limiter.ratio.value = 20;
  limiter.attack.value = 0.003;
  limiter.release.value = 0.25;
  master.connect(limiter); limiter.connect(ac.destination);
  players = clips.map(() => ({gain:null, src:null, buf:null, volume:1, mute:false,
                              solo:false, eye:true}));
}

function applyMaster() {
  if (!master) return;
  const t = ac.currentTime;
  master.gain.cancelScheduledValues(t);
  master.gain.setTargetAtTime(masterVal * MASTER_MAX, t, 0.02);
  const el = $("masterVal"); if (el) el.textContent = Math.round(masterVal * 100) + "%";
}

function b64ToBuf(b64) {
  const bin = atob(b64), len = bin.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

function loadBuffers() {
  const key = clips.map(c => c.role).join(",") + "|" + (DATA.pair.id || "");
  if (key === lastB64Key && players.every(p => p.buf)) return Promise.resolve();
  lastB64Key = key;
  return Promise.all(clips.map((c, i) => new Promise((res, rej) => {
    const ab = b64ToBuf(c.b64);
    ac.decodeAudioData(ab.slice(0), b => { players[i].buf = b; res(); }, rej);
  })));
}

function stopSources() {
  players.forEach(p => { if (p.src) { try { p.src.stop(); } catch (e) {} p.src = null; } });
}

function playFrom(offset) {
  const dur = totalDur();
  if (offset >= dur - 0.01) offset = 0;
  ensureCtx();
  // resume 是异步的：必须等它落定，否则 currentTime 还是 0、起播立刻暂停会把位置算成负数
  const ready = (ac.state === "suspended") ? ac.resume() : Promise.resolve();
  ready.then(() => loadBuffers()).then(() => {
    if (ac.state !== "running") { $("clock").textContent = "音频被浏览器暂停（点一下页面再试）"; return; }
    stopSources();
    const t0 = ac.currentTime + 0.03;
    players.forEach((p, i) => {
      const c = clips[i];
      if (!p.gain) { p.gain = ac.createGain(); p.gain.connect(master); }
      const src = ac.createBufferSource();
      src.buffer = p.buf; src.connect(p.gain);
      const local = Math.max(0, offset);
      if (local < c.dur) src.start(t0, local);
      // 淡入：从 0 升到目标值（含音量/独奏/静音），避免起播 click
      const anySolo = players.some(q => q.solo);
      const base = p.mute ? 0 : p.volume;
      const target = anySolo ? (p.solo ? base : 0) : base;
      const g = p.gain.gain;
      g.cancelScheduledValues(ac.currentTime);
      g.setValueAtTime(0.0001, t0);
      g.linearRampToValueAtTime(Math.max(0.0001, target), t0 + FADE_S);
      p.src = src;
    });
    playing = true; startCtxTime = t0; startOffset = offset;
    $("play").textContent = "⏸ 暂停";
    requestAnimationFrame(tick);
  }).catch(err => { console.error(err); $("clock").textContent = "解码失败"; });
}

function pause() {
  if (!playing) return;
  startOffset = Math.min(totalDur(), Math.max(0, startOffset + (ac.currentTime - startCtxTime)));
  // 淡出后停，避免切停 click
  const t = ac.currentTime;
  players.forEach(p => { if (p.gain) { const g = p.gain.gain;
    g.cancelScheduledValues(t); g.setValueAtTime(Math.max(0.0001, g.value), t);
    g.linearRampToValueAtTime(0.0001, t + FADE_S); } });
  const stopAt = t + FADE_S + 0.02;
  players.forEach(p => { if (p.src) { try { p.src.stop(stopAt); } catch (e) {} } });
  setTimeout(() => { players.forEach(p => { p.src = null; }); }, (FADE_S + 0.05) * 1000);
  playing = false;
  $("play").textContent = "▶ 播放";
  tickOnce(startOffset);
}

function clockPos() {
  if (!playing) return startOffset;
  let t = startOffset + (ac.currentTime - startCtxTime);
  const dur = totalDur();
  if (t >= dur) {
    if ($("loopck").checked) {
      startOffset = 0; startCtxTime = ac.currentTime + 0.03;
      stopSources();
      players.forEach((p, i) => {
        const c = clips[i];
        if (!p.buf) return;
        const src = ac.createBufferSource(); src.buffer = p.buf;
        src.connect(p.gain); src.start(startCtxTime, 0); p.src = src;
      });
      return 0;
    }
    pause(); startOffset = dur; return dur;
  }
  return t;
}

function tick() {
  const dur = totalDur();
  let t = clockPos();
  $("seek").value = Math.round(1000 * Math.min(1, t / dur));
  $("clock").textContent = fmt(t) + " / " + fmt(dur) + " s";
  players.forEach((p, i) => {
    const c = clips[i];
    const f = Math.max(0, Math.min(1, t / c.dur));
    const el = $("mf" + i); if (el) el.style.inset = "0 " + ((1 - f) * 100) + "% 0 0";
    const mt = $("mt" + i); if (mt) mt.textContent = fmt(Math.min(t, c.dur)) + "s";
  });
  drawF0(t);
  if (playing) requestAnimationFrame(tick);
}

function drawF0(playT) {
  const cv = $("canvas");
  const W = cv.clientWidth, H = cv.height;
  if (cv.width !== W * 2) { cv.width = W * 2; }
  const g = cv.getContext("2d");
  g.setTransform(2, 0, 0, 2, 0, 0);
  g.clearRect(0, 0, W, H);
  const padL = 44, padR = 10, padT = 12, padB = 20;
  const plotW = W - padL - padR, plotH = H - padT - padB;

  // frequency range across visible traces
  let lo = Infinity, hi = -Infinity;
  clips.forEach((c, i) => {
    if (!players[i].eye) return;
    c.contour.forEach(v => { if (v > 0) { lo = Math.min(lo, v); hi = Math.max(hi, v); } });
  });
  if (!isFinite(lo)) { lo = 80; hi = 320; }
  lo = Math.max(50, lo * 0.88); hi = hi * 1.12;
  const ly = v => padT + plotH * (1 - (Math.log2(v) - Math.log2(lo)) / (Math.log2(hi) - Math.log2(lo)));
  const dur = totalDur();
  const lx = t => padL + plotW * t / dur;

  // grid
  g.strokeStyle = "#1d242d"; g.lineWidth = 1;
  [80, 100, 125, 160, 200, 250, 320, 400].forEach(hz => {
    if (hz < lo || hz > hi) return;
    const y = ly(hz);
    g.beginPath(); g.moveTo(padL, y); g.lineTo(W - padR, y); g.stroke();
    g.fillStyle = "#5a6572"; g.font = "10px Menlo,monospace";
    g.fillText(hz + " Hz", 4, y + 3);
  });
  for (let s = 0; s <= Math.ceil(dur); s++) {
    const x = lx(Math.min(s, dur));
    g.strokeStyle = "#1d242d"; g.beginPath(); g.moveTo(x, padT); g.lineTo(x, padT + plotH); g.stroke();
    g.fillStyle = "#5a6572"; g.fillText(s + "s", x + 3, H - 6);
  }

  // traces: identity muted wide, endpoint dashed, arm thick
  clips.forEach((c, i) => {
    if (!players[i].eye) return;
    const isEndpoint = c.role === "endpoint";
    const isArm = c.role === "arm";
    g.strokeStyle = c.color;
    g.lineWidth = isArm ? 2.4 : 1.4;
    g.setLineDash(isEndpoint ? [4, 3] : []);
    g.beginPath();
    let pen = false, prev = 0;
    c.contour.forEach((v, k) => {
      const t = k * c.hop_ms / 1000;
      if (t > dur) return;
      const jump = (v > 0 && prev > 0) ? Math.abs(12 * Math.log2(v / prev)) : 0;
      if (v > 0 && jump <= 12) {
        const x = lx(t), y = ly(v);
        if (!pen) { g.moveTo(x, y); pen = true; } else g.lineTo(x, y);
      } else pen = false;
      prev = v;
    });
    g.stroke(); g.setLineDash([]);
  });

  // playhead
  if (typeof playT === "number" && playT > 0) {
    const x = lx(Math.min(playT, dur));
    g.strokeStyle = "#2f81f7"; g.lineWidth = 1;
    g.beginPath(); g.moveTo(x, padT); g.lineTo(x, padT + plotH); g.stroke();
  }
}

function setupTransport() {
  $("play").onclick = () => { if (playing) pause(); else playFrom(clockPos()); };
  $("seek").oninput = () => {
    const t = +$("seek").value / 1000 * totalDur();
    if (playing) playFrom(t); else { startOffset = t; tickOnce(t); }
  };
  $("seek").onchange = () => { const t = +$("seek").value / 1000 * totalDur(); playFrom(t); };
  const ms = $("master");
  if (ms) {
    ms.oninput = () => { masterVal = +ms.value / 100;
      const el = $("masterVal"); if (el) el.textContent = Math.round(masterVal * 100) + "%";
      if (ac) applyMaster(); };
  }
  document.addEventListener("keydown", e => {
    if (e.code === "Space" && !e.repeat) { e.preventDefault();
      if (playing) pause(); else playFrom(clockPos()); }
  });
}

function tickOnce(t) {
  $("clock").textContent = fmt(t) + " / " + fmt(totalDur()) + " s";
  players.forEach((p, i) => {
    const c = clips[i];
    const f = Math.max(0, Math.min(1, t / c.dur));
    const el = $("mf" + i); if (el) el.style.inset = "0 " + ((1 - f) * 100) + "% 0 0";
    const mt = $("mt" + i); if (mt) mt.textContent = fmt(Math.min(t, c.dur)) + "s";
  });
  drawF0(t);
}

function buildLegend() {
  const lg = $("legend"); lg.innerHTML = "";
  clips.forEach(c => {
    const s = document.createElement("span");
    s.innerHTML = `<i style="background:${c.color}"></i>${c.label}`;
    lg.appendChild(s);
  });
}

window.__mix = { clips, players: () => players,
  state: () => ({ playing, startOffset, startCtxTime, ctxState: ac && ac.state,
                  masterGainValue: master ? +master.gain.value.toFixed(4) : null,
                  limiterThreshold: limiter ? limiter.threshold.value : null,
                  limiterRatio: limiter ? limiter.ratio.value : null,
                  masterMax: MASTER_MAX }) };

(function init() {
  const p = DATA.pair;
  $("title").textContent = `试听调音台 · ${p.id}`;
  $("subtitle").textContent = `源说话人 ${p.src_spk} → 目标音域 ${p.tgt_spk}`;
  const arm = p.arm_candidate || "";
  const chip = $("armchip");
  if (DATA.armEqualsEndpoint) { chip.textContent = "arm = endpoint（该对选择器返回满预算端点）"; }
  else { chip.textContent = `arm = ${arm}`; chip.classList.add("hot"); }
  buildStrips(); buildLegend(); setupTransport();
  ensureCtx();
  const dur0 = totalDur();
  $("clock").textContent = "0.00 / " + fmt(dur0) + " s";
  drawF0(0);
  window.addEventListener("resize", () => drawF0(clockPos()));
})();
</script>
</body>
</html>
"""


def main():
    pairs = load_index()
    analysis = load_analysis()

    st.markdown(
        "<style>"
        "h1 { font-size: 1.5rem !important; }"
        ".block-container { padding-top: 1.2rem; padding-bottom: 1rem; max-width: 1100px; }"
        "</style>",
        unsafe_allow_html=True,
    )
    st.title("音域适配克隆 · 试听调音台")
    st.caption(
        "ICASSP 实验的克隆链产物：把源说话人 A 的句子做**有界 F0 预算**编辑、"
        "向目标说话人 B 的音域靠拢。五条通道同一句、同一渲染管线；"
        "M/S 独奏静音、拉音量做 A/B，F0 图看音高轨迹。"
    )

    col1, col2, col3 = st.columns([2.2, 1.6, 2.6])
    with col1:
        pool = st.selectbox("语料池", ["dev78", "ravdess78"],
                            format_func=lambda x: {"dev78": "dev78 · ESD", "ravdess78": "ravdess78 · RAVDESS"}[x])
    sub = [p for p in pairs if p["pool"] == pool]
    with col2:
        pid = st.selectbox("样本对", [p["id"] for p in sub], index=0)
    pair = next(p for p in pairs if p["id"] == pid)
    with col3:
        a = analysis[pid]["clips"]
        st.markdown(
            f"<div style='padding-top:28px;color:#8b949e;font-size:12.5px'>"
            f"源 {pair['src_spk']} → 目标 {pair['tgt_spk']} · "
            f"arm 选择 <code>{pair['arm_candidate']}</code>"
            f"{' · （= endpoint）' if pair['arm_equals_endpoint'] else ''}</div>",
            unsafe_allow_html=True,
        )

    components.html(build_mixer_html(pair, analysis[pid]), height=600)

    # metrics table
    with st.expander("指标（WORLD F0：分布 / 与目标音域的 W1 / 对源句的逐帧位移）", expanded=False):
        rows = []
        for role in ROLES:
            c = analysis[pid]["clips"].get(role)
            if not c:
                continue
            d = c.get("disp") or {}
            rows.append({
                "通道": ROLE_LABEL[role],
                "均 F0": fmt_hz(c["f0_mean_hz"]),
                "P5–P95 (Hz)": f"{c['f0_lo_hz']:.0f}–{c['f0_hi_hz']:.0f}" if c.get("f0_lo_hz") else "—",
                "W1 → 目标音域 (st)": "—" if c.get("w1_to_tgt_st") is None else f"{c['w1_to_tgt_st']:.3f}",
                "位移 ≥1.5st 帧占比": "—" if not d else f"{d.get('disp_frac_ge_cap', 0):.0%}",
                "浊音帧占比": f"{c['voiced_frac']:.0%}",
                "时长 (s)": f"{c['dur_s']:.2f}",
            })
        st.dataframe(rows, hide_index=True, use_container_width=True)
        st.caption(
            "全部由 a8002 上的冻结运行时一次算出（WORLD/Harvest F0，10 ms 帧，60–500 Hz）："
            "W1 = 33 分位 log-F0 的成对 Wasserstein-1（semitone），越小越贴近目标音域；"
            "「位移 ≥1.5st 帧占比」= 触到 ℓ∞=1.5 预算帽的帧比例（端点普遍跑满帽子，符合有界预算的预期）。"
            "音频由冻结的 P26 渲染管线一次生成，本页只做重放；听感结论请以实际试听为准，本页不做听感主张。"
        )

    st.caption("音频来源：ESD / RAVDESS 语料 + 冻结的有界 F0 编辑链（WORLD 合成），用于内部试听。")


if __name__ == "__main__":
    main()
