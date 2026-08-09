"use strict";

/**
 * sound.js - kurze Soundeffekte per Web Audio API (kein externes Audio-
 * Asset noetig) fuer Spiel-Aktionen (Klick, Fuettern, Ticketkauf,
 * Tageswechsel, Achievement). Stellt window.ZooSound.play(name) bereit,
 * das andere Skripte (game.js, achievements.js) aufrufen koennen, und
 * verdrahtet den Mute-Schalter im Header (siehe templates/base.html,
 * #sound-toggle). Der Mute-Zustand wird in localStorage gemerkt, damit er
 * ueber Seitenwechsel/Neustarts erhalten bleibt - reiner Client-Zustand,
 * ohne jeden Einfluss auf Server-/Domain-Daten.
 *
 * Ergaenzt von Kaiss Saleh (Datenbank-Schwerpunkt) im Rahmen des
 * Zoo-Spiel-Feature-Ausbaus, gemeinsam mit Alessio Bellamacina
 * (Frontend-Schwerpunkt).
 */

const MUTE_STORAGE_KEY = "zoo-sound-muted";

// Jeder Sound ist eine kurze Folge von [Frequenz Hz, Dauer ms] - bewusst
// simple Oszillator-Toene statt Audiodateien, damit keine Lizenz-/
// Download-Fragen fuer ein Schulprojekt entstehen.
const SOUND_DEFINITIONS = {
  click: [[440, 60]],
  feed: [[520, 70], [660, 90]],
  ticket: [[660, 60], [880, 60], [1050, 90]],
  day: [[330, 90], [440, 90], [550, 140]],
  adopt: [[440, 70], [590, 70], [740, 120]],
  achievement: [[660, 80], [880, 80], [990, 80], [1180, 160]],
};

// Reihenfolge ist relevant: die erste passende Teilzeichenkette gewinnt.
// Die durchsuchten Nachrichten stammen aus controller_stub.py (siehe dort
// feed_animal()/sell_ticket()/run_simulation_step()/add_animal()) - rein
// englischer Text, deshalb englische Stichworte.
const FLASH_SOUND_KEYWORDS = [
  ["ticket sold", "ticket"],
  ["was fed", "feed"],
  ["simulation step", "day"],
  ["added", "adopt"],
];

let audioContext = null;

/**
 * Liefert den (lazy erzeugten) AudioContext, oder null, falls der Browser
 * die Web Audio API nicht unterstuetzt.
 *
 * Args/Returns: AudioContext | null
 *
 * Test:
 *   TC-S01: Given die Web Audio API ist verfuegbar, when getAudioContext()
 *     mehrfach aufgerufen wird, then wird immer dieselbe Instanz
 *     zurueckgegeben (kein neuer Context pro Sound).
 *   TC-S02: Given die Web Audio API ist nicht verfuegbar (z.B. sehr alter
 *     Browser), when getAudioContext() aufgerufen wird, then wird null
 *     zurueckgegeben statt eine Exception zu werfen.
 */
function getAudioContext() {
  if (audioContext) {
    return audioContext;
  }
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) {
    return null;
  }
  audioContext = new AudioContextClass();
  return audioContext;
}

/**
 * Prueft, ob der Nutzer Sound stummgeschaltet hat.
 *
 * Args/Returns: boolean
 *
 * Test:
 *   TC-S03: Given localStorage enthaelt noch keinen Eintrag, when
 *     isMuted() aufgerufen wird, then wird false zurueckgegeben (Sound an
 *     per Default).
 *   TC-S04: Given der Mute-Schalter wurde zuvor aktiviert, when isMuted()
 *     aufgerufen wird, then wird true zurueckgegeben.
 */
function isMuted() {
  return window.localStorage.getItem(MUTE_STORAGE_KEY) === "true";
}

/**
 * Spielt einen benannten Sound ab, sofern nicht stummgeschaltet.
 *
 * Args: name (string) - einer der Schluessel aus SOUND_DEFINITIONS.
 * Returns: undefined
 *
 * Test:
 *   TC-S05: Given Sound ist nicht stummgeschaltet und name="feed", when
 *     play("feed") aufgerufen wird, then werden die in SOUND_DEFINITIONS
 *     hinterlegten Toene ueber den AudioContext geplant.
 *   TC-S06: Given Sound ist stummgeschaltet, when play(irgendein name)
 *     aufgerufen wird, then wird kein Ton erzeugt (frueher Ausstieg).
 */
function play(name) {
  if (isMuted()) {
    return;
  }
  const notes = SOUND_DEFINITIONS[name];
  const context = getAudioContext();
  if (!notes || !context) {
    return;
  }

  let startTime = context.currentTime;
  notes.forEach(([frequency, durationMs]) => {
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = frequency;
    gain.gain.setValueAtTime(0.15, startTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, startTime + durationMs / 1000);
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start(startTime);
    oscillator.stop(startTime + durationMs / 1000);
    startTime += durationMs / 1000;
  });
}

/**
 * Verdrahtet den Mute-Schalter im Header: liest den gespeicherten Zustand,
 * spiegelt ihn im Button (Icon/aria-pressed) und schaltet ihn per Klick um.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-S07: Given der Button #sound-toggle existiert im DOM, when
 *     initSoundToggle() aufgerufen wird, then zeigt sein Text/aria-pressed
 *     den aktuell gespeicherten Mute-Zustand korrekt an.
 *   TC-S08: Given der Button ist sichtbar und Sound ist aktuell an, when
 *     der Button geklickt wird, then wird Sound stummgeschaltet und der
 *     Zustand in localStorage gespeichert; ein erneuter Klick schaltet ihn
 *     wieder an.
 */
function initSoundToggle() {
  const button = document.getElementById("sound-toggle");
  if (!button) {
    return;
  }

  const applyState = () => {
    const muted = isMuted();
    button.textContent = muted ? "\u{1F507}" : "\u{1F50A}"; // 🔇 / 🔊
    button.setAttribute("aria-pressed", String(muted));
  };

  applyState();
  button.addEventListener("click", () => {
    window.localStorage.setItem(MUTE_STORAGE_KEY, String(!isMuted()));
    applyState();
    play("click");
  });
}

/**
 * Spielt nach einem Post/Redirect/Get-Zyklus einen passenden Sound anhand
 * der ersten Erfolgs-Flash-Message ab (z.B. "Ticket sold for 5.00." ->
 * "ticket"). Reines Best-Effort-Feature: bei mehreren Flash-Messages zaehlt
 * nur die erste, bei keinem Treffer passiert nichts.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-S09: Given eine `.flash-success`-Meldung mit Text "Ticket sold for
 *     5.00." ist im DOM, when playForFlashMessages() aufgerufen wird, then
 *     wird der "ticket"-Sound abgespielt.
 *   TC-S10: Given keine Flash-Messages sind im DOM (normaler Seitenaufruf
 *     ohne vorherige Formular-Aktion), when playForFlashMessages()
 *     aufgerufen wird, then passiert nichts, keine Exception.
 */
function playForFlashMessages() {
  const successMessage = document.querySelector(".flash-success");
  if (!successMessage) {
    return;
  }
  const text = successMessage.textContent.toLowerCase();
  const match = FLASH_SOUND_KEYWORDS.find(([keyword]) => text.includes(keyword));
  if (match) {
    play(match[1]);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initSoundToggle();
  playForFlashMessages();
});

window.ZooSound = { play };
