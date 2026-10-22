"use strict";
// Arrange the existing, functional controls into the player-facing cabinet.
(() => {
  const $ = id => document.getElementById(id);
  document.body.classList.add("player-view");
  const cabinet = document.querySelector(".slot-cabinet");
  const dialog = (id, title) => {
    const node = document.createElement("dialog"); node.id = id; node.className = "app-dialog player-dialog";
    node.setAttribute("aria-labelledby", `${id}-title`);
    const heading = document.createElement("div"); heading.className = "dialog-heading";
    const label = document.createElement("h2"); label.id = `${id}-title`; label.textContent = title;
    label.dataset.i18n = id === "settings-dialog" ? "settingsTitle" : "paytable";
    const close = document.createElement("button"); close.type = "button"; close.className = "icon-button close-button"; close.textContent = "×"; close.setAttribute("aria-label", "Zamknij"); close.setAttribute("data-i18n-aria-label", "close");
    close.addEventListener("click", () => node.close()); heading.append(label, close); node.append(heading);
    node.addEventListener("click", event => {
      if (event.target !== node) return;
      const r = node.getBoundingClientRect();
      if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) node.close();
    });
    document.body.append(node); return node;
  };
  const settings = dialog("settings-dialog", "Ustawienia gry");
  settings.append(document.querySelector(".theme-toolbar"), document.querySelector(".language-field"));
  const testTools = document.querySelector(".testing-tools");
  const studio = new URLSearchParams(location.search).has("studio");
  testTools.hidden = !studio;
  settings.append(testTools);
  settings.append(document.querySelector(".history-section"));
  $("catalog-button").addEventListener("click", () => settings.close());
  const paytable = dialog("paytable-dialog", "Tabela wypłat"); paytable.append($("paytable-panel"));
  const utilities = document.createElement("div"); utilities.className = "player-utilities";
  cabinet.append(utilities);
  for (const id of ["rules-button", "paytable-toggle"]) {
    const button = $(id); button.classList.add("utility-button"); utilities.append(button);
  }
  $("paytable-toggle").setAttribute("aria-controls", "paytable-dialog");
  $("paytable-toggle").setAttribute("aria-haspopup", "dialog");
  $("paytable-toggle").setAttribute("aria-label", "Tabela wypłat");
  $("paytable-toggle").setAttribute("data-i18n-aria-label", "paytable");
  $("paytable-toggle").setAttribute("data-i18n-title", "paytable");
  $("paytable-toggle").removeAttribute("aria-expanded");
  $("paytable-toggle").addEventListener("click", event => { event.stopImmediatePropagation(); paytable.showModal(); });
  const gear = document.createElement("button"); gear.id = "settings-button"; gear.type = "button"; gear.className = "icon-button utility-button";
  gear.setAttribute("aria-label", "Ustawienia gry"); gear.title = "Ustawienia gry"; gear.setAttribute("aria-haspopup", "dialog");
  gear.setAttribute("data-i18n-aria-label", "settingsTitle"); gear.setAttribute("data-i18n-title", "settingsTitle");
  gear.innerHTML = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m10 3-.8 3-2.5 1.4-3 .1-1 3 2.4 1.9.1 2.9-1.3 2.7 2.5 2 2.7-1.2 2.9.2 1.8 2.4 3-1 .3-3 1.4-2.4 2.8-.8v-3l-2.8-.9-1.5-2.4-.2-3-3-1-1.9 2.4-2.8.2L10 3Z"/><circle cx="12" cy="12" r="3"/></svg>';
  gear.addEventListener("click", () => settings.showModal()); utilities.append(gear);
  const bottom = document.createElement("div"); bottom.className = "player-bottom-bar";
  bottom.append(utilities, document.querySelector(".cabinet-meter"), document.querySelector(".game-controls")); cabinet.append(bottom);
  cabinet.append($("autoplay-progress"));
  const demo = document.createElement("span"); demo.className = "player-demo-label"; demo.textContent = "DEMO"; cabinet.append(demo);
})();
