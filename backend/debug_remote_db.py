import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.reservation import Reservation, ReservationStatus

def debug_db(database_url):
    if not database_url:
        print("Error: DATABASE_URL is not set.")
        return

    print(f"Connecting to database...")
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Check Enum values in DB
        print("\n--- Checking Database Enum Values ---")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT unnest(enum_range(NULL::reservationstatus))")).fetchall()
            values = [row[0] for row in result]
            print(f"Enum values in DB: {values}")
            
            if 'cancellation_requested' in values:
                print("OK: 'cancellation_requested' exists in DB Enum.")
            else:
                print("FAIL: 'cancellation_requested' is MISSING from DB Enum.")

        # 2. Try to query reservations (Read Test)
        print("\n--- Testing Read Operation ---")
        reservations = session.query(Reservation).limit(5).all()
        print(f"Successfully read {len(reservations)} reservations.")
        for r in reservations:
            print(f" - ID: {r.id}, Status: {r.status}")

        # 3. Try to query pending count (Logic Test)
        print("\n--- Testing Pending Count Query ---")
        from sqlalchemy import or_
        count = session.query(Reservation).filter(
            or_(
                Reservation.status == ReservationStatus.PENDING,
                Reservation.status == ReservationStatus.CANCELLATION_REQUESTED
            )
        ).count()
        print(f"Pending count query success. Count: {count}")

    except Exception as e:
        print(f"\n!!! ERROR OCCURRED !!!")
        print(e)
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        if len(sys.argv) > 1:
            db_url = sys.argv[1]
        else:
            db_url = input("Please enter your DATABASE_URL: ").strip()
    
    debug_db(db_url)
