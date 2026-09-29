from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

try:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    print(f"CRITICAL DATABASE ERROR: {e}")
    engine = None
    SessionLocal = None
    Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    try:
        # Delayed import to avoid circular dependency
        import database.models
        Base.metadata.create_all(bind=engine)
        print("Database connected and tables verified.")
    except Exception as e:
        print(f"Database initialization failed: {e}")