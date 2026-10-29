from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

_local_hosts = ("localhost", "host.docker.internal", "127.0.0.1", "db", "postgres")

# If sslmode is already specified in the query parameters (e.g. Neon, AWS RDS),
# SQLAlchemy / psycopg2 respects the query string.
# Otherwise, default to sslmode=require only for external remote hosts.
has_ssl_in_url = "sslmode=" in DATABASE_URL or "ssl=" in DATABASE_URL
is_local_or_docker = any(h in DATABASE_URL for h in _local_hosts)

if has_ssl_in_url or is_local_or_docker:
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require"},
    )

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
