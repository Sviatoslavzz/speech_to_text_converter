from talkushka_service.config.settings import DSN
from talkushka_service.db.model import Base


async def migrate() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(DSN)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

