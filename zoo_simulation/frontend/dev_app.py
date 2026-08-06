"""Lokaler Dev-Runner, um den ZooView-Blueprint manuell im Browser zu testen.

Schwerpunkt: Frontend (Presentation Layer) - Alessio Bellamacina
author: Alessio Bellamacina

Dies ist NICHT der offizielle Anwendungseinstiegspunkt des Gesamtsystems -
das bleibt `zoo_simulation/main.py` (aktuell leer, Teil der gemeinsamen
Integrationsarbeit lt. `planning.md`). Diese Datei existiert ausschliesslich,
damit der Frontend-Schwerpunkt die Flask-Oberflaeche lokal starten und
durchklicken kann, ohne auf die Fertigstellung von `main.py` bzw. des
echten `ZooController` warten zu muessen.

Start, wahlweise:
    py -m zoo_simulation.frontend.dev_app        (aus dem Projekt-Root)
    py zoo_simulation/frontend/dev_app.py        (von ueberall, z.B. IDE-Run-Button)

Beide Varianten funktionieren, siehe Kommentar beim sys.path-Fallback unten.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    # Datei wurde direkt gestartet (`python dev_app.py`, z.B. per IDE-Run-
    # Button) statt als Modul (`python -m zoo_simulation.frontend.dev_app`).
    # In diesem Fall fuegt Python nur den Ordner dieser Datei zu sys.path
    # hinzu, nicht das Projekt-Root - dadurch waere `zoo_simulation` nicht
    # importierbar. Wir tragen das Projekt-Root (zwei Ebenen ueber dieser
    # Datei: dev_app.py -> frontend/ -> zoo_simulation/ -> Projekt-Root)
    # deshalb hier manuell nach.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from flask import Flask

from zoo_simulation.frontend.zoo_view import zoo_bp


def create_app() -> Flask:
    """Baut eine minimale Flask-App nur fuer lokale Frontend-Tests.

    Args:
        (keine)

    Returns:
        Flask: App-Instanz mit registriertem `zoo_bp`-Blueprint. Der
        `SECRET_KEY` ist ein fest verdrahteter Dev-Wert (noetig fuer Flask's
        `flash()`), nicht fuer den produktiven Einsatz gedacht.

    Test:
        TC-V05: Given `create_app()` wird aufgerufen, when man mit
            `app.test_client()` ein GET auf `/` ausfuehrt, then ist der
            Statuscode 200 und die Antwort enthaelt den Zoo-Namen aus den
            Mock-Daten (`"Musterzoo"`).
        TC-V06: Given `create_app()` wird zweimal hintereinander aufgerufen,
            when man die beiden zurueckgegebenen Objekte vergleicht, then
            sind es zwei unabhaengige `Flask`-Instanzen (kein geteilter
            globaler App-Zustand zwischen Aufrufen).
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-only-not-for-production"
    app.register_blueprint(zoo_bp)
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
