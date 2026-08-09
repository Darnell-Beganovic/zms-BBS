"""Application entry point: builds and runs the Flask app with the real ZooController.

Schwerpunkt: Backend (Integration) - Darnell Beganovic

This is the official entry point referenced throughout the planning
docs (see README.md's "Running the Application" section: `python
main.py`, run from this folder). Unlike `frontend/dev_app.py` (a
Frontend-only local dev tool that never leaves the process' memory),
importing `zoo_view` here goes through the real `ZooController`
(`controller/zoo_controller.py`) instead of `MockZooController` - the
one-line import swap `zoo_view.py`'s own docstring anticipated. That
controller self-wires a real SQLite-backed ZooService/
SimulationService/ReportService on first use (see
`ZooController.__init__()`/`_build_default_dependencies()`), so no
additional wiring is needed here - `create_app()` only has to build the
Flask app and register the blueprint, exactly like `dev_app.py` does.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    # Started directly (`python main.py`, per README.md) rather than as
    # a module (`python -m zoo_simulation.main`) - Python then only adds
    # this file's own folder (zoo_simulation/) to sys.path, not the
    # project root, so `import zoo_simulation....` would fail. Same
    # fallback as zoo_view.py/dev_app.py.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask import Flask

from zoo_simulation.frontend.zoo_view import zoo_bp


def create_app() -> Flask:
    """Build the Flask app with the real ZooController wired in.

    Returns:
        Flask: app instance with `zoo_bp` registered. `SECRET_KEY` is a
        fixed dev value (needed for Flask's `flash()`); this project has
        no authentication/session-security requirements (see
        `planning.md`'s explicitly out-of-scope items), so a static key
        is sufficient here.

    Test:
        - Given `create_app()` is called, when a GET request to `/` is
          made via `app.test_client()`, then the status code is 200 and
          the response shows the self-wired starter zoo's name
          ("Musterzoo", see `zoo_controller.py`'s `_DEFAULT_ZOO_NAME`).
        - Given `create_app()` is called twice in a row, when both
          returned apps are compared, then they are two independent
          Flask instances (no shared global app state between calls) -
          `zoo_view.py`'s `_controller` module-level instance is shared
          between them regardless, since it is created once at import
          time, not per `create_app()` call.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-only-not-for-production"
    app.register_blueprint(zoo_bp)
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
