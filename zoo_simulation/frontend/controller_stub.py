"""MockZooController: temporary stand-in for the real ZooController.

Schwerpunkt: Frontend (Presentation Layer) - Alessio Bellamacina
author: Alessio Bellamacina

Hinweis: `zoo_simulation/controller/zoo_controller.py` ist zum Zeitpunkt
dieses Commits noch nicht implementiert (Backend-Schwerpunkt, Darnell
Beganovic). Damit die Flask-Oberflaeche (`zoo_view.py`) trotzdem entwickelt
und manuell getestet werden kann, stellt dieses Modul einen Mock/Stub bereit,
der exakt die gleiche Schnittstelle wie der zukuenftige ZooController
implementiert:

    show_status() / add_animal(data) / feed_animal(animal_id, food_id) /
    sell_ticket(price) / run_simulation_step() / create_report(format)

Vertrag (agreed 2026-08-06, siehe planning_frontend_alessio.md Abschnitt 2.1):
Jede Methode gibt ein einheitliches Result-Dict zurueck, nie ``None`` und nie
eine rohe Exception an den Aufrufer:

    {"success": bool, "message": str, "data": Any}

Sobald der echte ZooController fertig ist, wird in `zoo_view.py` nur der
Import ausgetauscht (`from .controller_stub import MockZooController as
ZooController` -> `from zoo_simulation.controller.zoo_controller import
ZooController`); an den Routen selbst aendert sich nichts, da beide Seiten
denselben Vertrag erfuellen.

Die Daten liegen ausschliesslich im Prozessspeicher (Python-Listen/dicts,
zurueckgegeben als `pandas.DataFrame` dort, wo der spaetere echte Controller
ebenfalls DataFrames liefert, siehe `AnimalRepository.get_as_dataframe()` im
Klassendiagramm) und werden bei jedem Prozessneustart zurueckgesetzt. Es
findet keine Persistenz statt - das ist bewusst so, da Datenbankanbindung
nicht zum Frontend-Schwerpunkt gehoert.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pandas as pd


class MockZooController:
    """Fake ZooController with in-memory data, matching the real interface.

    Wird ausschliesslich fuer die lokale Entwicklung/manuelles Testen der
    Flask-Oberflaeche verwendet, solange der echte `ZooController`
    (Backend-Schwerpunkt) noch nicht existiert. Haelt keine Verbindung zu
    Domain-Modell, Services oder Repositories - das genau nachzubilden ist
    nicht das Ziel dieses Stubs, sondern nur, dass er sich wie der echte
    Controller "anfuehlt" (gleiche Methodennamen, gleiche Rueckgabeform).

    Attributes:
        _animals (list[dict]): Fake-Tierbestand.
        _enclosures (list[dict]): Fake-Gehege.
        _zoo (dict): Fake-Zoo-Stammdaten (Name, Standort, Besucherzahlen).
        _transactions (list[dict]): Fake-Finanztransaktionen.
        _simulation_time (int): Zaehler fuer bereits ausgefuehrte Simulationsschritte.

    Test:
        TC-M01: Given eine frisch erstellte `MockZooController`-Instanz, when
            kein Aufruf stattgefunden hat, then enthaelt `_animals` genau die
            in `__init__` definierten Beispieltiere (deterministischer
            Startzustand fuer reproduzierbare manuelle Tests).
        TC-M02: Given zwei unabhaengige `MockZooController`-Instanzen, when
            eine davon veraendert wird (z.B. `feed_animal`), then bleibt die
            andere Instanz unveraendert (kein geteilter Modulzustand).
    """

    def __init__(self) -> None:
        """Initialisiert den Stub mit deterministischen Beispieldaten.

        Args:
            (keine)

        Returns:
            None

        Test:
            TC-M03: Given der Konstruktor wird aufgerufen, when keine
                Argumente uebergeben werden, then ist die Instanz sofort
                nutzbar (alle Folgemethoden koennen ohne weiteres Setup
                aufgerufen werden).
            TC-M04: Given der Konstruktor wird aufgerufen, when die
                Beispieldaten betrachtet werden, then ist
                `current_visitors < maximum_visitors` (Kapazitaet ist am
                Start nicht bereits ausgeschoepft, damit `sell_ticket()`
                manuell getestet werden kann).
        """
        self._animals: list[dict[str, Any]] = [
            {"id": 1, "name": "Leo", "species": "Lion", "age": 4,
             "health": 90, "hunger": 40, "energy": 70, "enclosure_id": 1},
            {"id": 2, "name": "Gina", "species": "Giraffe", "age": 6,
             "health": 95, "hunger": 20, "energy": 85, "enclosure_id": 2},
            {"id": 3, "name": "Pingu", "species": "Penguin", "age": 2,
             "health": 100, "hunger": 55, "energy": 60, "enclosure_id": 3},
        ]
        self._enclosures: list[dict[str, Any]] = [
            {"id": 1, "name": "Savannah", "enclosure_type": "Savanna",
             "capacity": 4, "cleanliness": 0.8, "temperature": 28.0},
            {"id": 2, "name": "Grassland", "enclosure_type": "Grassland",
             "capacity": 3, "cleanliness": 0.9, "temperature": 24.0},
            {"id": 3, "name": "Polar Bay", "enclosure_type": "Polar",
             "capacity": 6, "cleanliness": 0.95, "temperature": 5.0},
        ]
        self._zoo: dict[str, Any] = {
            "id": 1, "name": "Musterzoo", "location": "Berlin",
            "current_visitors": 12, "maximum_visitors": 50,
        }
        self._transactions: list[dict[str, Any]] = [
            {"id": 1, "transaction_type": "income", "amount": 250.0,
             "description": "Ticket sales (initial)"},
            {"id": 2, "transaction_type": "expense", "amount": -80.0,
             "description": "Food purchase (initial)"},
        ]
        self._simulation_time: int = 0

    def show_status(self) -> dict[str, Any]:
        """Liefert den aktuellen Zoo-Status (Besucher, Gehege, Tiere).

        Wird sowohl von der Route `/` (Dashboard) als auch von `/animals`
        (Tierliste) verwendet - beide zeigen nur einen anderen Ausschnitt
        desselben Status.

        Args:
            (keine)

        Returns:
            dict: `{"success": True, "message": str, "data": {"zoo": dict,
            "animals": pandas.DataFrame, "enclosures": pandas.DataFrame}}`.
            `show_status()` schlaegt in diesem Stub nie fehl, `success` ist
            daher immer `True`.

        Test:
            TC-M05: Given der Stub wurde mit den Standard-Beispieldaten
                initialisiert, when `show_status()` aufgerufen wird, then
                enthaelt `data["animals"]` genau 3 Zeilen und `data["zoo"]
                ["current_visitors"]` entspricht dem zuletzt bekannten Stand.
            TC-M06: Given `sell_ticket()` wurde zuvor erfolgreich aufgerufen,
                when `show_status()` danach aufgerufen wird, then ist
                `data["zoo"]["current_visitors"]` um die Anzahl der
                erfolgreichen Ticketverkaeufe erhoeht (Status spiegelt
                vorherige Aenderungen wider).
        """
        animals_df = pd.DataFrame(self._animals)
        enclosures_df = pd.DataFrame(self._enclosures)
        return {
            "success": True,
            "message": "Zoo status loaded.",
            "data": {
                "zoo": dict(self._zoo),
                "animals": animals_df,
                "enclosures": enclosures_df,
            },
        }

    def add_animal(self, data: dict[str, Any]) -> dict[str, Any]:
        """Legt ein neues Tier im Fake-Bestand an (Interface-Vollstaendigkeit).

        Aktuell von keiner der in `planning_frontend_alessio.md` Abschnitt 3
        gelisteten Routen verwendet; die Methode existiert hier nur, weil sie
        Teil der `ZooController`-Schnittstelle laut Klassendiagramm ist.

        Args:
            data (dict): Erwartet mindestens die Schluessel `name` (str),
                `species` (str) und `enclosure_id` (int).

        Returns:
            dict: `{"success": bool, "message": str, "data": dict | None}`.
            `success` ist `False`, wenn ein Pflichtfeld fehlt; `data`
            enthaelt in diesem Fall `None`.

        Test:
            TC-M07: Given `data` enthaelt `name`, `species` und
                `enclosure_id`, when `add_animal(data)` aufgerufen wird, then
                ist `success` `True` und das neue Tier erscheint danach in
                `show_status()["data"]["animals"]`.
            TC-M08: Given `data` fehlt der Schluessel `species`, when
                `add_animal(data)` aufgerufen wird, then ist `success`
                `False`, die Nachricht nennt das fehlende Feld, und der
                Tierbestand bleibt unveraendert.
        """
        required_fields = ("name", "species", "enclosure_id")
        missing = [field for field in required_fields if field not in data]
        if missing:
            return {
                "success": False,
                "message": f"Missing required field(s): {', '.join(missing)}.",
                "data": None,
            }

        new_id = max((animal["id"] for animal in self._animals), default=0) + 1
        new_animal = {
            "id": new_id,
            "name": data["name"],
            "species": data["species"],
            "age": data.get("age", 0),
            "health": data.get("health", 100),
            "hunger": data.get("hunger", 0),
            "energy": data.get("energy", 100),
            "enclosure_id": data["enclosure_id"],
        }
        self._animals.append(new_animal)
        return {
            "success": True,
            "message": f"Animal '{new_animal['name']}' added.",
            "data": new_animal,
        }

    def feed_animal(self, animal_id: int, food_id: int) -> dict[str, Any]:
        """Reduziert den Hunger eines Tieres (Fake-Fuetterung).

        Genutzt von der Route `POST /animals/<id>/feed`.

        Args:
            animal_id (int): ID des zu fuetternden Tieres.
            food_id (int): ID des verwendeten Futters (in diesem Stub nicht
                gegen einen echten Inventarbestand geprueft, nur auf
                Plausibilitaet: muss ein positiver int sein).

        Returns:
            dict: `{"success": bool, "message": str, "data": dict | None}`.
            `data` enthaelt bei Erfolg das aktualisierte Tier als dict.

        Test:
            TC-M09 (entspricht TC-F01 in planning_frontend_alessio.md): Given
                `animal_id` existiert und `food_id` ist ein positiver int,
                when `feed_animal(animal_id, food_id)` aufgerufen wird, then
                ist `success` `True` und der `hunger`-Wert des Tieres in
                `data` ist kleiner als vor dem Aufruf.
            TC-M10: Given `animal_id` existiert nicht im Fake-Bestand, when
                `feed_animal(animal_id, food_id)` aufgerufen wird, then ist
                `success` `False`, die Nachricht nennt die unbekannte ID, und
                `data` ist `None`.
        """
        animal = next((a for a in self._animals if a["id"] == animal_id), None)
        if animal is None:
            return {
                "success": False,
                "message": f"Animal with id {animal_id} not found.",
                "data": None,
            }
        if not isinstance(food_id, int) or food_id <= 0:
            return {
                "success": False,
                "message": "food_id must be a positive integer.",
                "data": None,
            }

        animal["hunger"] = max(0, animal["hunger"] - 30)
        return {
            "success": True,
            "message": f"{animal['name']} was fed (food_id={food_id}).",
            "data": dict(animal),
        }

    def sell_ticket(self, price: float) -> dict[str, Any]:
        """Verkauft ein Eintrittsticket, sofern der Zoo nicht voll ist.

        Genutzt von der Route `POST /tickets/buy`.

        Args:
            price (float): Ticketpreis; muss > 0 sein.

        Returns:
            dict: `{"success": bool, "message": str, "data": dict | None}`.
            `data` enthaelt bei Erfolg die neue Besucherzahl und den
            gebuchten Betrag.

        Test:
            TC-M11 (entspricht TC-F05): Given `current_visitors <
                maximum_visitors` und `price > 0`, when `sell_ticket(price)`
                aufgerufen wird, then ist `success` `True`,
                `current_visitors` ist um 1 erhoeht und eine
                Einnahme-Transaktion wurde erfasst.
            TC-M12 (entspricht TC-F06): Given `current_visitors ==
                maximum_visitors`, when `sell_ticket(price)` aufgerufen wird,
                then ist `success` `False`, die Nachricht lautet sinngemaess
                "zoo is full", und weder `current_visitors` noch die
                Transaktionsliste aendern sich.
        """
        if price <= 0:
            return {
                "success": False,
                "message": "Ticket price must be greater than 0.",
                "data": None,
            }
        if self._zoo["current_visitors"] >= self._zoo["maximum_visitors"]:
            return {
                "success": False,
                "message": "Zoo is full - no more tickets available.",
                "data": None,
            }

        self._zoo["current_visitors"] += 1
        new_id = max((t["id"] for t in self._transactions), default=0) + 1
        transaction = {
            "id": new_id, "transaction_type": "income",
            "amount": price, "description": "Ticket sale",
        }
        self._transactions.append(transaction)
        return {
            "success": True,
            "message": f"Ticket sold for {price:.2f}.",
            "data": {
                "current_visitors": self._zoo["current_visitors"],
                "transaction": transaction,
            },
        }

    def run_simulation_step(self) -> dict[str, Any]:
        """Fuehrt einen einzelnen Fake-Simulationsschritt aus.

        Genutzt von der Route `POST /simulation/step`. Erhoeht den
        Hunger und senkt die Energie jedes Tieres leicht, um dem Nutzer eine
        sichtbare Veraenderung im Dashboard zu zeigen, ohne die echte
        `SimulationEngine` (Backend-Schwerpunkt) zu benoetigen.

        Args:
            (keine)

        Returns:
            dict: `{"success": True, "message": str, "data": {"simulation_time":
            int}}`. Schlaegt in diesem Stub nie fehl.

        Test:
            TC-M13: Given `_simulation_time` steht auf 0, when
                `run_simulation_step()` einmal aufgerufen wird, then steht
                `data["simulation_time"]` auf 1 und jedes Tier hat einen
                `hunger`-Wert, der mindestens so hoch ist wie zuvor (Hunger
                steigt oder bleibt durch die Obergrenze gedeckelt gleich).
            TC-M14: Given `run_simulation_step()` wird zweimal hintereinander
                aufgerufen, when man die beiden Rueckgabewerte vergleicht,
                then unterscheidet sich `data["simulation_time"]` um genau 1
                zwischen den beiden Aufrufen (monoton steigender Zaehler).
        """
        self._simulation_time += 1
        for animal in self._animals:
            animal["hunger"] = min(100, animal["hunger"] + 5)
            animal["energy"] = max(0, animal["energy"] - 5)
        return {
            "success": True,
            "message": f"Simulation step {self._simulation_time} executed.",
            "data": {"simulation_time": self._simulation_time},
        }

    def create_report(self, format: str | None = None) -> dict[str, Any]:
        """Erstellt den Finanzbericht, wahlweise als Datei zum Download.

        Genutzt von der Route `GET /reports/financial`. Bei `format=None`
        (bzw. `"html"`) liefert `data["report"]` die Rohdaten fuer eine
        HTML-Tabelle. Bei `format="csv"`/`"xlsx"` schreibt dieser Stub
        (nur zu Testzwecken - im echten System uebernimmt das
        `ReportService`, Datenbank-Schwerpunkt) eine temporaere Datei und
        liefert deren Pfad zurueck, damit die Route sie per
        `flask.send_file()` ausliefern kann.

        Args:
            format (str | None): `None`/`"html"`, `"csv"` oder `"xlsx"`.

        Returns:
            dict: `{"success": bool, "message": str, "data": dict | None}`.
            Bei `format in ("csv", "xlsx")` enthaelt `data` die Schluessel
            `file_path` (str) und `mimetype` (str). Bei `format` in
            (`None`, `"html"`) enthaelt `data["report"]` eine
            `pandas.DataFrame` mit den Transaktionen. Bei unbekanntem
            `format` ist `success` `False`.

        Test:
            TC-M15 (entspricht TC-F07): Given Finanzdaten existieren (Stub-
                Transaktionen sind immer vorhanden), when
                `create_report("csv")` aufgerufen wird, then ist `success`
                `True`, `data["file_path"]` zeigt auf eine existierende
                `.csv`-Datei und `data["mimetype"]` ist `"text/csv"`.
            TC-M16 (entspricht TC-F08): Given Finanzdaten existieren, when
                `create_report("xlsx")` aufgerufen wird, then ist `success`
                `True`, `data["file_path"]` zeigt auf eine existierende
                `.xlsx`-Datei und `data["mimetype"]` entspricht dem
                Excel-Mimetype.
            TC-M17: Given ein nicht unterstuetztes `format` (z.B. `"pdf"`),
                when `create_report("pdf")` aufgerufen wird, then ist
                `success` `False` und `data` ist `None`, ohne dass eine
                Datei geschrieben wird.
        """
        transactions_df = pd.DataFrame(self._transactions)
        balance = transactions_df["amount"].sum() if not transactions_df.empty else 0.0

        if format in (None, "html"):
            return {
                "success": True,
                "message": "Financial report generated.",
                "data": {"report": transactions_df, "balance": balance},
            }

        if format not in ("csv", "xlsx"):
            return {
                "success": False,
                "message": f"Unsupported report format: {format!r}.",
                "data": None,
            }

        suffix = ".csv" if format == "csv" else ".xlsx"
        tmp_file = tempfile.NamedTemporaryFile(
            prefix="financial_report_", suffix=suffix, delete=False,
        )
        tmp_path = Path(tmp_file.name)
        tmp_file.close()

        if format == "csv":
            transactions_df.to_csv(tmp_path, index=False)
            mimetype = "text/csv"
        else:
            transactions_df.to_excel(tmp_path, index=False)
            mimetype = (
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet"
            )

        return {
            "success": True,
            "message": f"Financial report exported as {format}.",
            "data": {"file_path": str(tmp_path), "mimetype": mimetype},
        }
