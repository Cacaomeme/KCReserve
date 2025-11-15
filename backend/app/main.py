"""Entry-point for running the Flask development server."""

from __future__ import annotations

from . import create_app

app = create_app()


if __name__ == "__main__":
    # Useful when running `uv run python app/main.py`
    app.run(debug=True)
