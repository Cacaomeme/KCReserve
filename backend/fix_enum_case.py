import os
import sys
from sqlalchemy import create_engine, text

def fix_enum_case(database_url):
    if not database_url:
        print("Error: DATABASE_URL is not set.")
        return

    engine = create_engine(database_url)
    
    print(f"Connecting to database...")
    with engine.connect() as conn:
        conn.commit()
        connection = conn.execution_options(isolation_level="AUTOCOMMIT")
        
        try:
            # Check current values
            result = connection.execute(text("SELECT unnest(enum_range(NULL::reservationstatus))")).fetchall()
            values = [row[0] for row in result]
            print(f"Current Enum values: {values}")

            # The error "invalid input value for enum reservationstatus: CANCELLATION_REQUESTED"
            # suggests that the database expects 'cancellation_requested' (lowercase)
            # but SQLAlchemy might be sending 'CANCELLATION_REQUESTED' (uppercase) if the Enum definition is tricky,
            # OR the database actually has 'CANCELLATION_REQUESTED' and we are sending lowercase?
            
            # Wait, the error says: invalid input value ... "CANCELLATION_REQUESTED"
            # This means the query sent "CANCELLATION_REQUESTED" (uppercase) but the DB only knows lowercase.
            
            # Let's verify if we need to add the UPPERCASE version too, or fix the Python code to send lowercase.
            # Python Enum: CANCELLATION_REQUESTED = "cancellation_requested"
            # SQLAlchemy should send the value ("cancellation_requested"), not the name.
            
            # However, if the Enum was created with native_enum=True (default for Postgres), 
            # sometimes there are issues with how values are bound.
            
            # Let's try to add the UPPERCASE version to the DB just to be safe and stop the crashing,
            # although the correct fix is ensuring consistency.
            
            print("Attempting to add 'CANCELLATION_REQUESTED' (uppercase) to reservationstatus enum...")
            connection.execute(text("ALTER TYPE reservationstatus ADD VALUE IF NOT EXISTS 'CANCELLATION_REQUESTED'"))
            print("Success: Added 'CANCELLATION_REQUESTED'.")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        if len(sys.argv) > 1:
            db_url = sys.argv[1]
        else:
            db_url = input("Please enter your DATABASE_URL: ").strip()
    
    fix_enum_case(db_url)
