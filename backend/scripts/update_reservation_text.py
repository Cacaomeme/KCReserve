"""Utility script to fix garbled reservation titles/descriptions."""

from __future__ import annotations

import argparse

from app.database import session_scope
from app.models.reservation import Reservation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Update an existing reservation's purpose/description using UTF-8 safe input. "
            "Run `chcp 65001` beforehand when using PowerShell to avoid mojibake."
        )
    )
    parser.add_argument("--id", type=int, required=True, dest="reservation_id", help="Reservation ID to update")
    parser.add_argument("--purpose", required=True, help="New purpose/title (UTF-8 string)")
    parser.add_argument(
        "--description",
        help="Optional description override. If omitted, the existing description is kept.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with session_scope() as session:
        reservation = session.get(Reservation, args.reservation_id)
        if reservation is None:
            raise SystemExit(f"Reservation #{args.reservation_id} not found")

        reservation.purpose = args.purpose
        if args.description is not None:
            reservation.description = args.description

        session.add(reservation)

    print(
        f"Reservation #{args.reservation_id} updated -> purpose='{args.purpose}'"
        + (f", description='{args.description}'" if args.description is not None else "")
    )


if __name__ == "__main__":
    main()
