"use strict";

/**
 * animation.js - rein dekorative Bewegung der von game.js erzeugten
 * Tier-Sprites. Jedes Sprite "wandert" per zufaelligem Sprung innerhalb
 * der Grenzen seiner Gehege-Box umher und wird per CSS-Transition (siehe
 * game.css, `.animal-sprite { transition: ... }`) sanft dorthin animiert.
 *
 * Wichtig: Das ist reiner Client-Zustand. Positionen werden nie an den
 * Server geschickt und haben keinerlei Einfluss auf Domain-/Backend-Daten -
 * ausschliesslich Praesentation.
 *
 * Schwerpunkt: Frontend (Presentation Layer) - Alessio Bellamacina
 *
 * Zoo-Spiel-Feature-Ausbau (2026-08-09) ergaenzt mit Unterstuetzung von
 * Kaiss Saleh (Datenbank-Schwerpunkt): Sprites mit `data-mood="sleeping"`
 * (siehe game.js, computeMood()) bewegen sich nicht.
 *
 * Ergaenzt mit Unterstuetzung von Alessio Bellamacina (Frontend-
 * Schwerpunkt), 2026-08-09 (siehe planning_backend_darnell.md Abschnitt
 * 2.11): `computeMood()`s "sleeping"-Anzeige haengt an `animal.energy`,
 * das serverseitig nur bei einem Simulationsschritt (manueller Klick auf
 * "Simulationsschritt ausfuehren") aktualisiert wird - beim reinen
 * Zuschauen ohne Klicks wuerde man ein Tier daher ggf. nie schlafen
 * sehen. `triggerRandomNap()` versetzt deshalb rein clientseitig
 * (kosmetisch, kein Server-Request, keine Aenderung an echten
 * Domain-Daten) periodisch ein zufaelliges, aktuell nicht schlafendes
 * Sprite fuer ein paar Sekunden in denselben "sleeping"-Zustand -
 * dieselbe Anzeige/Bewegungssperre wie ein echt niedriger Energiewert,
 * nur garantiert oefter sichtbar.
 */

const STEP_INTERVAL_MS = 900;
const MAX_STEP_PX = 40;
const LABEL_RESERVE_PX = 14; // Platz unterhalb des Emojis fuer den Namen

// Muss NICHT exakt mit game.js's MOOD_ICONS.sleeping synchron gehalten
// werden (rein kosmetischer Nickerchen-Effekt, kein Domain-Zustand),
// verwendet aber bewusst dasselbe 💤-Icon fuer ein konsistentes Bild.
const NAP_ICON = "\u{1F4A4}"; // 💤
const NAP_INTERVAL_MS = 20000;
const NAP_DURATION_MS = 8000;

/**
 * Liefert einen zufaelligen Versatz zwischen -MAX_STEP_PX und +MAX_STEP_PX.
 *
 * Args/Returns: number
 *
 * Test:
 *   TC-A01: Given `MAX_STEP_PX = 40`, when `randomStep()` viele Male
 *     aufgerufen wird, then liegen alle Ergebnisse im Bereich [-40, 40].
 *   TC-A02: Given mehrere Aufrufe von `randomStep()`, when man die
 *     Ergebnisse vergleicht, then sind sie (mit ueberwaeltigender
 *     Wahrscheinlichkeit) nicht alle identisch (echte Zufallsstreuung).
 */
function randomStep() {
  return (Math.random() * 2 - 1) * MAX_STEP_PX;
}

/**
 * Begrenzt `value` auf das Intervall [min, max].
 *
 * Args: value, min, max (number)
 * Returns: number
 *
 * Test:
 *   TC-A03: Given value=100, min=0, max=50, when `clamp(value, min, max)`
 *     aufgerufen wird, then ist das Ergebnis 50.
 *   TC-A04: Given value=-10, min=0, max=50, when `clamp(value, min, max)`
 *     aufgerufen wird, then ist das Ergebnis 0.
 */
function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

/**
 * Bewegt ein einzelnes Sprite um einen zufaelligen Schritt, ohne die
 * Grenzen seiner Gehege-Box (`pen`) zu verlassen.
 *
 * Args: sprite (HTMLElement), pen (HTMLElement, das umgebende
 *   .enclosure-pen-Element)
 * Returns: undefined
 *
 * Test:
 *   TC-A05: Given ein Sprite steht nahe am rechten Rand seiner 260px
 *     breiten Gehege-Box, when `moveSprite(sprite, pen)` wiederholt
 *     aufgerufen wird, then bleibt `sprite.style.left` immer <= der
 *     Boxbreite minus Sprite-Breite (kein Verlassen der Box).
 *   TC-A06: Given ein frisch erzeugtes Sprite ohne vorherige
 *     `style.left`/`style.top`, when `moveSprite(sprite, pen)` aufgerufen
 *     wird, then wird eine gueltige Position (>= 0) gesetzt, statt mit
 *     NaN abzubrechen.
 *   TC-A11: Given ein Sprite hat `dataset.mood === "sleeping"` (siehe
 *     game.js, computeMood()), when `moveSprite(sprite, pen)` aufgerufen
 *     wird, then bleiben `style.left`/`style.top` unveraendert (schlafende
 *     Tiere bewegen sich nicht).
 *   TC-A12: Given ein Sprite bewegt sich zu einem `left`-Wert, der kleiner
 *     ist als der vorherige, when `moveSprite(sprite, pen)` aufgerufen
 *     wird, then wird `dataset.facing` auf "left" gesetzt (siehe game.css,
 *     `.animal-sprite-emoji` wird dadurch gespiegelt).
 */
function moveSprite(sprite, pen) {
  if (sprite.dataset.mood === "sleeping") {
    return;
  }
  const penRect = pen.getBoundingClientRect();
  const spriteRect = sprite.getBoundingClientRect();

  const maxLeft = Math.max(0, penRect.width - spriteRect.width);
  const maxTop = Math.max(0, penRect.height - spriteRect.height - LABEL_RESERVE_PX);

  const currentLeft = parseFloat(sprite.style.left) || 0;
  const currentTop = parseFloat(sprite.style.top) || 0;
  const newLeft = clamp(currentLeft + randomStep(), 0, maxLeft);

  sprite.dataset.facing = newLeft < currentLeft ? "left" : "right";
  sprite.style.left = `${newLeft}px`;
  sprite.style.top = `${clamp(currentTop + randomStep(), 0, maxTop)}px`;
}

/**
 * Ein Bewegungsschritt fuer alle aktuell im DOM vorhandenen Sprites.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-A07: Given 2 Gehege-Boxen mit zusammen 5 Sprites, when `tick()`
 *     aufgerufen wird, then aendert sich fuer jedes der 5 Sprites
 *     `style.left` oder `style.top` (oder bleibt zufaellig gleich, aber
 *     kein Sprite wird uebersprungen).
 *   TC-A08: Given keine Gehege-Boxen existieren im DOM (z.B. Fehlerseite),
 *     when `tick()` aufgerufen wird, then passiert nichts und es wird
 *     keine Exception geworfen.
 */
function tick() {
  document.querySelectorAll(".enclosure-pen").forEach((pen) => {
    pen.querySelectorAll(".animal-sprite").forEach((sprite) => {
      moveSprite(sprite, pen);
    });
  });
}

/**
 * Startet die Bewegungs-Schleife (ein sofortiger Schritt, danach im
 * festen Intervall). Wird von game.js nach dem Erzeugen der Sprites
 * aufgerufen, siehe `window.ZooAnimation.start()`.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-A09: Given `start()` wird aufgerufen, when man kurz danach die
 *     Sprite-Positionen prueft, then wurden sie bereits mindestens einmal
 *     gesetzt (nicht erst nach STEP_INTERVAL_MS).
 *   TC-A10: Given `start()` wurde bereits aufgerufen, when die Seite laenger
 *     als mehrere STEP_INTERVAL_MS offen bleibt, then bewegen sich die
 *     Sprites wiederholt (Intervall laeuft dauerhaft, nicht nur einmalig).
 */
function start() {
  tick();
  setInterval(tick, STEP_INTERVAL_MS);
  setInterval(triggerRandomNap, NAP_INTERVAL_MS);
}

/**
 * Versetzt ein zufaelliges, aktuell nicht schlafendes Sprite fuer
 * `NAP_DURATION_MS` in den "sleeping"-Zustand (Icon + Bewegungsstopp,
 * siehe Modul-Docstring), dann zurueck in seinen vorherigen Zustand
 * (echtes `sick`/`hungry`/kein Mood-Icon bleibt danach wieder sichtbar).
 * Rein praesentations-seitig - siehe Modul-Docstring fuer den Grund.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-A13: Given mindestens ein Sprite ohne `data-mood="sleeping"`
 *     existiert im DOM, when `triggerRandomNap()` aufgerufen wird, then
 *     hat danach genau ein Sprite `data-mood === "sleeping"` und ein
 *     💤-Icon, und `moveSprite()` bewegt es nicht mehr.
 *   TC-A14: Given kein Sprite im DOM (oder alle bereits schlafend),
 *     when `triggerRandomNap()` aufgerufen wird, then passiert nichts
 *     und es wird keine Exception geworfen.
 */
function triggerRandomNap() {
  const candidates = Array.from(document.querySelectorAll(".animal-sprite")).filter(
    (sprite) => sprite.dataset.mood !== "sleeping"
  );
  if (!candidates.length) {
    return;
  }
  const sprite = candidates[Math.floor(Math.random() * candidates.length)];
  const previousMood = sprite.dataset.mood || "";
  let moodIcon = sprite.querySelector(".animal-sprite-mood");
  const previousIconText = moodIcon ? moodIcon.textContent : null;
  if (!moodIcon) {
    moodIcon = document.createElement("span");
    moodIcon.className = "animal-sprite-mood";
    sprite.appendChild(moodIcon);
  }
  moodIcon.textContent = NAP_ICON;
  sprite.dataset.mood = "sleeping";

  setTimeout(() => {
    sprite.dataset.mood = previousMood;
    if (previousIconText !== null) {
      moodIcon.textContent = previousIconText;
    } else if (moodIcon.isConnected) {
      moodIcon.remove();
    }
  }, NAP_DURATION_MS);
}

window.ZooAnimation = { start };
