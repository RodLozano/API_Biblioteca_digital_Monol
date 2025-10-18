from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import DecBase

DATABASE_URL = "sqlite:///./library.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


if __name__ == "__main__":
    DecBase.metadata.create_all(bind=engine)
    print("Base de datos y tablas creadas correctamente.")