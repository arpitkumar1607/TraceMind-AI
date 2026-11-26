import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

logger = logging.getLogger("tracemind.database")

Base = declarative_base()

def get_engine():
    target_url = settings.DATABASE_URL
    try:
        # If PostgreSQL, try creating engine with a quick connect test
        if target_url.startswith("postgresql"):
            test_engine = create_engine(
                target_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3}
            )
            # Try connecting
            with test_engine.connect() as conn:
                logger.info("Successfully connected to PostgreSQL at %s", target_url.split("@")[-1])
            return test_engine
        else:
            return create_engine(target_url, connect_args={"check_same_thread": False})
    except Exception as e:
        logger.warning(
            "Could not connect to configured database (%s). Error: %s. Falling back to SQLite for local session.",
            target_url, str(e)
        )
        fallback_url = "sqlite:///./tracemind.db"
        return create_engine(fallback_url, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables defined in models."""
    from backend import models  # noqa
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
