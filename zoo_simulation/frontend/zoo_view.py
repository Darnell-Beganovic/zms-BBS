"""ZooView: Flask-Blueprint fuer die Presentation Layer des ZMS.

Schwerpunkt: Frontend (Presentation Layer) - Alessio Bellamacina
author: Alessio Bellamacina

Dieses Modul implementiert `ZooView` aus dem Klassendiagramm
(`Projektplanung/Klassendiagramm_Code.md`) als Flask-Blueprint statt als
einzelne Konsolen-Klasse (siehe `planning_frontend_alessio.md` Abschnitt 2).
Die Routen entsprechen der Tabelle in Abschnitt 3 desselben Dokuments.

Architektur-Regel (siehe `planning_frontend_alessio.md` Abschnitt 1): dieses
Modul spricht NIEMALS direkt mit Domain-Modell, Services oder Repositories.
Jede Route ruft ausschliesslich `ZooController` auf. Solange der echte
`ZooController` (Backend-Schwerpunkt, Darnell Beganovic) noch nicht
implementiert ist, wird stattdessen `MockZooController` aus
`controller_stub.py` verwendet - identischer Vertrag, siehe dortiges
Modul-Docstring. Der Tausch auf die echte Implementierung passiert an genau
einer Stelle (dem Import unten).

Eingabeformulare werden hier nur oberflaechlich validiert (Pflichtfelder,
Typen). Domain-Validierung (z.B. "hunger darf nicht negativ werden") ist
bewusst nicht Aufgabe dieser Datei, sondern des Service-Layers hinter
`ZooController` (siehe `planning_backend_darnell.md` Abschnitt "Open
Questions").

Flash-Messages: `ZooController`-Ergebnisse (`{"success", "message", "data"}`)
werden ueber `show_message()` per Flask `flash()` gespeichert und beim
naechsten gerenderten Template (siehe `templates/base.html`) angezeigt. Das
weicht bewusst vom Klassendiagramm ab, das `show_message(message: str)
Response` zeigt: Flask's idiomatisches Post/Redirect/Get-Muster erzeugt die
tatsaechliche `Response` erst durch das nachfolgende `render_template()`/
`redirect()` der jeweiligen Route, nicht durch `show_message()` selbst.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    # Diese Datei ist ein Flask-Blueprint-Modul, kein Einstiegspunkt - siehe
    # `if __name__ == "__main__":` unten fuer den Hinweis, falls sie trotzdem
    # direkt gestartet wird (z.B. per IDE-Run-Button). Der sys.path-Fallback
    # ist derselbe wie in `dev_app.py`: bei Direktstart fehlt sonst das
    # Projekt-Root in sys.path und der Import von `zoo_simulation` schlaegt
    # mit `ModuleNotFoundError` fehl.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from zoo_simulation.frontend.controller_stub import MockZooController as ZooController

zoo_bp = Blueprint("zoo", __name__, template_folder="templates")

# Erlaubte Werte fuer den `format`-Query-Parameter von `/reports/financial`.
# `None` steht fuer "kein Parameter angegeben" (request.args.get() liefert
# dann None), gleichbedeutend mit `"html"`.
_VALID_REPORT_FORMATS = (None, "html", "csv", "xlsx")

# Ein Controller pro Prozess, wiederverwendet ueber alle Requests hinweg -
# noetig, damit der In-Memory-Zustand des Stubs (siehe controller_stub.py)
# zwischen Formular-Submits erhalten bleibt. Der echte ZooController wird
# vermutlich genauso als Singleton instanziiert werden.
_controller = ZooController()


def show_message(message: str, category: str = "info") -> None:
    """Merkt eine Erfolgs-/Fehlermeldung von ZooController fuer die naechste Response vor.

    Wrapper um Flask's `flash()`, siehe Hinweis zum Post/Redirect/Get-Muster
    im Modul-Docstring. `category` steuert die CSS-Klasse in
    `templates/base.html` (`flash-success`, `flash-error`, `flash-info`).

    Args:
        message (str): Anzuzeigender Text, wird unveraendert (nicht escaped
            durch uns - Jinja2 escaped automatisch beim Rendern) angezeigt.
        category (str): Eine von `"success"`, `"error"`, `"info"`.
            Default `"info"`.

    Returns:
        None: Die Nachricht liegt danach in der Flask-Session und wird beim
        naechsten `get_flashed_messages()`-Aufruf im Template konsumiert.

    Test:
        TC-V01: Given `message="Fehler beim Laden"` und `category="error"`,
            when `show_message()` aufgerufen wird und danach ein Template
            gerendert wird, then enthaelt die HTML-Antwort ein Element mit
            der CSS-Klasse `flash-error` und dem Text der Nachricht.
        TC-V02: Given `show_message()` wird zweimal mit unterschiedlichen
            Nachrichten aufgerufen, bevor ein Template gerendert wird, then
            erscheinen beide Nachrichten in Aufrufreihenfolge in der
            gerenderten Flash-Liste (Flask akkumuliert mehrere Meldungen pro
            Request-Zyklus).
    """
    flash(message, category)


@zoo_bp.route("/", methods=["GET"])
def index() -> str:
    """Route `GET /`: zeigt das Zoo-Dashboard (Besucher, Gehege).

    Ruft ausschliesslich `ZooController.show_status()` auf (siehe
    Routen-Tabelle in `planning_frontend_alessio.md` Abschnitt 3) und
    delegiert das Rendering an `show_zoo_status()`.

    Args:
        (keine; Flask uebergibt keine URL-Parameter fuer `/`)

    Returns:
        str: Gerenderter HTML-Inhalt (von Flask automatisch in eine
        `Response` mit Status 200 verpackt).

    Test:
        TC-V03: Given `ZooController.show_status()` liefert
            `success=True` mit Gehege-Daten, when GET `/` aufgerufen wird,
            then antwortet die Route mit Status 200 und das Dashboard zeigt
            Zoo-Name, Standort und Besucherzahl aus `data["zoo"]`.
        TC-V04: Given `ZooController.show_status()` liefert `success=False`
            (z.B. ein zukuenftiger Datenbankfehler), when GET `/` aufgerufen
            wird, then wird die Fehlermeldung per `show_message()` geflasht
            und das Dashboard wird trotzdem mit leeren Daten gerendert, statt
            einen 500-Fehler an den Nutzer auszuliefern.
    """
    result = _controller.show_status()
    if not result["success"]:
        show_message(result["message"], category="error")
        return render_template("index.html", zoo={}, enclosures=[])
    return show_zoo_status(result["data"])


def show_zoo_status(status_data: dict) -> str:
    """Rendert das Dashboard-Template mit Zoo-Stammdaten und Gehegen.

    Entspricht `ZooView.show_zoo_status(data: DataFrame) Response` im
    Klassendiagramm; `status_data` hier ist das `data`-Feld aus
    `ZooController.show_status()`'s Result-Dict (siehe
    `planning_frontend_alessio.md` Abschnitt 2.1), welches sowohl den
    Zoo-Stammdaten-dict als auch das Gehege-`DataFrame` enthaelt.

    Args:
        status_data (dict): Erwartet die Schluessel `"zoo"` (dict) und
            `"enclosures"` (`pandas.DataFrame`).

    Returns:
        str: Gerenderter Inhalt von `templates/index.html`.

    Test:
        TC-F03 (siehe planning_frontend_alessio.md): Given ein
            nicht-leeres `DataFrame` von Gehegen, when
            `show_zoo_status(status_data)` aufgerufen wird, then rendert das
            Dashboard-Template eine Zeile pro Gehege in der Gehege-Tabelle.
        TC-F04 (siehe planning_frontend_alessio.md): Given ein leeres
            `DataFrame` (noch keine Gehege angelegt), when
            `show_zoo_status(status_data)` aufgerufen wird, then wird
            stattdessen ein freundlicher "noch keine Gehege"-Hinweis gezeigt,
            keine leere Tabelle.
    """
    enclosures = status_data["enclosures"].to_dict(orient="records")
    return render_template("index.html", zoo=status_data["zoo"], enclosures=enclosures)


@zoo_bp.route("/animals", methods=["GET"])
def list_animals() -> str:
    """Route `GET /animals`: listet alle Tiere mit Hunger/Health/Energy.

    Ruft wie `index()` `ZooController.show_status()` auf (siehe Routen-
    Tabelle in `planning_frontend_alessio.md` Abschnitt 3 - beide Routen
    zeigen nur einen anderen Ausschnitt desselben Status) und delegiert das
    Rendering an `show_animals()`.

    Args:
        (keine; Flask uebergibt keine URL-Parameter fuer `/animals`)

    Returns:
        str: Gerenderter HTML-Inhalt (von Flask automatisch in eine
        `Response` mit Status 200 verpackt).

    Test:
        TC-V07: Given `ZooController.show_status()` liefert `success=True`
            mit einem nicht-leeren Animals-`DataFrame`, when GET `/animals`
            aufgerufen wird, then antwortet die Route mit Status 200 und die
            Tabelle zeigt eine Zeile pro Tier inkl. Hunger/Health/Energy.
        TC-V08: Given `ZooController.show_status()` liefert `success=False`,
            when GET `/animals` aufgerufen wird, then wird die Fehlermeldung
            per `show_message()` geflasht und die Seite rendert eine leere
            Tierliste statt eines 500-Fehlers.
    """
    result = _controller.show_status()
    if not result["success"]:
        show_message(result["message"], category="error")
        return render_template("animals.html", animals=[])
    return show_animals(result["data"])


def show_animals(status_data: dict) -> str:
    """Rendert das Template mit der Tierliste (Hunger/Health/Energy je Tier).

    Entspricht `ZooView.show_animals(data: DataFrame) Response` im
    Klassendiagramm. Anders als `show_zoo_status()` braucht diese Funktion
    nur den Animals-Teil von `status_data`, ignoriert `"zoo"`/`"enclosures"`.

    Args:
        status_data (dict): Erwartet mindestens den Schluessel `"animals"`
            (`pandas.DataFrame` mit Spalten u.a. `id`, `name`, `species`,
            `hunger`, `health`, `energy`).

    Returns:
        str: Gerenderter Inhalt von `templates/animals.html`.

    Test:
        TC-V09 (analog TC-F03): Given ein nicht-leeres Animals-`DataFrame`,
            when `show_animals(status_data)` aufgerufen wird, then rendert
            das Template eine Zeile pro Tier mit Name, Spezies, Hunger,
            Health und Energy.
        TC-V10 (analog TC-F04): Given ein leeres Animals-`DataFrame` (noch
            keine Tiere angelegt), when `show_animals(status_data)`
            aufgerufen wird, then wird ein freundlicher "noch keine
            Tiere"-Hinweis gezeigt statt einer leeren Tabelle.
    """
    animals = status_data["animals"].to_dict(orient="records")
    return render_template("animals.html", animals=animals)


@zoo_bp.route("/animals/<int:animal_id>/feed", methods=["POST"])
def handle_feed_animal_form(animal_id: int):
    """Route `POST /animals/<id>/feed`: verarbeitet das Fuetterungsformular.

    Entspricht `ZooView.handle_feed_animal_form(request: Request) Response`
    im Klassendiagramm. Die Signatur nimmt hier `animal_id` als
    Flask-URL-Parameter entgegen statt eines expliziten `request`-Arguments;
    inhaltlich ist das dasselbe, da Flask's globales `request`-Objekt (aus
    `flask import request`) innerhalb der Funktion ohnehin verfuegbar ist und
    fuer die Formularfelder (`food_id`) genutzt wird.

    Nur oberflaechliche Validierung (Pflichtfeld, Typ) - siehe Modul-
    Docstring: `animal_id` wird bereits von Flask's `<int:...>`-Konverter auf
    Typ int geprueft (nicht-numerische IDs fuehren zu 404, bevor diese
    Funktion ueberhaupt aufgerufen wird); `food_id` wird hier auf "vorhanden
    und positive Ganzzahl" geprueft. Ob `animal_id` tatsaechlich zu einem
    existierenden Tier gehoert, entscheidet - wie in
    `planning_backend_darnell.md` festgelegt ("Flask validates input shape,
    the service layer validates domain rules") - `ZooController.feed_animal()`,
    nicht diese Funktion.

    Args:
        animal_id (int): ID des zu fuetternden Tieres, aus der URL.

    Returns:
        Response | tuple[str, int]: Bei ungueltigem `food_id` ein
        gerenderter Fehlerzustand der Tierliste mit Status 400, ohne dass
        `ZooController.feed_animal()` aufgerufen wird. Bei gueltiger Eingabe
        ein Redirect (Status 302) zurueck auf `/animals` nach dem
        Post/Redirect/Get-Muster, mit der Erfolgs-/Fehlermeldung von
        `ZooController.feed_animal()` als Flash-Message.

    Test:
        TC-F01 (siehe planning_frontend_alessio.md): Given ein POST-Request
            mit gueltigem `animal_id` und `food_id`, when das Formular
            abgeschickt wird, then wird `ZooController.feed_animal()` mit den
            geparsten Werten aufgerufen und eine Erfolgsmeldung wird
            (per Flash-Message nach dem Redirect) angezeigt.
        TC-F02 (siehe planning_frontend_alessio.md): Given ein POST-Request
            ohne das Feld `food_id`, when das Formular abgeschickt wird,
            then wird der Request mit Status 400 abgelehnt und eine
            Fehlermeldung gezeigt, ohne dass `ZooController.feed_animal()`
            aufgerufen wird.
        TC-V11: Given ein POST-Request mit `food_id="abc"` (kein Zahlwert),
            when das Formular abgeschickt wird, then wird der Request
            ebenfalls mit Status 400 und einer Fehlermeldung abgelehnt, ohne
            dass `ZooController.feed_animal()` aufgerufen wird (gleiche
            Behandlung wie ein fehlendes Feld).
    """
    food_id_raw = request.form.get("food_id", "").strip()

    if not food_id_raw or not food_id_raw.isdigit() or int(food_id_raw) <= 0:
        show_message(
            "Bitte eine gueltige Futter-ID (positive Ganzzahl) angeben.",
            category="error",
        )
        return list_animals(), 400

    result = _controller.feed_animal(animal_id, int(food_id_raw))
    show_message(result["message"], category="success" if result["success"] else "error")
    return redirect(url_for("zoo.list_animals"))


@zoo_bp.route("/tickets/buy", methods=["POST"])
def handle_buy_ticket_form():
    """Route `POST /tickets/buy`: verarbeitet das Ticketkauf-Formular.

    Entspricht `ZooView.handle_buy_ticket_form(request: Request) Response`
    im Klassendiagramm (siehe `handle_feed_animal_form()` fuer die Anmerkung
    zur `request`-Signatur). Das Formular liegt auf dem Dashboard
    (`templates/index.html`), da dort bereits die Besucherzahl angezeigt
    wird.

    Nur oberflaechliche Validierung (Pflichtfeld, Typ): geprueft wird, dass
    `price` vorhanden und als Zahl parsbar ist. Ob der Preis positiv ist und
    ob der Zoo noch Kapazitaet hat ("zoo is full", TC-F06), sind bewusst
    Domain-Entscheidungen und bleiben bei `ZooController.sell_ticket()`
    (siehe `planning_backend_darnell.md`: "Flask validates input shape, the
    service layer validates domain rules") - diese Funktion ruft
    `sell_ticket()` in diesen Faellen trotzdem auf und zeigt dessen
    Fehlermeldung an, statt selbst zu entscheiden, ob der Preis gueltig ist.

    Args:
        (keine expliziten; `price` wird aus `flask.request.form` gelesen)

    Returns:
        Response | tuple[str, int]: Bei fehlendem/nicht-numerischem `price`
        ein gerendertes Dashboard mit Status 400, ohne dass
        `ZooController.sell_ticket()` aufgerufen wird. Bei gueltiger Eingabe
        ein Redirect (Status 302) zurueck auf `/` nach dem
        Post/Redirect/Get-Muster, mit der Erfolgs-/Fehlermeldung von
        `ZooController.sell_ticket()` als Flash-Message.

    Test:
        TC-F05 (siehe planning_frontend_alessio.md): Given ein POST-Request
            mit gueltigem Ticketpreis und der Zoo hat noch Kapazitaet, when
            das Formular abgeschickt wird, then wird
            `ZooController.sell_ticket()` mit dem geparsten Preis aufgerufen
            und eine Bestaetigung (Erfolgsmeldung nach dem Redirect) gezeigt.
        TC-F06 (siehe planning_frontend_alessio.md): Given der Zoo steht bei
            `maximum_visitors`-Kapazitaet, when das Formular abgeschickt
            wird, then zeigt `ZooController.sell_ticket()` die Fehlermeldung
            "zoo is full" und keine Transaktion wird erfasst - die Route
            leitet trotzdem (mit dieser Fehlermeldung) zurueck zum Dashboard.
        TC-V12: Given ein POST-Request ohne das Feld `price`, when das
            Formular abgeschickt wird, then wird der Request mit Status 400
            abgelehnt und `ZooController.sell_ticket()` nicht aufgerufen.
        TC-V13: Given ein POST-Request mit `price="abc"` (kein Zahlwert),
            when das Formular abgeschickt wird, then wird der Request
            ebenfalls mit Status 400 abgelehnt, ohne dass
            `ZooController.sell_ticket()` aufgerufen wird.
    """
    price_raw = request.form.get("price", "").strip()

    if not price_raw:
        show_message("Bitte einen Ticketpreis angeben.", category="error")
        return index(), 400

    try:
        price = float(price_raw)
    except ValueError:
        show_message("Ticketpreis muss eine Zahl sein.", category="error")
        return index(), 400

    result = _controller.sell_ticket(price)
    show_message(result["message"], category="success" if result["success"] else "error")
    return redirect(url_for("zoo.index"))


@zoo_bp.route("/simulation/step", methods=["POST"])
def handle_simulation_step():
    """Route `POST /simulation/step`: stoesst einen Simulationsschritt an.

    Reine Aktions-Route ohne Formularfelder - es gibt daher nichts
    oberflaechlich zu validieren (kein Pflichtfeld, kein Typ zu pruefen).
    Wie `index()`/`list_animals()` ist dies reine Routing-Verdrahtung ohne
    inhaltliche Rendering-Arbeit und daher bewusst keine eigene `ZooView`-
    Methode im Klassendiagramm (siehe `planning_frontend_alessio.md`
    Abschnitt 2.2).

    Args:
        (keine; POST-Body wird nicht ausgewertet)

    Returns:
        Response: Redirect (Status 302) zurueck auf `/`, mit der
        Erfolgs-/Fehlermeldung von `ZooController.run_simulation_step()`
        als Flash-Message.

    Test:
        TC-V14: Given die Simulation steht bei Schritt 0, when
            `POST /simulation/step` abgeschickt wird, then wird
            `ZooController.run_simulation_step()` genau einmal aufgerufen,
            der Simulationsschritt-Zaehler erhoeht sich um 1 und nach dem
            Redirect wird eine Erfolgsmeldung angezeigt.
        TC-V15: Given `POST /simulation/step` wird zweimal hintereinander
            abgeschickt, when man die beiden Antworten vergleicht, then
            fuehrt jeder Aufruf zu einem Redirect (Status 302) zurueck auf
            `/`, unabhaengig davon, wie viele Schritte bereits gelaufen sind
            (kein Sonderfall fuer den ersten/letzten Schritt).
    """
    result = _controller.run_simulation_step()
    show_message(result["message"], category="success" if result["success"] else "error")
    return redirect(url_for("zoo.index"))


@zoo_bp.route("/reports/financial", methods=["GET"])
def financial_report():
    """Route `GET /reports/financial`: zeigt oder exportiert den Finanzbericht.

    Ruft `ZooController.create_report(format)` auf (siehe Routen-Tabelle in
    `planning_frontend_alessio.md` Abschnitt 3). Ohne `format`-Query-
    Parameter (oder `format=html`) wird der Bericht als HTML-Tabelle
    gerendert; bei `format=csv`/`format=xlsx` wird die vom Controller
    gelieferte Datei per `flask.send_file()` zum Download angeboten - das
    Frontend erzeugt die CSV/Excel-Datei nicht selbst (siehe
    `planning_frontend_alessio.md` Abschnitt 2.1).

    Oberflaechliche Validierung: `format` muss einer der bekannten Werte
    (`None`/fehlend, `"html"`, `"csv"`, `"xlsx"`) sein - das ist eine reine
    Shape-Pruefung dieser Route (welche Query-Werte sie ueberhaupt kennt),
    nicht Sache des Controllers. Ein unbekannter Wert wird daher schon hier
    mit 400 abgelehnt, bevor `ZooController.create_report()` aufgerufen
    wird.

    Args:
        (keine expliziten; `format` wird aus `flask.request.args` gelesen)

    Returns:
        Response | str | tuple[str, int]: Bei unbekanntem `format` ein
        gerendertes (leeres) Berichts-Template mit Status 400. Bei
        `format=csv`/`"xlsx"` und Erfolg eine Datei-Download-`Response` von
        `send_file()`. Sonst der gerenderte HTML-Bericht (Status 200), ggf.
        mit geflashter Fehlermeldung, falls `create_report()` fehlschlaegt.

    Test:
        TC-F07 (siehe planning_frontend_alessio.md): Given Finanzdaten
            existieren, when die Route mit `format=csv` aufgerufen wird,
            then liefert `ZooController.create_report("csv")` eine Datei und
            die Route sendet sie als herunterladbare CSV-Datei zurueck.
        TC-F08 (siehe planning_frontend_alessio.md): Given Finanzdaten
            existieren, when die Route mit `format=xlsx` aufgerufen wird,
            then liefert `ZooController.create_report("xlsx")` eine Datei
            und die Route sendet sie als herunterladbare Excel-Datei zurueck.
        TC-V16: Given kein `format`-Query-Parameter wird mitgeschickt, when
            die Route aufgerufen wird, then werden Bilanz und
            Transaktionstabelle als HTML gerendert (Status 200), ohne dass
            ein Datei-Download ausgeloest wird.
        TC-V17: Given ein nicht unterstuetzter `format`-Wert (z.B. `"pdf"`),
            when die Route mit `format=pdf` aufgerufen wird, then wird der
            Request mit Status 400 abgelehnt und eine Fehlermeldung gezeigt,
            ohne dass `ZooController.create_report()` aufgerufen wird.
    """
    requested_format = request.args.get("format") or None

    if requested_format not in _VALID_REPORT_FORMATS:
        show_message(f"Unbekanntes Report-Format: {requested_format!r}.", category="error")
        return show_financial_report(), 400

    result = _controller.create_report(requested_format)
    if not result["success"]:
        show_message(result["message"], category="error")
        return show_financial_report()

    if requested_format in ("csv", "xlsx"):
        file_info = result["data"]
        return send_file(
            file_info["file_path"],
            mimetype=file_info["mimetype"],
            as_attachment=True,
            download_name=f"financial_report.{requested_format}",
        )

    return show_financial_report(result["data"])


def show_financial_report(report_data: dict | None = None) -> str:
    """Rendert das Template mit Transaktionstabelle und Bilanz.

    Entspricht `ZooView.show_financial_report(data: DataFrame) Response` im
    Klassendiagramm; `report_data` hier ist (analog zu `show_zoo_status()`)
    das `data`-Feld aus `ZooController.create_report()`'s Result-Dict, nicht
    ein rohes `DataFrame`.

    Args:
        report_data (dict | None): Erwartet die Schluessel `"report"`
            (`pandas.DataFrame` mit den Transaktionen) und `"balance"`
            (float). `None` (Default) steht fuer "keine Daten verfuegbar"
            (z.B. Fehlerfall) und wird wie eine leere Transaktionsliste
            behandelt.

    Returns:
        str: Gerenderter Inhalt von `templates/financial_report.html`.

    Test:
        TC-V18: Given `report_data` mit einer nicht-leeren Transaktionen-
            `DataFrame`, when `show_financial_report(report_data)`
            aufgerufen wird, then rendert das Template eine Zeile pro
            Transaktion sowie die korrekte Bilanz.
        TC-V19 (analog TC-F04): Given `report_data=None` oder ein leeres
            Transaktionen-`DataFrame`, when `show_financial_report(...)`
            aufgerufen wird, then wird ein freundlicher "noch keine
            Transaktionen"-Hinweis gezeigt statt einer leeren Tabelle.
    """
    if report_data is None:
        return render_template("financial_report.html", transactions=[], balance=0.0)
    transactions = report_data["report"].to_dict(orient="records")
    return render_template(
        "financial_report.html", transactions=transactions, balance=report_data["balance"]
    )


if __name__ == "__main__":
    # Diese Datei enthaelt nur den Blueprint, keinen lauffaehigen Server -
    # Flask-Blueprints werden von einer Flask-App registriert, nicht selbst
    # gestartet. Zum manuellen Testen im Browser bitte `dev_app.py` starten:
    #   py -m zoo_simulation.frontend.dev_app
    print(
        "zoo_view.py ist ein Flask-Blueprint-Modul, kein Einstiegspunkt.\n"
        "Zum lokalen Testen bitte stattdessen ausfuehren:\n"
        "    py -m zoo_simulation.frontend.dev_app\n"
        "oder die Datei zoo_simulation/frontend/dev_app.py direkt starten."
    )
