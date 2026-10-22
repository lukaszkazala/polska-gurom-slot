"use strict";
// Local, decoded music loops and one bounded cue voice. Audio never gates a round.
(() => {
  const files = {
    base: "01_Karczma_Disco_BASE_120bpm_Dm.wav",
    bonus: "02_Szarza_Husarza_BONUS_120bpm_Dm.wav",
    bonusIntro: "03_Wejscie_do_bonusu.wav",
    win: "04_Wygrana.wav",
    bigWin: "05_Duza_wygrana.wav",
    returned: "06_Czesciowy_zwrot.wav"
  };
  let muted = false;
  try { muted = localStorage.getItem("pg-muted") === "true"; } catch {}
  let ctx, master, music, loop, cue, cueLevel, scene = "base", unlocked = false, disposed = false;
  const buffers = new Map(), loading = new Map();
  const audible = () => unlocked && !muted && !document.hidden && !disposed;
  const gain = (node, value, seconds = .12) => {
    const now = ctx.currentTime;
    node.gain.cancelScheduledValues(now);
    node.gain.setValueAtTime(node.gain.value, now);
    node.gain.linearRampToValueAtTime(value, now + seconds);
  };
  function stopCue() {
    if (cue) { cue.onended = null; try { cue.stop(); } catch {} cue.disconnect(); cueLevel.disconnect(); cue = null; cueLevel = null; }
    if (music) gain(music, .24);
  }
  function sync() {
    if (!ctx || disposed) return;
    // A zero-duration master change silences even an in-progress fade or fanfare.
    gain(master, audible() ? 1 : 0, 0);
    if (!audible()) stopCue();
    if (!audible() || ctx.state !== "running" || !buffers.has(scene) || loop?.key === scene) return;
    const old = loop, voice = ctx.createBufferSource(), level = ctx.createGain();
    voice.buffer = buffers.get(scene); voice.loop = true;
    voice.connect(level); level.connect(music);
    level.gain.setValueAtTime(0, ctx.currentTime); gain(level, 1, .3);
    loop = { key: scene, voice, level }; voice.start();
    if (old) {
      gain(old.level, 0, .3);
      old.voice.onended = () => { old.voice.disconnect(); old.level.disconnect(); };
      old.voice.stop(ctx.currentTime + .32);
    }
  }
  function load(key) {
    if (loading.has(key)) return loading.get(key);
    const work = (async () => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      try {
        const response = await fetch(`assets/audio/${files[key]}`, { signal: controller.signal });
        if (!response.ok) throw new Error("audio_unavailable");
        const buffer = await ctx.decodeAudioData(await response.arrayBuffer());
        if (!disposed) { buffers.set(key, buffer); sync(); }
      } catch { loading.delete(key); } // Missing audio must not affect game recovery.
      finally { clearTimeout(timeout); }
    })();
    loading.set(key, work); return work;
  }
  function unlock() {
    if (disposed) return;
    try {
      const Audio = window.AudioContext || window.webkitAudioContext;
      if (!Audio) return;
      if (!ctx) {
        ctx = new Audio(); master = ctx.createGain(); music = ctx.createGain();
        master.gain.value = 0; music.gain.value = .24;
        music.connect(master); master.connect(ctx.destination);
        ctx.onstatechange = sync;
      }
      unlocked = true;
      Promise.resolve(ctx.resume()).then(sync).catch(() => {});
      Object.keys(files).forEach(load); sync();
    } catch {} // Unsupported/blocked audio still leaves a playable silent game.
  }
  function play(key) {
    stopCue();
    if (!audible() || ctx?.state !== "running" || !buffers.has(key)) return;
    // Never enqueue a cue whose result may already have disappeared when decoding ends.
    cue = ctx.createBufferSource(); cue.buffer = buffers.get(key);
    const voice = cue, level = ctx.createGain(); cueLevel = level; level.gain.value = key === "returned" ? .28 : .65;
    voice.connect(level); level.connect(master); gain(music, .065, .06);
    voice.onended = () => { voice.disconnect(); level.disconnect(); if (cue === voice) { cue = null; cueLevel = null; gain(music, .24, .25); } };
    voice.start();
  }
  window.PG_AUDIO = {
    get muted() { return muted; },
    unlock,
    toggle() {
      muted = !muted;
      try { localStorage.setItem("pg-muted", String(muted)); } catch {}
      if (!muted) unlock(); sync(); return muted;
    },
    scene(key) { scene = key === "bonus" ? "bonus" : "base"; sync(); },
    beginRound() { stopCue(); scene = "base"; sync(); },
    bonus() { scene = "bonus"; sync(); play("bonusIntro"); },
    result(win, bet) { scene = "base"; sync(); if (win > 0) play(win <= bet ? "returned" : win / bet >= 20 ? "bigWin" : "win"); },
    get status() { return { muted, unlocked, scene, context: ctx?.state || "idle", loaded: [...buffers.keys()], cue: !!cue }; }
  };
  document.addEventListener("visibilitychange", sync);
  window.addEventListener("pagehide", event => {
    if (event.persisted) return;
    disposed = true; stopCue(); if (loop) { try { loop.voice.stop(); } catch {} }
    if (ctx) void ctx.close().catch(() => {});
  });
})();
