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
 */

const STEP_INTERVAL_MS = 900;
const MAX_STEP_PX = 40;
const LABEL_RESERVE_PX = 14; // Platz unterhalb des Emojis fuer den Namen

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
 */
function moveSprite(sprite, pen) {
  const penRect = pen.getBoundingClientRect();
  const spriteRect = sprite.getBoundingClientRect();

  const maxLeft = Math.max(0, penRect.width - spriteRect.width);
  const maxTop = Math.max(0, penRect.height - spriteRect.height - LABEL_RESERVE_PX);

  const currentLeft = parseFloat(sprite.style.left) || 0;
  const currentTop = parseFloat(sprite.style.top) || 0;

  sprite.style.left = `${clamp(currentLeft + randomStep(), 0, maxLeft)}px`;
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
}

window.ZooAnimation = { start };
