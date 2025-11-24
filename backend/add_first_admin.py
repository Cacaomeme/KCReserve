import os
import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models.whitelist import WhitelistEntry

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.getcwd())

def add_admin(email, database_url):
    if not database_url:
        print("Error: DATABASE_URL is not set.")
        return

    engine = create_engine(database_url)
    
    with Session(engine) as session:
        # Check if already exists
        stmt = select(WhitelistEntry).where(WhitelistEntry.email == email)
        existing = session.execute(stmt).scalar_one_or_none()
        
        if existing:
            print(f"Email {email} is already in the whitelist.")
            if not existing.is_admin_default:
                print("Updating to admin...")
                existing.is_admin_default = True
                session.commit()
                print("Updated.")
            return

        # Add new entry
        new_entry = WhitelistEntry(
            email=email,
            is_admin_default=True,
            display_name="Initial Admin"
        )
        session.add(new_entry)
        session.commit()
        print(f"Successfully added {email} as an admin to the whitelist.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_first_admin.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    db_url = os.environ.get("DATABASE_URL")
    
    if not db_url:
        db_url = input("Please enter your DATABASE_URL (Neon connection string): ").strip()
    
    add_admin(email, db_url)
