"use strict";

/**
 * animal_list.js - Client-seitige Such-/Sortierleiste fuer die
 * Tier-Tabellenansicht (templates/animals.html, ?view=list). Arbeitet nur
 * auf bereits vom Server gerenderten Tabellenzeilen (data-*-Attribute) -
 * kein Server-Request, keine neue ZooController-Methode.
 *
 * Ergaenzt von Kaiss Saleh (Datenbank-Schwerpunkt) im Rahmen des
 * Zoo-Spiel-Feature-Ausbaus, gemeinsam mit Alessio Bellamacina
 * (Frontend-Schwerpunkt).
 */

const SORTERS = {
  "name-asc": (a, b) => a.dataset.name.localeCompare(b.dataset.name),
  "hunger-desc": (a, b) => Number(b.dataset.hunger) - Number(a.dataset.hunger),
  "health-asc": (a, b) => Number(a.dataset.health) - Number(b.dataset.health),
  "energy-asc": (a, b) => Number(a.dataset.energy) - Number(b.dataset.energy),
};

/**
 * Filtert Tabellenzeilen nach Name/Spezies (Teilstring, gross-/klein-
 * schreibungsunabhaengig) und sortiert die Zeilen nach der gewaehlten
 * Option neu ins DOM ein.
 *
 * Args/Returns: keine (arbeitet direkt auf dem DOM).
 *
 * Test:
 *   TC-L01: Given eine Zeile mit data-name="Simba" und der Suchbegriff
 *     "sim", when `applyFilterAndSort()` aufgerufen wird, then bleibt die
 *     Zeile sichtbar (Grossschreibung wird ignoriert).
 *   TC-L02: Given kein Tier passt zum Suchbegriff, when
 *     `applyFilterAndSort()` aufgerufen wird, then werden alle Zeilen
 *     versteckt und der Hinweistext (#animal-list-empty-hint) sichtbar.
 */
function applyFilterAndSort() {
  const searchInput = document.getElementById("animal-search");
  const sortSelect = document.getElementById("animal-sort");
  const tableBody = document.getElementById("animal-table-body");
  const emptyHint = document.getElementById("animal-list-empty-hint");
  if (!searchInput || !sortSelect || !tableBody) {
    return;
  }

  const query = searchInput.value.trim().toLowerCase();
  const rows = Array.from(tableBody.querySelectorAll("tr"));

  let visibleCount = 0;
  rows.forEach((row) => {
    const matches =
      !query ||
      row.dataset.name.toLowerCase().includes(query) ||
      row.dataset.species.toLowerCase().includes(query);
    row.classList.toggle("hidden", !matches);
    if (matches) {
      visibleCount += 1;
    }
  });

  const sorter = SORTERS[sortSelect.value] || SORTERS["name-asc"];
  rows.sort(sorter).forEach((row) => tableBody.appendChild(row));

  if (emptyHint) {
    emptyHint.classList.toggle("hidden", visibleCount > 0);
  }
}

/**
 * Verdrahtet Such-Input und Sortier-Select mit `applyFilterAndSort()`.
 *
 * Args/Returns: keine.
 *
 * Test:
 *   TC-L03: Given #animal-search/#animal-sort existieren im DOM, when
 *     `initAnimalList()` aufgerufen wird, then loest ein "input"-Event auf
 *     dem Suchfeld eine Neufilterung aus.
 *   TC-L04: Given die Steuerelemente fehlen (z.B. keine Tiere vorhanden,
 *     Tabelle wird gar nicht gerendert), when `initAnimalList()`
 *     aufgerufen wird, then passiert nichts, keine Exception.
 */
function initAnimalList() {
  const searchInput = document.getElementById("animal-search");
  const sortSelect = document.getElementById("animal-sort");
  if (!searchInput || !sortSelect) {
    return;
  }
  searchInput.addEventListener("input", applyFilterAndSort);
  sortSelect.addEventListener("change", applyFilterAndSort);
}

document.addEventListener("DOMContentLoaded", initAnimalList);
