from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

# Render and older Heroku connection strings start with postgres://, which
# SQLAlchemy 1.4+ rejects. Normalize to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_local_hosts = ("localhost", "host.docker.internal", "127.0.0.1", "db", "postgres")

# If sslmode is already specified in the query parameters (e.g. Neon, AWS RDS),
# SQLAlchemy respects the query string.
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
