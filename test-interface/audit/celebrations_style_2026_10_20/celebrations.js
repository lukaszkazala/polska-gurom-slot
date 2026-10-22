"use strict";
// Presentation only: the caller supplies the already validated, credited result.
(() => {
  let current = null;
  const copy = {
    pl: {skip:"Pomiń animację",big:"WIELKA WYGRANA",mega:"MEGA WYGRANA",epic:"EPICKA WYGRANA"},
    en: {skip:"Skip animation",big:"BIG WIN",mega:"MEGA WIN",epic:"EPIC WIN"},
    de: {skip:"Animation überspringen",big:"GROSSGEWINN",mega:"MEGA GEWINN",epic:"EPISCHER GEWINN"}
  };
  const tier = (win, bet) => {
    if (!Number.isFinite(win) || !Number.isFinite(bet) || bet <= 0 || win < bet * 20) return null;
    return win >= bet * 100 ? "epic" : win >= bet * 50 ? "mega" : "big";
  };
  function clear() { if (current) current(); }
  function play({kind = "bonus", title = "", value = "", detail = "", duration = 1800} = {}) {
    clear();
    if (document.hidden) return Promise.resolve();
    const cabinet = document.querySelector(".slot-cabinet");
    if (!cabinet) return Promise.resolve();
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const words = copy[document.documentElement.lang] || copy.en;
    const overlay = document.createElement("section");
    overlay.className = "celebration";
    overlay.dataset.kind = kind;
    const announcement = document.createElement("span");
    announcement.className = "celebration-sr";
    announcement.setAttribute("role", "status"); announcement.setAttribute("aria-live", "polite");
    announcement.textContent = [title || words[kind], value, detail].filter(Boolean).join(". ");
    const rays = document.createElement("div"); rays.className = "celebration-rays"; rays.setAttribute("aria-hidden", "true");
    const particles = document.createElement("div"); particles.className = "celebration-particles"; particles.setAttribute("aria-hidden", "true");
    if (!reduced) for (let i = 0; i < 26; i++) {
      const coin = document.createElement("i");
      coin.style.setProperty("--x", `${(i * 37 + 11) % 100}%`);
      coin.style.setProperty("--delay", `${-(i % 9) * .21}s`);
      coin.style.setProperty("--drift", `${(i % 5 - 2) * 24}px`);
      coin.style.setProperty("--duration", `${1.7 + (i % 7) * .14}s`);
      particles.append(coin);
    }
    const card = document.createElement("div"); card.className = "celebration-card"; card.setAttribute("aria-hidden", "true");
    const ornament = document.createElement("span"); ornament.className = "celebration-ornament"; ornament.textContent = "✦  ◆  ✦";
    const heading = document.createElement("strong"); heading.className = "celebration-title"; heading.textContent = title || words[kind];
    const amount = document.createElement("strong"); amount.className = "celebration-value"; amount.textContent = value; amount.hidden = !value;
    const note = document.createElement("span"); note.className = "celebration-detail"; note.textContent = detail;
    card.append(ornament,heading,amount,note);
    const skip = document.createElement("button"); skip.type = "button"; skip.className = "celebration-skip"; skip.textContent = words.skip;
    overlay.append(rays,particles,card,skip,announcement); cabinet.append(overlay);
    return new Promise(resolve => {
      let timer;
      const finish = () => {
        clearTimeout(timer); overlay.remove();
        if (current === finish) current = null;
        resolve();
      };
      current = finish; skip.addEventListener("click",finish,{once:true});
      timer = setTimeout(finish,reduced ? 650 : duration);
    });
  }
  document.addEventListener("visibilitychange", () => { if (document.hidden) clear(); });
  window.addEventListener("pagehide",clear);
  window.PG_CELEBRATION = Object.freeze({play,clear,tier});
})();
