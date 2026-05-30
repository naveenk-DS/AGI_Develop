from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine.url import URL

# Hardcoded credentials — change these if your pgAdmin settings change
DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username="postgres",
    password="Naveen@677",
    host="127.0.0.1",
    port=5433,
    database="AGI_Start",
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
