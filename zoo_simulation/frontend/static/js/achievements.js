"use strict";

/**
 * achievements.js - kleine, rein clientseitige "Errungenschaften" als
 * Toast-Benachrichtigung, um dem Zoo-Spiel ein Erfolgserlebnis zu geben.
 * Liest ausschliesslich Daten, die der Server bereits mit der Seite
 * mitgeliefert hat (_hud.html-Datenattribute fuer Besucher, #animals-data
 * falls auf der Seite vorhanden) - keine zusaetzlichen Requests, keine
 * neue ZooController-Methode. Der Freischalt-Zustand liegt in
 * localStorage (browserlokal, nicht Teil der Domain-/Server-Daten).
 *
 * Ergaenzt von Kaiss Saleh (Datenbank-Schwerpunkt) im Rahmen des
 * Zoo-Spiel-Feature-Ausbaus, gemeinsam mit Alessio Bellamacina
 * (Frontend-Schwerpunkt).
 */

const UNLOCKED_KEY_PREFIX = "zoo-achievement-";
const LAST_ANIMAL_COUNT_KEY = "zoo-last-animal-count";

const CONTENT_HUNGER_THRESHOLD = 20;
const CONTENT_ENERGY_THRESHOLD = 60;

const ACHIEVEMENTS = [
  {
    id: "first_visitor",
    label: "🎟️ Erster Besucher!",
    check: (ctx) => ctx.currentVisitors !== null && ctx.currentVisitors >= 1,
  },
  {
    id: "zoo_full",
    label: "🏟️ Der Zoo ist ausverkauft!",
    check: (ctx) =>
      ctx.maximumVisitors !== null &&
      ctx.maximumVisitors > 0 &&
      ctx.currentVisitors >= ctx.maximumVisitors,
  },
  {
    id: "all_content",
    label: "😊 Alle Tiere sind zufrieden!",
    check: (ctx) =>
      ctx.animals.length > 0 &&
      ctx.animals.every(
        (animal) =>
          animal.hunger <= CONTENT_HUNGER_THRESHOLD && animal.energy >= CONTENT_ENERGY_THRESHOLD
      ),
  },
  {
    id: "new_resident",
    label: "🦁 Neuer Bewohner im Zoo!",
    check: (ctx) => ctx.animalCountIncreased,
  },
  {
    id: "enclosure_full",
    label: "🏠 Ein Gehege ist komplett belegt!",
    check: (ctx) =>
      ctx.enclosures.some(
        (enclosure) => enclosure.capacity > 0 && enclosure.occupied_count >= enclosure.capacity
      ),
  },
];

/**
 * Prueft, ob ein Achievement bereits freigeschaltet wurde.
 *
 * Args: id (string). Returns: boolean.
 *
 * Test:
 *   TC-AC01: Given das Achievement wurde noch nie freigeschaltet, when
 *     `isUnlocked(id)` aufgerufen wird, then wird false zurueckgegeben.
 *   TC-AC02: Given `unlock(id)` wurde zuvor aufgerufen, when
 *     `isUnlocked(id)` aufgerufen wird, then wird true zurueckgegeben.
 */
function isUnlocked(id) {
  return window.localStorage.getItem(UNLOCKED_KEY_PREFIX + id) === "true";
}

/**
 * Merkt ein Achievement dauerhaft als freigeschaltet (browserlokal).
 *
 * Args: id (string). Returns: undefined.
 *
 * Test:
 *   TC-AC10: Given `unlock("zoo_full")` wird aufgerufen, when
 *     `isUnlocked("zoo_full")` danach aufgerufen wird, then wird true
 *     zurueckgegeben.
 *   TC-AC11: Given `unlock(id)` wird zweimal hintereinander mit derselben
 *     id aufgerufen, when man den localStorage-Eintrag danach prueft, then
 *     bleibt er unveraendert "true" (idempotent, kein Fehler).
 */
function unlock(id) {
  window.localStorage.setItem(UNLOCKED_KEY_PREFIX + id, "true");
}

/**
 * Sammelt den aktuellen Kontext (Besucherzahlen, Tierliste, Gehegeliste,
 * Tierbestands-Veraenderung) aus dem bereits gerenderten DOM. Funktioniert
 * gleichermassen auf dem Dashboard (nur Besucher-/Tier-Daten vorhanden) wie
 * auf der Spielansicht (zusaetzlich #enclosures-data).
 *
 * Args/Returns: keine / Object mit currentVisitors, maximumVisitors,
 *   animals, enclosures, animalCountIncreased.
 *
 * Test:
 *   TC-AC03: Given die Seite enthaelt kein Element mit
 *     `[data-current-visitors]` (sollte nicht vorkommen, da _hud.html
 *     ueberall eingebunden ist), when `readContext()` aufgerufen wird,
 *     then sind `currentVisitors`/`maximumVisitors` null statt NaN.
 *   TC-AC04: Given dies ist der allererste Aufruf auf dieser Seite (kein
 *     vorher gespeicherter Tierbestand in localStorage), when
 *     `readContext()` aufgerufen wird, then ist `animalCountIncreased`
 *     false (nur eine Baseline wird gespeichert, kein falscher Alarm beim
 *     ersten Laden).
 *   TC-AC09: Given `#enclosures-data` fehlt (z.B. Dashboard, das keine
 *     Gehege-Liste einbettet), when `readContext()` aufgerufen wird, then
 *     ist `enclosures` ein leeres Array statt einer Exception.
 */
function readContext() {
  const visitorsElement = document.querySelector("[data-current-visitors]");
  const currentVisitors = visitorsElement
    ? Number(visitorsElement.dataset.currentVisitors)
    : null;
  const maximumVisitors = visitorsElement
    ? Number(visitorsElement.dataset.maximumVisitors)
    : null;

  const animalsDataElement = document.getElementById("animals-data");
  let animals = [];
  if (animalsDataElement) {
    try {
      animals = JSON.parse(animalsDataElement.textContent);
    } catch (error) {
      animals = [];
    }
  }

  const enclosuresDataElement = document.getElementById("enclosures-data");
  let enclosures = [];
  if (enclosuresDataElement) {
    try {
      enclosures = JSON.parse(enclosuresDataElement.textContent);
    } catch (error) {
      enclosures = [];
    }
  }

  let animalCountIncreased = false;
  if (animalsDataElement) {
    const storedCount = window.localStorage.getItem(LAST_ANIMAL_COUNT_KEY);
    if (storedCount !== null) {
      animalCountIncreased = animals.length > Number(storedCount);
    }
    window.localStorage.setItem(LAST_ANIMAL_COUNT_KEY, String(animals.length));
  }

  return { currentVisitors, maximumVisitors, animals, enclosures, animalCountIncreased };
}

let toastQueue = [];
let toastShowing = false;

/**
 * Zeigt den naechsten Toast aus der Warteschlange (falls vorhanden) fuer
 * einige Sekunden an und faehrt danach mit dem naechsten fort - so
 * ueberlappen sich mehrere gleichzeitig freigeschaltete Achievements
 * nicht.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-AC05: Given zwei Achievements werden in derselben `checkAchievements()`-
 *     Ausfuehrung freigeschaltet, when die Toasts angezeigt werden, then
 *     erscheinen sie nacheinander, nie gleichzeitig.
 *   TC-AC06: Given die Warteschlange ist leer, when `showNextToast()`
 *     aufgerufen wird, then passiert nichts, keine Exception.
 */
function showNextToast() {
  const toast = document.getElementById("achievement-toast");
  const next = toastQueue.shift();
  if (!toast || !next) {
    toastShowing = false;
    return;
  }
  toastShowing = true;
  toast.textContent = next.label;
  toast.classList.remove("hidden");
  if (window.ZooSound) {
    window.ZooSound.play("achievement");
  }
  window.setTimeout(() => {
    toast.classList.add("hidden");
    window.setTimeout(showNextToast, 300);
  }, 3200);
}

/**
 * Reiht ein Achievement in die Toast-Warteschlange ein und startet die
 * Anzeige sofort, falls gerade kein anderer Toast laeuft.
 *
 * Args: achievement (Object) - Eintrag aus ACHIEVEMENTS. Returns: undefined.
 *
 * Test:
 *   TC-AC12: Given kein Toast wird aktuell angezeigt, when
 *     `queueToast(achievement)` aufgerufen wird, then wird
 *     `showNextToast()` sofort ausgeloest.
 *   TC-AC13: Given bereits ein Toast wird angezeigt, when `queueToast()`
 *     erneut aufgerufen wird, then wird das neue Achievement nur an die
 *     Warteschlange angehaengt, ohne den laufenden Toast zu unterbrechen.
 */
function queueToast(achievement) {
  toastQueue.push(achievement);
  if (!toastShowing) {
    showNextToast();
  }
}

/**
 * Prueft alle Achievements gegen den aktuellen Kontext und schaltet neu
 * erreichte frei (Toast + Freischalt-Flag). Wird einmal pro Seitenaufruf
 * aufgerufen; bereits freigeschaltete Achievements werden uebersprungen.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-AC07: Given `current_visitors` erreicht erstmals `maximum_visitors`,
 *     when `checkAchievements()` aufgerufen wird, then wird "zoo_full"
 *     freigeschaltet und ein Toast angezeigt.
 *   TC-AC08: Given ein Achievement wurde in einem frueheren Seitenaufruf
 *     bereits freigeschaltet, when `checkAchievements()` erneut aufgerufen
 *     wird und die Bedingung weiterhin zutrifft, then wird kein zweiter
 *     Toast angezeigt.
 */
function checkAchievements() {
  const context = readContext();
  ACHIEVEMENTS.forEach((achievement) => {
    if (isUnlocked(achievement.id)) {
      return;
    }
    if (achievement.check(context)) {
      unlock(achievement.id);
      queueToast(achievement);
    }
  });
}

document.addEventListener("DOMContentLoaded", checkAchievements);

window.ZooAchievements = { checkAchievements };
