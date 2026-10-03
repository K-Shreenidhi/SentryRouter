// Synthesizes the soundtrack + in-key SFX for the SentryRouter brag video.
// A minor, 120 BPM, downbeats at 0.5 + 2k s (aligned with scene cuts in composition.html).
const fs = require('fs');
const path = require('path');
const SR = 48000, DUR = 23, N = SR * DUR;
const L = new Float32Array(N), R = new Float32Array(N), REV = new Float32Array(N);
const TAU = Math.PI * 2;
const rnd = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
let seed = 7; const noise = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 2147483648 - 1; };
const lpCoef = fc => 1 - Math.exp(-TAU * fc / SR);

function add(t0, len, fn, gain = 1, pan = 0, rev = 0) {
  const s0 = Math.floor(t0 * SR), n = Math.floor(len * SR);
  const gl = gain * Math.cos((pan + 1) * Math.PI / 4), gr = gain * Math.sin((pan + 1) * Math.PI / 4);
  for (let i = 0; i < n; i++) {
    const j = s0 + i; if (j < 0 || j >= N) continue;
    const v = fn(i / SR, j / SR);
    L[j] += v * gl; R[j] += v * gr; REV[j] += v * gain * rev;
  }
}
// sidechain ducking from the four-on-the-floor kick
const duck = t => (t >= 2.5 && t < 20.5) ? 1 - 0.55 * Math.exp(-((t - 2.5) % 0.5) / 0.09) : 1;

// ---------- harmony ----------
const CH = {
  Am: { root: 55.0, pad: [220.0, 261.63, 329.63, 440.0] },
  F:  { root: 43.65, pad: [174.61, 220.0, 261.63, 349.23] },
  C:  { root: 65.41, pad: [196.0, 261.63, 329.63, 392.0] },
  G:  { root: 49.0, pad: [196.0, 246.94, 293.66, 392.0] },
};
const chordAt = b => (b <= 1 || b >= 10) ? 'Am' : ['Am', 'F', 'C', 'G'][(b - 1) % 4];
const barStart = b => 0.5 + 2 * b;

// ---------- pad ----------
for (let b = -1; b <= 11; b++) {
  const ch = CH[chordAt(b)], t0 = Math.max(0, barStart(b)), t1 = Math.min(DUR, barStart(b + 1));
  ch.pad.forEach((f, k) => {
    let p1 = 0, p2 = 0, y1 = 0, y2 = 0;
    const len = t1 - t0 + 0.6;
    add(t0, len, (x, t) => {
      p1 += f * 1.003 / SR; p2 += f * 0.997 / SR;
      const s = ((p1 % 1) * 2 - 1) + ((p2 % 1) * 2 - 1);
      const fc = t < 2.5 ? 380 + 260 * (t / 2.5) : t < 20.5 ? 1500 + 400 * Math.sin(t * 0.7) : 1500 - 700 * Math.min(1, (t - 20.5) / 2.5);
      const a = lpCoef(fc); y1 += a * (s - y1); y2 += a * (y1 - y2);
      const env = Math.min(1, x / 0.25) * (x > t1 - t0 ? Math.exp(-(x - (t1 - t0)) / 0.18) : 1);
      return y2 * env * duck(t);
    }, k === 3 ? 0.018 : 0.03, (k - 1.5) * 0.35, 0.5);
  });
}

// ---------- kick ----------
function kick(t0, g, click = true) {
  let ph = 0;
  add(t0, 0.5, x => {
    const f = 46 + 80 * Math.exp(-x * 32); ph += f / SR;
    return Math.sin(TAU * ph) * Math.exp(-x * 7) + (click ? noise() * Math.exp(-x * 320) * 0.25 : 0);
  }, g);
}
kick(0.5, 0.32, false); kick(1.5, 0.32, false);           // heartbeat under the hook
for (let t = 2.5; t < 20.5 - 1e-6; t += 0.5) kick(t, 0.55);
kick(20.5, 0.7);

// ---------- hats ----------
for (let t = 2.75, i = 0; t < 20.5; t += 0.5, i++) {
  let lp = 0; add(t, 0.12, x => { const n = noise(); lp += 0.25 * (n - lp); return (n - lp) * Math.exp(-x * 55); }, 0.06, i % 2 ? 0.3 : -0.3);
}
for (let t = 6.5, i = 0; t < 16.5; t += 0.125, i++) {
  if (i % 4 === 2) continue;
  let lp = 0; add(t, 0.05, x => { const n = noise(); lp += 0.3 * (n - lp); return (n - lp) * Math.exp(-x * 120); }, 0.018, i % 2 ? 0.5 : -0.5);
}

// ---------- clap (beats 2 & 4) ----------
for (let t = 7.0; t < 20.5; t += 1.0) {
  let lp = 0, hp = 0;
  add(t, 0.3, x => {
    const n = noise(); lp += lpCoef(2200) * (n - lp); hp += lpCoef(700) * (lp - hp);
    const env = x < 0.03 ? (Math.exp(-(x % 0.01) * 300)) : Math.exp(-(x - 0.03) * 18);
    return (lp - hp) * env;
  }, 0.16, 0, 0.35);
}

// ---------- bass (offbeat 8ths) ----------
for (let b = 1; b <= 9; b++) {
  const f = CH[chordAt(b)].root * 2;
  for (let k = 0; k < 4; k++) {
    const t0 = barStart(b) + k * 0.5 + 0.25;
    let ph = 0, y = 0, y2 = 0;
    add(t0, 0.24, (x, t) => {
      ph += f / SR; const s = (ph % 1) * 2 - 1;
      const a = lpCoef(260 + 900 * Math.exp(-x * 20)); y += a * (s - y); y2 += a * (y - y2);
      return y2 * Math.exp(-x * 7) * Math.min(1, x / 0.004);
    }, 0.32);
  }
}

// ---------- pluck arp (16ths) ----------
const PAT = [0, 2, 1, 3, 2, 1, 3, 2];
for (let t = 6.5, i = 0; t < 20.5 - 1e-6; t += 0.125, i++) {
  const b = Math.floor((t - 0.5) / 2), ch = CH[chordAt(b)];
  const f = ch.pad[PAT[i % 8]] * 2;
  let ph = 0;
  const g = t < 16.5 ? 0.04 : 0.025;
  add(t, 0.35, x => { ph += f / SR; return (Math.sin(TAU * ph) + 0.25 * Math.sin(2 * TAU * ph)) * Math.exp(-x * 16) * Math.min(1, x / 0.003); },
    g, i % 2 ? 0.45 : -0.45, 0.45);
}

// ---------- SFX ----------
function bell(t0, f, g, pan = 0, decay = 4) {
  let p = 0, q = 0;
  add(t0, 1.6, x => { p += f / SR; q += f * 2.76 / SR;
    return (Math.sin(TAU * p) + 0.35 * Math.sin(TAU * q) * Math.exp(-x * 9)) * Math.exp(-x * decay) * Math.min(1, x / 0.002); }, g, pan, 0.55);
}
function whoosh(tCut, g = 0.09) {
  const len = 0.55; let y = 0, y2 = 0;
  add(tCut - 0.42, len, x => {
    const u = x / len, fc = 600 + 4200 * u, a = lpCoef(fc), n = noise();
    y += a * (n - y); y2 += a * (y - y2);
    return y2 * Math.pow(Math.sin(Math.PI * u), 2) * 2.2;
  }, g, 0, 0.3);
}
function impact(t0, g) {
  let ph = 0, y = 0;
  add(t0, 2.2, x => { ph += (55 + 30 * Math.exp(-x * 20)) / SR; const n = noise(); y += lpCoef(500) * (n - y);
    return Math.sin(TAU * ph) * Math.exp(-x * 2.4) + y * Math.exp(-x * 7) * 1.6; }, g, 0, 0.5);
}
function thud(t0, g) {
  let ph = 0, y = 0;
  add(t0, 0.9, x => { ph += 82.41 * (1 - 0.18 * Math.min(1, x / 0.3)) / SR; const n = noise(); y += lpCoef(320) * (n - y);
    return Math.sin(TAU * ph) * Math.exp(-x * 5) + y * Math.exp(-x * 14) * 2; }, g, 0, 0.3);
}
function tick(t0, f, g, pan = 0) {
  let ph = 0; add(t0, 0.15, x => { ph += f / SR; return (Math.sin(TAU * ph) + 0.2 * Math.sin(3 * TAU * ph)) * Math.exp(-x * 28); }, g, pan, 0.2);
}
function click(t0, g, pan) {
  let y = 0; add(t0, 0.04, x => { const n = noise(); y += lpCoef(1400) * (n - y); return y * Math.exp(-x * 140); }, g, pan);
}

// riser into the reveal
{ let y = 0; add(1.35, 1.15, (x) => { const u = x / 1.15, a = lpCoef(250 + 6000 * u * u), n = noise(); y += a * (n - y); return y * u * u * 1.8; }, 0.14, 0, 0.3); }
// hook failure
thud(1.0, 0.42); [1.0, 1.07, 1.14].forEach((t, i) => click(t, 0.12, i - 1));
// reveal
impact(2.5, 0.42); bell(2.62, 880, 0.03, -0.2); bell(2.7, 1318.5, 0.025, 0.2);
// scene whooshes
[6.5, 10.5, 14.5, 16.5, 20.5].forEach(t => whoosh(t));
// failover
[7.2, 7.45, 7.7].forEach((t, i) => tick(t, 329.63, 0.1, 0.4));
thud(7.75, 0.4);
bell(7.88, 880, 0.05, 0.2); bell(7.96, 1318.5, 0.04, 0.3);
// rate limit — resolution order shared with composition.html
const order = [...Array(50).keys()].sort((a, b) => rnd(a + 500) - rnd(b + 500));
const PENT = [440, 523.25, 587.33, 659.25, 783.99, 880, 1046.5, 1174.66, 1318.51, 1567.98];
for (let r = 0; r < 50; r++) {
  const t = 11.5 + r * 0.024, p = order[r];
  const pan = ((p % 10) / 9 - 0.5) * 0.9;
  if (r < 10) bell(t, PENT[r], 0.035, pan, 6); else click(t, 0.05, pan);
}
for (let row = 0; row < 5; row++) click(10.85 + row * 0.05, 0.03, 0.3);
// singleflight
{ let y = 0; add(14.7, 0.5, x => { const u = x / 0.5, n = noise(); y += lpCoef(400 + 2500 * u) * (n - y); return y * Math.sin(Math.PI * u) * 1.6; }, 0.06, -0.3, 0.3); }
bell(15.5, 1318.5, 0.07, 0.3);
[880, 1046.5, 1318.5, 1760].forEach((f, i) => bell(15.75 + i * 0.035, f, 0.028, -0.4 + i * 0.1, 6));
// proof counters landing
bell(17.3, 880, 0.045, -0.3); bell(17.8, 1318.5, 0.045, 0.3);
// outro
impact(20.5, 0.4); bell(20.62, 440, 0.04, 0); bell(21.45, 1318.5, 0.03, 0.2);

// ---------- reverb (Schroeder) ----------
function reverb(input, off) {
  const out = new Float32Array(N);
  const combs = [1687, 1601, 1867, 1523].map(d => d + off), fb = 0.78, damp = 0.3;
  for (const d of combs) {
    const buf = new Float32Array(d); let idx = 0, filt = 0;
    for (let i = 0; i < N; i++) { const o = buf[idx]; filt = o * (1 - damp) + filt * damp; buf[idx] = input[i] + filt * fb; idx = (idx + 1) % d; out[i] += o * 0.25; }
  }
  for (const d of [245 + off, 605 + off]) {
    const buf = new Float32Array(d); let idx = 0;
    for (let i = 0; i < N; i++) { const b = buf[idx]; const y = -out[i] * 0.5 + b; buf[idx] = out[i] + b * 0.5; out[i] = y; idx = (idx + 1) % d; }
  }
  return out;
}
const wl = reverb(REV, 0), wr = reverb(REV, 23);

// ---------- master ----------
let peak = 0;
const ML = new Float32Array(N), MR = new Float32Array(N);
for (let i = 0; i < N; i++) {
  const t = i / SR;
  const fade = Math.min(1, t / 0.01) * (t > 22.3 ? Math.max(0, 1 - (t - 22.3) / 0.7) : 1);
  const l = Math.tanh((L[i] + wl[i] * 0.3) * 1.25), r = Math.tanh((R[i] + wr[i] * 0.3) * 1.25);
  ML[i] = l * fade; MR[i] = r * fade; peak = Math.max(peak, Math.abs(ML[i]), Math.abs(MR[i]));
}
const norm = 0.89 / peak;
const buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVE', 8); buf.write('fmt ', 12);
buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24);
buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) {
  buf.writeInt16LE(Math.round(Math.max(-1, Math.min(1, ML[i] * norm)) * 32767), 44 + i * 4);
  buf.writeInt16LE(Math.round(Math.max(-1, Math.min(1, MR[i] * norm)) * 32767), 46 + i * 4);
}
fs.writeFileSync(path.join(__dirname, 'music.wav'), buf);
console.log('wrote music.wav, pre-norm peak', peak.toFixed(3));
