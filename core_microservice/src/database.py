from sqlmodel import create_engine, Session
from sqlalchemy.pool import QueuePool
from settings import app_config

# create the engine with connection pooling
engine = create_engine(
    app_config.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping = True,
    echo=False
)


# create the session generator that we will use in our dependancy injection
def get_db():
    with Session(engine) as db:
        try:
            yield db
        finally:
            db.close()