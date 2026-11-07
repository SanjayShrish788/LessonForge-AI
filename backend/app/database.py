from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from pathlib import Path
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import get_settings, BACKEND_DIR


class Base(DeclarativeBase):
    pass


url = get_settings().database_url
resolved_url = make_url(url)
if url.startswith("sqlite") and resolved_url.database and resolved_url.database != ":memory:" and not Path(resolved_url.database).is_absolute():
    resolved_url = resolved_url.set(database=str((BACKEND_DIR / resolved_url.database).resolve()))
engine = create_engine(resolved_url, connect_args={"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


if url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def sqlite_settings(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")


def get_db():
    with SessionLocal() as session:
        yield session


def init_db():
    from . import models  # register models
    Base.metadata.create_all(engine)
