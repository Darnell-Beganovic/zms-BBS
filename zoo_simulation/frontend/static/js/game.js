"use strict";

/**
 * game.js - baut die Tier-Sprites in ihre Gehege-Boxen ein und steuert das
 * Klick-Popup (Stats + Fuetterungsformular). Nutzt ausschliesslich Daten,
 * die der Server schon mit der Seite mitgeliefert hat (siehe
 * templates/animals_game.html, `#animals-data`) - kein zusaetzlicher
 * HTTP-Request, kein neuer ZooController-Aufruf.
 *
 * Die Bewegung der hier erzeugten Sprites uebernimmt animation.js
 * (getrennte Datei); dieses Skript erzeugt nur die Elemente und setzt
 * ihre Startposition.
 *
 * Schwerpunkt: Frontend (Presentation Layer) - Alessio Bellamacina
 */

const SPECIES_EMOJI = {
  Lion: "\u{1F981}", // 🦁
  Giraffe: "\u{1F992}", // 🦒
  Penguin: "\u{1F427}", // 🐧
};
const DEFAULT_EMOJI = "\u{1F43E}"; // 🐾 fuer unbekannte/zukuenftige Spezies

function speciesEmoji(species) {
  return SPECIES_EMOJI[species] || DEFAULT_EMOJI;
}

/**
 * Liest die vom Server eingebettete Tierliste aus dem JSON-<script>-Tag.
 *
 * Args: (keine)
 * Returns: Array von Tier-Objekten (id, name, species, age, health,
 *   hunger, energy, enclosure_id), oder ein leeres Array, falls das
 *   Element fehlt oder kein gueltiges JSON enthaelt.
 *
 * Test:
 *   TC-J01: Given das `#animals-data`-Element enthaelt gueltiges JSON mit
 *     7 Tieren, when `loadAnimals()` aufgerufen wird, then liefert es ein
 *     Array mit 7 Eintraegen.
 *   TC-J02: Given das `#animals-data`-Element fehlt auf der Seite (z.B.
 *     Fehlerzustand), when `loadAnimals()` aufgerufen wird, then liefert
 *     es ein leeres Array statt einer Exception.
 */
function loadAnimals() {
  const dataElement = document.getElementById("animals-data");
  if (!dataElement) {
    return [];
  }
  try {
    return JSON.parse(dataElement.textContent);
  } catch (error) {
    console.error("zoo-game: animals-data konnte nicht gelesen werden", error);
    return [];
  }
}

/**
 * Erstellt das DOM-Element fuer ein einzelnes Tier-Sprite.
 *
 * Args: animal (Object) - ein Eintrag aus loadAnimals().
 * Returns: HTMLElement, noch nicht in ein Gehege eingehaengt.
 *
 * Test:
 *   TC-J03: Given ein Tier-Objekt mit species="Lion", when
 *     `createSprite(animal)` aufgerufen wird, then enthaelt das erzeugte
 *     Element das Loewen-Emoji und ein data-animal-id-Attribut mit der
 *     richtigen ID.
 *   TC-J04: Given ein Tier-Objekt mit einer unbekannten species (z.B.
 *     "Elephant", falls spaeter ergaenzt), when `createSprite(animal)`
 *     aufgerufen wird, then wird das Standard-Emoji verwendet statt eines
 *     Fehlers.
 */
function createSprite(animal) {
  const sprite = document.createElement("div");
  sprite.className = "animal-sprite";
  sprite.dataset.animalId = String(animal.id);
  sprite.setAttribute("role", "button");
  sprite.setAttribute("tabindex", "0");
  sprite.setAttribute("aria-label", `${animal.name} (${animal.species})`);

  const emoji = document.createElement("span");
  emoji.textContent = speciesEmoji(animal.species);
  sprite.appendChild(emoji);

  const nameLabel = document.createElement("span");
  nameLabel.className = "animal-sprite-name";
  nameLabel.textContent = animal.name;
  sprite.appendChild(nameLabel);

  return sprite;
}

/**
 * Fuellt das Popup mit den Daten eines Tieres und zeigt es an.
 *
 * Args: animal (Object)
 * Returns: undefined
 *
 * Test:
 *   TC-J05: Given ein Tier mit id=3, when `openAnimalPopup(animal)`
 *     aufgerufen wird, then zeigt das Fuetterungsformular im Popup als
 *     action-Attribut die URL "/animals/3/feed".
 *   TC-J06: Given das Popup ist aktuell versteckt (Klasse "hidden"), when
 *     `openAnimalPopup(animal)` aufgerufen wird, then wird die Klasse
 *     "hidden" entfernt.
 */
function openAnimalPopup(animal) {
  document.getElementById("animal-popup-name").textContent = animal.name;
  document.getElementById("animal-popup-species").textContent = animal.species;
  document.getElementById("animal-popup-age").textContent = animal.age;
  document.getElementById("animal-popup-health").textContent = animal.health;
  document.getElementById("animal-popup-hunger").textContent = animal.hunger;
  document.getElementById("animal-popup-energy").textContent = animal.energy;

  const feedForm = document.getElementById("animal-popup-feed-form");
  feedForm.action = `/animals/${animal.id}/feed`;

  document.getElementById("animal-popup").classList.remove("hidden");
}

/** Blendet das Popup wieder aus. Args/Returns: keine.
 *
 * Test:
 *   TC-J07: Given das Popup ist gerade sichtbar, when `closeAnimalPopup()`
 *     aufgerufen wird, then bekommt es wieder die Klasse "hidden".
 *   TC-J08: Given das Popup ist bereits versteckt, when
 *     `closeAnimalPopup()` trotzdem aufgerufen wird, then bleibt es
 *     versteckt, ohne einen Fehler zu werfen (idempotent).
 */
function closeAnimalPopup() {
  document.getElementById("animal-popup").classList.add("hidden");
}

/**
 * Initialisiert das Spielbrett: erzeugt alle Tier-Sprites in ihren
 * Gehege-Boxen und verdrahtet Klick-/Tastatur-Interaktion sowie das
 * Schliessen des Popups. Wird einmal beim Laden der Seite aufgerufen.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-J09: Given 3 Tiere mit enclosure_id=1 und eine Gehege-Box mit
 *     data-enclosure-id="1" existiert im DOM, when `initGameBoard()`
 *     aufgerufen wird, then enthaelt diese Box danach genau 3
 *     ".animal-sprite"-Elemente.
 *   TC-J10: Given ein Tier referenziert eine enclosure_id, fuer die keine
 *     Gehege-Box im DOM existiert, when `initGameBoard()` aufgerufen wird,
 *     then wird dieses Tier uebersprungen, ohne dass die Initialisierung
 *     der uebrigen Tiere abbricht.
 */
function initGameBoard() {
  const animals = loadAnimals();

  animals.forEach((animal) => {
    const pen = document.querySelector(
      `.enclosure-pen[data-enclosure-id="${animal.enclosure_id}"]`
    );
    if (!pen) {
      return;
    }

    const sprite = createSprite(animal);
    pen.appendChild(sprite);

    const openThisAnimal = () => openAnimalPopup(animal);
    sprite.addEventListener("click", openThisAnimal);
    sprite.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openThisAnimal();
      }
    });
  });

  const closeButton = document.getElementById("animal-popup-close");
  if (closeButton) {
    closeButton.addEventListener("click", closeAnimalPopup);
  }

  const popupOverlay = document.getElementById("animal-popup");
  if (popupOverlay) {
    popupOverlay.addEventListener("click", (event) => {
      if (event.target === popupOverlay) {
        closeAnimalPopup();
      }
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeAnimalPopup();
    }
  });

  // animation.js registriert sich hier, falls es vor game.js geladen wurde
  // oder umgekehrt - beide Reihenfolgen sollen funktionieren.
  if (window.ZooAnimation && typeof window.ZooAnimation.start === "function") {
    window.ZooAnimation.start();
  }
}

document.addEventListener("DOMContentLoaded", initGameBoard);
