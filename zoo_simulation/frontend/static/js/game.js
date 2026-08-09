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
 *
 * Zoo-Spiel-Feature-Ausbau (2026-08-09) ergaenzt mit Unterstuetzung von
 * Kaiss Saleh (Datenbank-Schwerpunkt): Stimmungs-Icons auf den Sprites,
 * "Alle hungrigen fuettern" (global + pro Gehege) und das "Tier
 * adoptieren"-Modal mit Lebensraum-/Fortschritts-Filterung, Zufallsname-
 * Button und Spotlight-Hervorhebung. Die HUD-Wohlfuehl-Score-Berechnung
 * lebt inzwischen in static/js/zoo_stats.js (sitewide, nicht nur hier).
 *
 * Ergaenzt mit Unterstuetzung von Alessio Bellamacina (Frontend-
 * Schwerpunkt), 2026-08-09: `openAnimalPopup()` setzt jetzt zusaetzlich
 * die action-URL des Behandlungsformulars (verdrahtet
 * ZooController.treat_animal(), siehe planning_backend_darnell.md
 * Abschnitt 2.10).
 *
 * Weiter ergaenzt mit Unterstuetzung von Alessio Bellamacina (Frontend-
 * Schwerpunkt), 2026-08-09 (siehe planning_backend_darnell.md Abschnitt
 * 2.11): Fuetterungs-/Behandlungsformulare verlangen jetzt zusaetzlich
 * eine Tierpfleger-/Tierarzt-Auswahl; `lastZookeeperId` merkt sich die
 * zuletzt gewaehlte (oder die erste eingestellte) Tierpfleger-ID fuer
 * die "Alle hungrigen fuettern"-Schnellaktionen, die nicht pro Tier
 * danach fragen. Das Popup hat zudem einen "Entfernen"-Knopf
 * (verdrahtet ZooController.remove_animal()).
 */

const SPECIES_EMOJI = {
  Lion: "\u{1F981}", // 🦁
  Giraffe: "\u{1F992}", // 🦒
  Penguin: "\u{1F427}", // 🐧
};
const DEFAULT_EMOJI = "\u{1F43E}"; // 🐾 fuer unbekannte/zukuenftige Spezies

// Welche Gehege-Typen fuer welche Art als Lebensraum in Frage kommen -
// steuert nur die Vorauswahl/Filterung im "Tier adoptieren"-Formular
// (rein praesentations-seitige UX-Hilfe). Bewusst KEINE serverseitige
// Regel: weder das Domain-Modell noch controller_stub.py kennen ein
// Konzept von "passendem Lebensraum" - siehe dortige Kapazitaetspruefung,
// die unabhaengig davon weiterhin greift.
const SPECIES_HABITATS = {
  Lion: ["Savanna", "Grassland"],
  Giraffe: ["Savanna", "Grassland"],
  Penguin: ["Polar", "Aquatic"],
};

// Ab wie vielen Besuchern eine Art im Adopt-Formular waehlbar ist - reines
// Tycoon-Fortschrittsgefuehl, ebenfalls praesentations-seitig only (siehe
// SPECIES_HABITATS-Kommentar). Lion/Giraffe von Anfang an frei, Penguin
// erst als "Belohnung" ab etwas Zoo-Wachstum.
const SPECIES_UNLOCK_VISITORS = {
  Lion: 0,
  Giraffe: 0,
  Penguin: 15,
};

// Themen-Namenspool fuer den Zufallsname-Button im Adopt-Formular.
const SPECIES_NAME_POOL = {
  Lion: ["Simba", "Mufasa", "Nala", "Kimba", "Elsa", "Kiara"],
  Giraffe: ["Melman", "Gina", "Geraldine", "Twiga", "Marius"],
  Penguin: ["Pingu", "Skipper", "Kowalski", "Rico", "Private"],
};

/**
 * Liefert einen zufaelligen, thematisch passenden Namen fuer eine Art.
 *
 * Args: species (string). Returns: string.
 *
 * Test:
 *   TC-J26: Given species="Penguin", when `randomNameForSpecies("Penguin")`
 *     wiederholt aufgerufen wird, then liegt das Ergebnis immer in
 *     SPECIES_NAME_POOL.Penguin.
 *   TC-J27: Given eine unbekannte species, when
 *     `randomNameForSpecies(species)` aufgerufen wird, then wird trotzdem
 *     ein nicht-leerer String zurueckgegeben (Fallback-Pool), keine
 *     Exception.
 */
function randomNameForSpecies(species) {
  const pool = SPECIES_NAME_POOL[species] || ["Neuling"];
  return pool[Math.floor(Math.random() * pool.length)];
}

// Schwellenwerte fuer die Stimmungs-Icons. SICK_HEALTH_THRESHOLD spiegelt
// exakt Veterinarian._SICK_THRESHOLD aus domain/employees/veterinarian.py
// (dort examine_animal() -> "sick" wenn health < 40), damit "krank
// wirkend" im Spiel mit der Backend-Diagnose uebereinstimmt.
const SICK_HEALTH_THRESHOLD = 40;
const HUNGRY_THRESHOLD = 70;
const SLEEPING_ENERGY_THRESHOLD = 20;
const MOOD_ICONS = {
  sick: "\u{1F912}", // 🤒
  hungry: "\u{1F924}", // 🤤
  sleeping: "\u{1F4A4}", // 💤
};

/**
 * Liefert das Sprite-Emoji fuer eine Tierart.
 *
 * Args: species (string). Returns: string (Emoji).
 *
 * Test:
 *   TC-J33: Given species="Giraffe", when `speciesEmoji("Giraffe")`
 *     aufgerufen wird, then wird das Giraffen-Emoji zurueckgegeben.
 *   TC-J34: Given eine unbekannte species (z.B. "Elephant"), when
 *     `speciesEmoji("Elephant")` aufgerufen wird, then wird
 *     DEFAULT_EMOJI zurueckgegeben statt eines Fehlers.
 */
function speciesEmoji(species) {
  return SPECIES_EMOJI[species] || DEFAULT_EMOJI;
}

/**
 * Bestimmt die Stimmung eines Tieres aus seinen Stats, nach Dringlichkeit
 * priorisiert (krank vor hungrig vor schlaefrig), da ein Sprite nur ein
 * Icon gleichzeitig zeigt.
 *
 * Args: animal (Object) - mit health/hunger/energy.
 * Returns: string | null - einer von "sick"/"hungry"/"sleeping", oder null
 *   wenn keine Schwelle erreicht ist (Tier wirkt zufrieden).
 *
 * Test:
 *   TC-J11: Given ein Tier mit health=20 und hunger=90, when
 *     computeMood(animal) aufgerufen wird, then wird "sick" zurueckgegeben
 *     (Gesundheit hat Vorrang vor Hunger).
 *   TC-J12: Given ein Tier mit health=100, hunger=10, energy=100, when
 *     computeMood(animal) aufgerufen wird, then wird null zurueckgegeben.
 */
function computeMood(animal) {
  if (animal.health < SICK_HEALTH_THRESHOLD) {
    return "sick";
  }
  if (animal.hunger >= HUNGRY_THRESHOLD) {
    return "hungry";
  }
  if (animal.energy <= SLEEPING_ENERGY_THRESHOLD) {
    return "sleeping";
  }
  return null;
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
 * Liest die eingebettete Zookeeper-Liste (`#zookeepers-data`, siehe
 * templates/animals_game.html) fuer die "Alle hungrigen
 * fuettern"-Schnellaktion. Ergaenzt mit Unterstuetzung von Alessio
 * Bellamacina (Frontend-Schwerpunkt), 2026-08-09 - siehe
 * planning_backend_darnell.md Abschnitt 2.11.
 *
 * Args/Returns: Array (leer, falls das Element fehlt/kein gueltiges
 * JSON enthaelt).
 *
 * Test:
 *   TC-J14: Given das `#zookeepers-data`-Element enthaelt gueltiges
 *     JSON mit 2 Tierpflegern, when `loadZookeepers()` aufgerufen
 *     wird, then liefert es ein Array mit 2 Eintraegen.
 *   TC-J15: Given das `#zookeepers-data`-Element fehlt, when
 *     `loadZookeepers()` aufgerufen wird, then liefert es ein leeres
 *     Array statt einer Exception.
 */
function loadZookeepers() {
  const dataElement = document.getElementById("zookeepers-data");
  if (!dataElement) {
    return [];
  }
  try {
    return JSON.parse(dataElement.textContent);
  } catch (error) {
    console.error("zoo-game: zookeepers-data konnte nicht gelesen werden", error);
    return [];
  }
}

// Von initGameBoard() gesetzt: id des zuletzt im Popup gewaehlten
// Tierpflegers, oder des ersten eingestellten, falls noch keiner gewaehlt
// wurde. "Alle hungrigen fuettern"/"Gehege fuettern" fragen bewusst nicht
// pro Tier nach einem Tierpfleger (siehe feedAnimals()) - dieser Wert
// entscheidet, wer dort eingetragen wird.
let lastZookeeperId = null;

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
 *   TC-J13: Given ein Tier-Objekt mit energy=10 (unter
 *     SLEEPING_ENERGY_THRESHOLD), when `createSprite(animal)` aufgerufen
 *     wird, then hat das erzeugte Element `dataset.mood === "sleeping"` und
 *     zeigt das Schlaf-Icon.
 */
function createSprite(animal) {
  const sprite = document.createElement("div");
  sprite.className = "animal-sprite";
  sprite.dataset.animalId = String(animal.id);
  sprite.setAttribute("role", "button");
  sprite.setAttribute("tabindex", "0");
  sprite.setAttribute("aria-label", `${animal.name} (${animal.species})`);

  const emoji = document.createElement("span");
  emoji.className = "animal-sprite-emoji";
  emoji.textContent = speciesEmoji(animal.species);
  sprite.appendChild(emoji);

  const mood = computeMood(animal);
  if (mood) {
    sprite.dataset.mood = mood;
    const moodIcon = document.createElement("span");
    moodIcon.className = "animal-sprite-mood";
    moodIcon.textContent = MOOD_ICONS[mood];
    sprite.appendChild(moodIcon);
  }

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
 *   TC-J13 (ergaenzt mit Unterstuetzung von Alessio Bellamacina,
 *     Frontend-Schwerpunkt, 2026-08-09): Given ein Tier mit id=3, when
 *     `openAnimalPopup(animal)` aufgerufen wird, then zeigt das
 *     Behandlungsformular im Popup als action-Attribut die URL
 *     "/animals/3/treat".
 */
function openAnimalPopup(animal) {
  document.getElementById("animal-popup-name").textContent = animal.name;
  document.getElementById("animal-popup-species").textContent = animal.species;
  document.getElementById("animal-popup-age").textContent = animal.age;
  document.getElementById("animal-popup-health").textContent = animal.health;
  document.getElementById("animal-popup-hunger").textContent = animal.hunger;
  document.getElementById("animal-popup-energy").textContent = animal.energy;

  const feedForm = document.getElementById("animal-popup-feed-form");
  if (feedForm) {
    feedForm.action = `/animals/${animal.id}/feed`;
    const zookeeperSelect = document.getElementById("animal-popup-zookeeper-select");
    if (zookeeperSelect && lastZookeeperId !== null) {
      zookeeperSelect.value = String(lastZookeeperId);
    }
  }

  const treatForm = document.getElementById("animal-popup-treat-form");
  if (treatForm) {
    treatForm.action = `/animals/${animal.id}/treat`;
  }

  const removeForm = document.getElementById("animal-popup-remove-form");
  if (removeForm) {
    removeForm.action = `/animals/${animal.id}/remove`;
  }

  document.getElementById("animal-popup").classList.remove("hidden");
  if (window.ZooSound) {
    window.ZooSound.play("click");
  }
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
 * Oeffnet/schliesst das "Tier adoptieren"-Modal - gleiches Muster wie
 * `openAnimalPopup()`/`closeAnimalPopup()`.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-J18: Given das Add-Animal-Modal ist versteckt, when
 *     `openAddAnimalModal()` aufgerufen wird, then verliert es die Klasse
 *     "hidden".
 *   TC-J19: Given das Add-Animal-Modal ist sichtbar, when
 *     `closeAddAnimalModal()` aufgerufen wird, then bekommt es wieder die
 *     Klasse "hidden" (auch wenn bereits versteckt, keine Exception).
 */
function openAddAnimalModal() {
  const modal = document.getElementById("add-animal-modal");
  if (!modal) {
    return;
  }
  modal.classList.remove("hidden");
  refreshAddAnimalForm();
  if (window.ZooSound) {
    window.ZooSound.play("click");
  }
}

/** Blendet das "Tier adoptieren"-Modal wieder aus. Args/Returns: keine.
 *
 * Test:
 *   TC-J35: Given das Modal ist gerade sichtbar, when
 *     `closeAddAnimalModal()` aufgerufen wird, then bekommt es wieder die
 *     Klasse "hidden".
 *   TC-J36: Given das Modal existiert nicht im DOM (z.B. Fehlerzustand),
 *     when `closeAddAnimalModal()` aufgerufen wird, then passiert nichts,
 *     keine Exception.
 */
function closeAddAnimalModal() {
  const modal = document.getElementById("add-animal-modal");
  if (modal) {
    modal.classList.add("hidden");
  }
}

/**
 * Prueft, ob eine Art zu einem Gehege-Typ passt (siehe SPECIES_HABITATS).
 * Unbekannte Arten gelten als ueberall passend, damit das Formular nicht
 * kaputt geht, sobald spaeter eine neue Spezies ergaenzt wird, ohne dass
 * SPECIES_HABITATS gepflegt wurde.
 *
 * Args: species (string), enclosureType (string). Returns: boolean.
 *
 * Test:
 *   TC-J22: Given species="Penguin" und enclosureType="Polar", when
 *     `isHabitatCompatible(species, enclosureType)` aufgerufen wird, then
 *     wird true zurueckgegeben.
 *   TC-J23: Given species="Lion" und enclosureType="Polar", when
 *     `isHabitatCompatible(species, enclosureType)` aufgerufen wird, then
 *     wird false zurueckgegeben.
 */
function isHabitatCompatible(species, enclosureType) {
  const habitats = SPECIES_HABITATS[species];
  if (!habitats) {
    return true;
  }
  return habitats.includes(enclosureType);
}

/**
 * Sperrt Arten im "Tier adoptieren"-Formular, die die aktuelle
 * Besucherzahl noch nicht erreicht hat (siehe SPECIES_UNLOCK_VISITORS),
 * beschriftet sie mit dem Freischalt-Schwellenwert und wechselt die
 * Auswahl auf die erste noch freigeschaltete Art, falls die bisherige
 * Auswahl dadurch gesperrt wurde.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-J28: Given current_visitors=12 (unter der Penguin-Schwelle 15) und
 *     "Penguin" ist ausgewaehlt, when
 *     `updateSpeciesOptionsForProgress()` aufgerufen wird, then wird die
 *     Penguin-Option deaktiviert und die Auswahl springt auf "Lion" um.
 *   TC-J29: Given das Besucher-HUD-Element `[data-current-visitors]`
 *     existiert nicht auf der Seite, when
 *     `updateSpeciesOptionsForProgress()` aufgerufen wird, then gelten
 *     alle Arten als freigeschaltet (currentVisitors=0 als sicherer
 *     Default fuehrt nur bei Schwelle 0 zur Freischaltung - siehe
 *     SPECIES_UNLOCK_VISITORS.Lion/Giraffe), keine Exception.
 */
function updateSpeciesOptionsForProgress() {
  const speciesSelect = document.getElementById("add-animal-species");
  if (!speciesSelect) {
    return;
  }
  const visitorsElement = document.querySelector("[data-current-visitors]");
  const currentVisitors = visitorsElement ? Number(visitorsElement.dataset.currentVisitors) : 0;

  let firstUnlocked = null;
  Array.from(speciesSelect.options).forEach((option) => {
    const requiredVisitors = SPECIES_UNLOCK_VISITORS[option.value] || 0;
    const locked = currentVisitors < requiredVisitors;
    option.disabled = locked;

    const baseLabel = option.dataset.label || option.value;
    option.textContent = locked ? `${baseLabel} – 🔒 ab ${requiredVisitors} Besuchern` : baseLabel;

    if (!locked && !firstUnlocked) {
      firstUnlocked = option;
    }
  });

  const selected = speciesSelect.options[speciesSelect.selectedIndex];
  if (selected && selected.disabled && firstUnlocked) {
    speciesSelect.value = firstUnlocked.value;
  }
}

/**
 * Filtert die Gehege-Optionen im "Tier adoptieren"-Formular nach der
 * aktuell gewaehlten Art: Gehege mit unpassendem Lebensraum werden
 * deaktiviert und beschriftet, volle Gehege bleiben (zusaetzlich zur
 * bereits serverseitig gesetzten disabled-Markierung) deaktiviert. Wechselt
 * die aktuelle Auswahl auf die erste noch waehlbare Option, falls die
 * bisher gewaehlte durch den Artwechsel deaktiviert wurde.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-J24: Given "Penguin" ist ausgewaehlt und ein Gehege vom Typ
 *     "Savanna" war zuvor ausgewaehlt, when
 *     `updateEnclosureOptionsForSpecies()` aufgerufen wird, then wird
 *     dieses Gehege deaktiviert und die Auswahl springt auf ein
 *     passendes (z.B. "Polar") Gehege um.
 *   TC-J25: Given die Formularelemente existieren nicht auf der Seite
 *     (z.B. Fehlerzustand ohne Gehege), when
 *     `updateEnclosureOptionsForSpecies()` aufgerufen wird, then passiert
 *     nichts, keine Exception.
 */
function updateEnclosureOptionsForSpecies() {
  const speciesSelect = document.getElementById("add-animal-species");
  const enclosureSelect = document.getElementById("add-animal-enclosure");
  if (!speciesSelect || !enclosureSelect) {
    return;
  }

  const species = speciesSelect.value;
  let firstEnabledOption = null;

  Array.from(enclosureSelect.options).forEach((option) => {
    const isFull = option.dataset.full === "true";
    const matchesHabitat = isHabitatCompatible(species, option.dataset.enclosureType);
    option.disabled = isFull || !matchesHabitat;

    let label = option.dataset.label || option.textContent.trim();
    if (isFull) {
      label += " – voll";
    } else if (!matchesHabitat) {
      label += " – falscher Lebensraum";
    }
    option.textContent = label;

    if (!option.disabled && !firstEnabledOption) {
      firstEnabledOption = option;
    }
  });

  const selected = enclosureSelect.options[enclosureSelect.selectedIndex];
  if (selected && selected.disabled && firstEnabledOption) {
    enclosureSelect.value = firstEnabledOption.value;
  }
}

/**
 * Aktualisiert beide Filter des Adopt-Formulars zusammen (Reihenfolge
 * wichtig: Fortschritts-Sperre zuerst, damit ein dadurch ausgeloester
 * Artwechsel korrekt in die anschliessende Lebensraum-Filterung
 * einfliesst). Wird beim Oeffnen des Modals und bei jedem Artwechsel
 * aufgerufen.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-J37: Given "Penguin" ist gesperrt (Besucherzahl unter der
 *     Schwelle) und war ausgewaehlt, when `refreshAddAnimalForm()`
 *     aufgerufen wird, then springt die Art-Auswahl zuerst auf eine
 *     freigeschaltete Art um, und die Gehege-Filterung wendet sich
 *     danach korrekt auf diese neue Art an (nicht mehr auf "Penguin").
 *   TC-J38: Given beide Formularelemente (#add-animal-species,
 *     #add-animal-enclosure) fehlen auf der Seite, when
 *     `refreshAddAnimalForm()` aufgerufen wird, then passiert nichts,
 *     keine Exception (beide Teilaufrufe brechen fruehzeitig ab).
 */
function refreshAddAnimalForm() {
  updateSpeciesOptionsForProgress();
  updateEnclosureOptionsForSpecies();
}

/**
 * Fuehrt fuer jedes uebergebene Tier einen POST an die bestehende
 * `/animals/<id>/feed`-Route aus (dieselbe Route wie das einzelne
 * Fuetterungsformular, kein neuer Endpoint) und laedt die Seite danach neu,
 * damit die aktualisierten Werte sichtbar werden. Gemeinsame Basis fuer
 * `feedAllHungry()` (globaler Button) und `feedHungryInEnclosure()`
 * (Pro-Gehege-Button).
 *
 * Args: animalsToFeed (Array). Returns: Promise<void>.
 *
 * Nutzt food_id=1 ("Heu", die guenstigste Sorte in controller_stub.py
 * `_FOOD_CATALOG`) fuer alle Schnellaktionen - eine bewusste, einfache
 * Wahl, damit Massenfuetterungen nicht pro Tier nach Futterart fragen
 * muessen; die Einzelfuetterung (Popup/Tabelle) bietet die volle Auswahl.
 *
 * Test:
 *   TC-J20: Given 2 Tiere werden uebergeben, when `feedAnimals(animals)`
 *     aufgerufen wird, then werden genau 2 POST-Requests an
 *     `/animals/<id>/feed` gesendet, danach ein Reload ausgeloest.
 *   TC-J21: Given ein leeres Array wird uebergeben, when
 *     `feedAnimals([])` aufgerufen wird, then wird kein Request gesendet
 *     und die Seite nicht neu geladen.
 *   TC-J22 (ergaenzt 2026-08-09, siehe planning_backend_darnell.md
 *     Abschnitt 2.11): Given `lastZookeeperId` ist `null` (kein
 *     Tierpfleger eingestellt), when `feedAnimals(animals)` mit
 *     nicht-leerem Array aufgerufen wird, then wird kein Request
 *     gesendet.
 */
async function feedAnimals(animalsToFeed) {
  if (!animalsToFeed.length || lastZookeeperId === null) {
    return;
  }
  await Promise.all(
    animalsToFeed.map((animal) =>
      fetch(`/animals/${animal.id}/feed`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `food_id=1&zookeeper_id=${lastZookeeperId}`,
      })
    )
  );
  window.location.reload();
}

/**
 * Fuettert alle Tiere mit Hunger >= HUNGRY_THRESHOLD, gehegeuebergreifend
 * (globaler "Alle hungrigen fuettern"-Button).
 *
 * Args: animals (Array). Returns: Promise<void>.
 *
 * Test: siehe feedAnimals(); zusaetzlich TC-J21b: Given kein Tier erreicht
 *   HUNGRY_THRESHOLD, when `feedAllHungry(animals)` aufgerufen wird, then
 *   wird `feedAnimals([])` effektiv aufgerufen (kein Request).
 */
function feedAllHungry(animals) {
  return feedAnimals(animals.filter((animal) => animal.hunger >= HUNGRY_THRESHOLD));
}

/**
 * Fuettert alle hungrigen Tiere innerhalb genau eines Geheges (Pro-Gehege-
 * "🍽️"-Button auf jeder Gehege-Box).
 *
 * Args: animals (Array), enclosureId (number). Returns: Promise<void>.
 *
 * Test:
 *   TC-J30: Given 2 hungrige Tiere in Gehege 1 und 1 hungriges Tier in
 *     Gehege 2, when `feedHungryInEnclosure(animals, 1)` aufgerufen wird,
 *     then werden nur die 2 Tiere aus Gehege 1 gefuettert.
 */
function feedHungryInEnclosure(animals, enclosureId) {
  return feedAnimals(
    animals.filter(
      (animal) => animal.hunger >= HUNGRY_THRESHOLD && animal.enclosure_id === enclosureId
    )
  );
}

/**
 * Hebt ein frisch adoptiertes Tier kurz optisch hervor (siehe game.css,
 * `.newly-adopted`), falls die Seite ueber `?highlight=<id>` (siehe
 * zoo_view.py `handle_add_animal_form()`) mit einer passenden ID geladen
 * wurde. Liest die ID aus `.zoo-board`s `data-highlight-id`-Attribut, das
 * `zoo_view.py`/`animals_game.html` serverseitig setzt.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-J31: Given `.zoo-board` hat `data-highlight-id="3"` und ein Sprite
 *     mit `data-animal-id="3"` existiert, when `applyHighlight()`
 *     aufgerufen wird, then bekommt genau dieses Sprite die Klasse
 *     "newly-adopted".
 *   TC-J32: Given `data-highlight-id` ist leer (Normalfall ohne gerade
 *     erfolgten Adopt-Vorgang), when `applyHighlight()` aufgerufen wird,
 *     then bekommt kein Sprite die Klasse, keine Exception.
 */
function applyHighlight() {
  const board = document.querySelector(".zoo-board");
  const highlightId = board ? board.dataset.highlightId : "";
  if (!highlightId) {
    return;
  }
  const sprite = document.querySelector(`.animal-sprite[data-animal-id="${highlightId}"]`);
  if (sprite) {
    sprite.classList.add("newly-adopted");
  }
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

  applyHighlight();

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
      closeAddAnimalModal();
    }
  });

  const openAddButton = document.getElementById("open-add-animal-modal");
  if (openAddButton) {
    openAddButton.addEventListener("click", openAddAnimalModal);
  }
  const addModalClose = document.getElementById("add-animal-modal-close");
  if (addModalClose) {
    addModalClose.addEventListener("click", closeAddAnimalModal);
  }
  const addModalOverlay = document.getElementById("add-animal-modal");
  if (addModalOverlay) {
    addModalOverlay.addEventListener("click", (event) => {
      if (event.target === addModalOverlay) {
        closeAddAnimalModal();
      }
    });
  }
  const addAnimalSpeciesSelect = document.getElementById("add-animal-species");
  if (addAnimalSpeciesSelect) {
    addAnimalSpeciesSelect.addEventListener("change", refreshAddAnimalForm);
  }
  refreshAddAnimalForm();

  const randomNameButton = document.getElementById("add-animal-random-name");
  if (randomNameButton) {
    randomNameButton.addEventListener("click", () => {
      const nameInput = document.getElementById("add-animal-name");
      if (nameInput && addAnimalSpeciesSelect) {
        nameInput.value = randomNameForSpecies(addAnimalSpeciesSelect.value);
      }
      if (window.ZooSound) {
        window.ZooSound.play("click");
      }
    });
  }

  const zookeepers = loadZookeepers();
  lastZookeeperId = zookeepers.length ? zookeepers[0].id : null;
  const zookeeperSelect = document.getElementById("animal-popup-zookeeper-select");
  if (zookeeperSelect) {
    zookeeperSelect.addEventListener("change", () => {
      lastZookeeperId = Number(zookeeperSelect.value);
    });
  }

  const feedHungryButton = document.getElementById("feed-hungry-button");
  if (feedHungryButton) {
    feedHungryButton.addEventListener("click", () => feedAllHungry(animals));
  }

  document.querySelectorAll(".enclosure-feed-button").forEach((button) => {
    button.addEventListener("click", () => {
      feedHungryInEnclosure(animals, Number(button.dataset.enclosureId));
    });
  });

  // animation.js registriert sich hier, falls es vor game.js geladen wurde
  // oder umgekehrt - beide Reihenfolgen sollen funktionieren.
  if (window.ZooAnimation && typeof window.ZooAnimation.start === "function") {
    window.ZooAnimation.start();
  }
}

document.addEventListener("DOMContentLoaded", initGameBoard);
