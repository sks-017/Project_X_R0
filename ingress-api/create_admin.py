"""
Create Admin User Script
Creates an initial admin user for the system.
"""
from app import models, auth, database
from sqlalchemy.orm import Session
def create_admin():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == "admin").first()
        if user:
            print("[INFO] Admin user already exists")
            return
        hashed_password = auth.get_password_hash("admin123")
        admin_user = models.User(
            username="admin",
            email="admin@prodcontrol.com",
            password_hash=hashed_password,
            role="admin",
            active=True
        )
        db.add(admin_user)
        db.commit()
        print("[OK] Admin user created successfully")
        print("Username: admin")
        print("Password: admin123")
    except Exception as e:
        print(f"[ERROR] Error creating admin user: {e}")
    finally:
        db.close()
if __name__ == "__main__":
    create_admin()
