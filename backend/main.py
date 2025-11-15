"""Helper entry-point for quickly launching the Flask app."""

from app.main import app


def main() -> None:
    app.run(debug=True)


if __name__ == "__main__":
    main()
