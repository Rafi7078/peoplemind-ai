from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import settings


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return (
            "postgresql+psycopg://"
            + database_url[len("postgresql://"): ]
        )

    if database_url.startswith("postgres://"):
        return (
            "postgresql+psycopg://"
            + database_url[len("postgres://"): ]
        )

    return database_url


database_url = normalize_database_url(
    settings.database_url
)

is_sqlite = database_url.startswith("sqlite")

if is_sqlite:
    engine = create_engine(
        database_url,
        connect_args={
            "check_same_thread": False
        },
    )
else:
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
