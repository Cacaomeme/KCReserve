import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User

def check_admin_notifications(database_url):
    if not database_url:
        print("Error: DATABASE_URL is not set.")
        return

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Checking admin users...")
        admins = session.query(User).filter(User.is_admin == True).all()
        
        if not admins:
            print("No admin users found!")
            return

        for admin in admins:
            status = "ON" if admin.receives_notification else "OFF"
            print(f"- Admin: {admin.email} (Notifications: {status})")
            
            if not admin.receives_notification:
                print(f"  -> Enabling notifications for {admin.email}...")
                admin.receives_notification = True
                session.commit()
                print("  -> Done.")
        
        print("\nCheck complete. All admins should now receive notifications.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        if len(sys.argv) > 1:
            db_url = sys.argv[1]
        else:
            db_url = input("Please enter your DATABASE_URL: ").strip()
    
    check_admin_notifications(db_url)
