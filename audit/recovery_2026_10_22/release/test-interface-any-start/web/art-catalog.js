"use strict";
// Drawing coordinates crop the unmodified texture atlas at display time.
window.PG_ART = {
  files: {
    folklore: {src: "assets/art/polskie-motywy.png", width: 1254, height: 1254},
    classic: {src: "assets/art/klasyczne-motywy.png", width: 1774, height: 887},
    hussar: {src: "assets/art/husarz.png", width: 1254, height: 1254},
    special: {src: "assets/art/symbole-specjalne.png", width: 1774, height: 887}
  },
  symbols: {
    car: {pl:"Maluch", en:"Little car", de:"Kleinwagen", file:"folklore", box:[12,35,426,325]},
    bread: {pl:"Obwarzanek", en:"Bread ring", de:"Gebäckring", file:"folklore", box:[442,15,371,363]},
    castle: {pl:"Zamek królewski", en:"Royal castle", de:"Königsschloss", file:"folklore", box:[814,4,440,394]},
    cheese: {pl:"Oscypek", en:"Smoked cheese", de:"Räucherkäse", file:"folklore", box:[0,418,419,341]},
    mermaid: {pl:"Syrenka", en:"Mermaid", de:"Meerjungfrau", file:"folklore", box:[420,379,418,426]},
    dumplings: {pl:"Pierogi", en:"Pierogi", de:"Pierogi", file:"folklore", box:[824,426,430,335]},
    stork: {pl:"Bocian", en:"Stork", de:"Storch", file:"folklore", box:[20,775,350,456]},
    dragon: {pl:"Smok wawelski", en:"Legendary dragon", de:"Sagenhafter Drache", file:"folklore", box:[423,803,416,439]},
    hussar: {pl:"Husarz", en:"Hussar", de:"Husar", file:"hussar", box:[0,0,1254,1254]},
    diamond: {pl:"Diament", en:"Diamond", de:"Diamant", file:"classic", box:[214,375,168,162]},
    spade: {pl:"Pik", en:"Spade", de:"Pik", file:"classic", box:[393,375,167,162]},
    heart: {pl:"Serce", en:"Heart", de:"Herz", file:"classic", box:[572,375,168,162]},
    club: {pl:"Trefl", en:"Club", de:"Kreuz", file:"classic", box:[751,375,169,162]},
    lily: {pl:"Lilia", en:"Lily", de:"Lilie", file:"classic", box:[932,375,168,162]},
    goblet: {pl:"Kielich", en:"Goblet", de:"Kelch", file:"classic", box:[214,549,168,163]},
    crown: {pl:"Korona", en:"Crown", de:"Krone", file:"classic", box:[393,549,167,163]},
    wild: {pl:"WILD", en:"WILD", de:"WILD", file:"special", box:[4,65,939,762]},
    scatter: {pl:"SCATTER", en:"SCATTER", de:"SCATTER", file:"special", box:[977,0,797,887]}
  },
  themes: {
    polska: {pl:"Polska", en:"Poland", de:"Polen", symbols:{L1:"bread", L2:"dumplings", L3:"cheese", L4:"car", P1:"stork", P2:"castle", P3:"mermaid", P4:"hussar", WILD:"wild", SCATTER:"scatter"}},
    legendy: {pl:"Legendy", en:"Legends", de:"Legenden", symbols:{L1:"diamond", L2:"spade", L3:"heart", L4:"club", P1:"lily", P2:"castle", P3:"dragon", P4:"hussar", WILD:"wild", SCATTER:"scatter"}},
    klasyczny: {pl:"Klasyczny", en:"Classic", de:"Klassisch", symbols:{L1:"diamond", L2:"spade", L3:"heart", L4:"club", P1:"lily", P2:"goblet", P3:"crown", P4:"hussar", WILD:"wild", SCATTER:"scatter"}}
  }
};
