"use strict";
// Explicit visual preview only: no game API, no random draws, no wallet calls.
document.querySelectorAll("[data-effect]").forEach(button => button.addEventListener("click", () => {
  const kind = button.dataset.effect;
  const data = kind === "bonus" ? {title:"8 DARMOWYCH OBROTÓW",detail:"×4 · Mnożnik dotyczy wygranych linii"} : {value:({big:"40,00 zł",mega:"100,00 zł",epic:"200,00 zł"})[kind],detail:({big:"20×",mega:"50×",epic:"100×"})[kind]};
  window.PG_CELEBRATION.play({kind,...data,duration:12000});
}));
