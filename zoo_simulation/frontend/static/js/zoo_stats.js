"use strict";

/**
 * zoo_stats.js - berechnet und zeigt aggregierte "Tycoon"-Kennzahlen
 * (Wohlfuehl-Score, Zoo-Level, Artensammlung, Attraktivitaets-Score) aus
 * den bereits vom Server mitgelieferten Tierdaten (`#animals-data`). Laeuft
 * sitewide (siehe base.html), da sowohl Dashboard als auch Spielansicht
 * jetzt `animals_json` einbetten (siehe zoo_view.py, `show_zoo_status()`/
 * `show_animals()`) - kein zusaetzlicher Request, keine neue
 * ZooController-Methode. Ersetzt die fruehere, nur auf der Spielansicht
 * laufende Wohlfuehl-Score-Berechnung in game.js.
 *
 * Ergaenzt von Kaiss Saleh (Datenbank-Schwerpunkt) im Rahmen des
 * Zoo-Spiel-Feature-Ausbaus, gemeinsam mit Alessio Bellamacina
 * (Frontend-Schwerpunkt).
 */

const SPECIES_EMOJI_STATS = {
  Lion: "\u{1F981}",
  Giraffe: "\u{1F992}",
  Penguin: "\u{1F427}",
};

// Level-Schwellen nach Gesamt-Tieranzahl - rein clientseitige Tycoon-
// Fortschrittsanzeige, kein Backend-Konzept.
const ZOO_LEVELS = [
  { level: 1, minAnimals: 0, title: "Kleiner Tierpark" },
  { level: 2, minAnimals: 5, title: "Wachsender Zoo" },
  { level: 3, minAnimals: 10, title: "Etablierter Zoo" },
  { level: 4, minAnimals: 15, title: "Großer Zoo" },
  { level: 5, minAnimals: 20, title: "Mega-Zoo" },
];

/**
 * Liest die vom Server eingebettete Tierliste aus `#animals-data`, falls
 * auf der aktuellen Seite vorhanden (Dashboard und Spielansicht haben es,
 * andere Seiten nicht).
 *
 * Args/Returns: (keine) / Array von Tier-Objekten oder leeres Array.
 *
 * Test:
 *   TC-ZS01: Given `#animals-data` enthaelt gueltiges JSON mit 7 Tieren,
 *     when `loadAnimalsData()` aufgerufen wird, then liefert es ein Array
 *     mit 7 Eintraegen.
 *   TC-ZS02: Given das Element fehlt (z.B. Finanzbericht-Seite), when
 *     `loadAnimalsData()` aufgerufen wird, then liefert es ein leeres
 *     Array statt einer Exception.
 */
function loadAnimalsData() {
  const dataElement = document.getElementById("animals-data");
  if (!dataElement) {
    return [];
  }
  try {
    return JSON.parse(dataElement.textContent);
  } catch (error) {
    console.error("zoo-stats: animals-data konnte nicht gelesen werden", error);
    return [];
  }
}

/**
 * Durchschnittlicher Wohlfuehl-Score, mit derselben Formel wie
 * `Zoo.calculate_average_welfare()`/`Animal.calculate_welfare()` im
 * Backend (Mittelwert aus health, 100-hunger, energy je Tier, dann
 * Mittelwert ueber alle Tiere) - siehe domain/zoo.py bzw.
 * domain/animals/animal.py. Rein clientseitige Anzeige-Berechnung.
 *
 * Args: animals (Array). Returns: number | null (0-100, null wenn leer).
 *
 * Test:
 *   TC-ZS03: Given ein Tier mit health=100, hunger=0, energy=100, when
 *     `computeWelfareScore([animal])` aufgerufen wird, then wird 100
 *     zurueckgegeben.
 *   TC-ZS04: Given ein leeres Array, when `computeWelfareScore([])`
 *     aufgerufen wird, then wird null zurueckgegeben (keine Division
 *     durch 0).
 */
function computeWelfareScore(animals) {
  if (!animals.length) {
    return null;
  }
  const total = animals.reduce(
    (sum, animal) => sum + (animal.health + (100 - animal.hunger) + animal.energy) / 3,
    0
  );
  return total / animals.length;
}

/**
 * Bestimmt das aktuelle Zoo-Level und den Fortschritt zum naechsten Level
 * anhand der Gesamt-Tieranzahl.
 *
 * Args: animalCount (number). Returns: Object mit level/title/minAnimals/
 *   next/progressPct.
 *
 * Test:
 *   TC-ZS05: Given animalCount=7, when `computeZooLevel(7)` aufgerufen
 *     wird, then ist `.level` 2 ("Wachsender Zoo", Schwelle bei 5).
 *   TC-ZS06: Given animalCount=25 (ueber der hoechsten Schwelle), when
 *     `computeZooLevel(25)` aufgerufen wird, then ist `.next` null und
 *     `.progressPct` 100.
 */
function computeZooLevel(animalCount) {
  let current = ZOO_LEVELS[0];
  ZOO_LEVELS.forEach((entry) => {
    if (animalCount >= entry.minAnimals) {
      current = entry;
    }
  });
  const next = ZOO_LEVELS[ZOO_LEVELS.indexOf(current) + 1] || null;
  const progressPct = next
    ? Math.min(
        100,
        ((animalCount - current.minAnimals) / (next.minAnimals - current.minAnimals)) * 100
      )
    : 100;
  return { ...current, next, progressPct };
}

/**
 * Zaehlt Tiere je Spezies.
 *
 * Args: animals (Array). Returns: Object, z.B. {Lion: 3, Giraffe: 2}.
 *
 * Test:
 *   TC-ZS07: Given 3 Loewen und 2 Giraffen, when
 *     `computeSpeciesCounts(animals)` aufgerufen wird, then liefert es
 *     `{Lion: 3, Giraffe: 2}`.
 *   TC-ZS08: Given ein leeres Array, when `computeSpeciesCounts([])`
 *     aufgerufen wird, then liefert es ein leeres Object.
 */
function computeSpeciesCounts(animals) {
  const counts = {};
  animals.forEach((animal) => {
    counts[animal.species] = (counts[animal.species] || 0) + 1;
  });
  return counts;
}

/**
 * Kombinierter "Attraktivitaets-Score" (0-100) aus Wohlfuehl, Artenvielfalt
 * und Besucherzahl - eine reine Anzeige-Kennzahl ohne Entsprechung im
 * Domain-Modell, gedacht als Tycoon-Fortschrittsgefuehl.
 *
 * Args: animals (Array), speciesCount (number), currentVisitors (number).
 * Returns: number (0-100, gerundet).
 *
 * Test:
 *   TC-ZS09: Given perfektes Wohlfuehl (100), 3 Arten und 25+ Besucher,
 *     when `computeAttractivenessScore(...)` aufgerufen wird, then wird
 *     der Wert auf 100 gedeckelt, nicht darueber hinaus berechnet.
 *   TC-ZS10: Given keine Tiere, 0 Arten, 0 Besucher, when
 *     `computeAttractivenessScore([], 0, 0)` aufgerufen wird, then wird 0
 *     zurueckgegeben.
 */
function computeAttractivenessScore(animals, speciesCount, currentVisitors) {
  const welfare = computeWelfareScore(animals) || 0;
  const diversityBonus = Math.min(30, speciesCount * 10);
  const visitorBonus = Math.min(20, Math.floor(currentVisitors / 5));
  return Math.min(100, Math.round(welfare * 0.5 + diversityBonus + visitorBonus));
}

/**
 * Waehlt ein Stimmungs-Emoji passend zum Wohlfuehl-Score.
 *
 * Args: score (number, 0-100). Returns: string (Emoji).
 *
 * Test:
 *   TC-ZS13: Given score=85, when `moodEmojiForScore(85)` aufgerufen
 *     wird, then wird das froehliche Emoji ("\u{1F600}") zurueckgegeben.
 *   TC-ZS14: Given score=10, when `moodEmojiForScore(10)` aufgerufen
 *     wird, then wird das unzufriedene Emoji ("\u{1F61F}") zurueckgegeben.
 */
function moodEmojiForScore(score) {
  if (score >= 70) {
    return "\u{1F600}";
  }
  return score >= 40 ? "\u{1F610}" : "\u{1F61F}";
}

/**
 * Rendert alle Kennzahlen in die HUD-Elemente (siehe templates/_hud.html),
 * falls diese auf der aktuellen Seite vorhanden sind. Jedes Element wird
 * einzeln per `getElementById` geprueft, damit Seiten, die nur einen Teil
 * der HUD-Karten rendern (oder gar keine), nicht brechen.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-ZS11: Given `#hud-level-value`/`#hud-level-progress-fill` existieren
 *     und 7 Tiere sind vorhanden, when `renderStats()` aufgerufen wird,
 *     then zeigt `#hud-level-value` "Lvl 2 – Wachsender Zoo" und die
 *     Balkenbreite spiegelt den Fortschritt zu Level 3.
 *   TC-ZS12: Given keines der HUD-Elemente existiert auf der Seite, when
 *     `renderStats()` aufgerufen wird, then passiert nichts, keine
 *     Exception.
 */
function renderStats() {
  const animals = loadAnimalsData();

  const welfareTarget = document.getElementById("hud-welfare-value");
  if (welfareTarget) {
    const score = computeWelfareScore(animals);
    welfareTarget.textContent =
      score === null ? "–" : `${Math.round(score)} ${moodEmojiForScore(score)}`;
  }

  const levelTarget = document.getElementById("hud-level-value");
  const levelProgressFill = document.getElementById("hud-level-progress-fill");
  if (levelTarget) {
    const levelInfo = computeZooLevel(animals.length);
    levelTarget.textContent = `Lvl ${levelInfo.level} – ${levelInfo.title}`;
    if (levelProgressFill) {
      levelProgressFill.style.width = `${levelInfo.progressPct}%`;
    }
  }

  const speciesCounts = computeSpeciesCounts(animals);
  const speciesTarget = document.getElementById("hud-species-value");
  if (speciesTarget) {
    const parts = Object.entries(speciesCounts).map(
      ([species, count]) => `${SPECIES_EMOJI_STATS[species] || "\u{1F43E}"}×${count}`
    );
    speciesTarget.textContent = parts.length ? parts.join(" ") : "–";
  }

  const attractivenessTarget = document.getElementById("hud-attractiveness-value");
  if (attractivenessTarget) {
    const visitorsElement = document.querySelector("[data-current-visitors]");
    const currentVisitors = visitorsElement ? Number(visitorsElement.dataset.currentVisitors) : 0;
    const score = computeAttractivenessScore(
      animals,
      Object.keys(speciesCounts).length,
      currentVisitors
    );
    attractivenessTarget.textContent = `${score} ⭐`;
  }
}

document.addEventListener("DOMContentLoaded", renderStats);

window.ZooStats = {
  computeWelfareScore,
  computeZooLevel,
  computeSpeciesCounts,
  computeAttractivenessScore,
};
