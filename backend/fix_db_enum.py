import os
import sys
from sqlalchemy import create_engine, text

def fix_enum(database_url):
    if not database_url:
        print("Error: DATABASE_URL is not set.")
        return

    engine = create_engine(database_url)
    
    print(f"Connecting to database...")
    with engine.connect() as conn:
        # Transaction is required for some operations, but ALTER TYPE cannot run in a transaction block in some contexts.
        # However, with sqlalchemy engine.connect(), we are in a transaction.
        # We need to commit to end the current transaction and set autocommit for the ALTER TYPE.
        conn.commit()
        connection = conn.execution_options(isolation_level="AUTOCOMMIT")
        
        try:
            print("Attempting to add 'cancellation_requested' to reservationstatus enum...")
            connection.execute(text("ALTER TYPE reservationstatus ADD VALUE IF NOT EXISTS 'cancellation_requested'"))
            print("Success: Added 'cancellation_requested'.")
        except Exception as e:
            print(f"Error adding cancellation_requested: {e}")

        try:
            print("Attempting to add 'cancellation_requested' to reservation_status enum (just in case)...")
            connection.execute(text("ALTER TYPE reservation_status ADD VALUE IF NOT EXISTS 'cancellation_requested'"))
            print("Success: Added 'cancellation_requested' (snake_case).")
        except Exception as e:
            print(f"Note: Could not add to reservation_status (this is expected if the type name is reservationstatus): {e}")

if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        if len(sys.argv) > 1:
            db_url = sys.argv[1]
        else:
            db_url = input("Please enter your DATABASE_URL (Neon connection string): ").strip()
    
    fix_enum(db_url)
