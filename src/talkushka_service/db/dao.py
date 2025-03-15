from collections.abc import Callable
from functools import wraps
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, DeclarativeMeta

from talkushka_service.config.settings import DSN
from talkushka_service.db.model import Payment, Privilege, Promocode, Subscription, User, UserLimit

async_session_factory = async_sessionmaker(create_async_engine(DSN), class_=AsyncSession, expire_on_commit=False)


def with_session(func: Callable) -> Callable:
    """
    Async session factory.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        async with async_session_factory() as session:
            try:
                result = await func(*args, session=session, **kwargs)
                await session.commit()
                return result
            except Exception as exc:
                await session.rollback()
                logger.error("Error executing DB operation: {exc}", exc=exc.__repr__())
                return None
            finally:
                await session.close()

    return wrapper


class BaseDAO:
    """
    Base Data Access Object
    """

    __abstract__ = True
    _model = None

    @classmethod
    @with_session
    async def add_by_kwargs(cls, session: AsyncSession, **kwargs) -> "DeclarativeBase":
        new_ins = cls._model(**kwargs)
        session.add(new_ins)
        await session.flush()
        return new_ins

    @classmethod
    @with_session
    async def add(cls, session: AsyncSession, field: DeclarativeMeta) -> None:
        session.add(field)

    @classmethod
    @with_session
    async def add_all(cls, session: AsyncSession, fields: list[DeclarativeMeta]) -> None:
        """
        :param session: passed by decorator
        :param fields: list of new fields in dictionary representation
        """
        session.add_all(fields)

    @classmethod
    @with_session
    async def get_all(cls, session: AsyncSession, **kwargs) -> list["DeclarativeBase"]:
        query = select(cls._model)
        for k, v in kwargs.items():
            query = query.where(getattr(cls._model, k) == v)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    @with_session
    async def get_one_or_none(cls, session: AsyncSession, **kwargs) -> "DeclarativeBase":
        query = select(cls._model)
        for k, v in kwargs.items():
            query = query.where(getattr(cls._model, k) == v)
        result = await session.execute(query)
        return result.scalars().one_or_none()

    @classmethod
    @with_session
    async def delete(cls, session: AsyncSession, field: DeclarativeMeta) -> None:
        """
        :param session: passed by decorator
        :param field: instance of DeclarativeMeta, must be passed as keyword argument 'field=Instance()'
        """
        await session.delete(field)

    @classmethod
    @with_session
    async def delete_many(cls, session: AsyncSession, fields: list[DeclarativeMeta]) -> None:
        """
        :param session: passed by decorator
        :param fields: list of DeclarativeMeta instances, must be passed as keyword argument 'fields=[Instance(),]'
        """
        for field in fields:
            await session.delete(field)

    @classmethod
    @with_session
    async def delete_all_by_filter(cls, session: AsyncSession, **kwargs) -> None:
        query = select(cls._model)
        for k, v in kwargs.items():
            query = query.where(getattr(cls._model, k) == v)
        result = await session.execute(query)
        for ins in result.scalars().all():
            await session.delete(ins)


class UserDAO(BaseDAO):
    _model = User

    @classmethod
    @with_session
    async def update_by_kwargs(cls, session: AsyncSession, **kwargs) -> User:
        query = select(cls._model).where(cls._model.user_id == kwargs["user_id"])
        result = await session.scalars(query)
        instance = result.first()
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await session.flush()
        return instance

    @classmethod
    @with_session
    async def get_helpdesk_and_admin(cls, session: AsyncSession) -> list[User]:
        query = select(cls._model).where(
            cls._model.privilege.in_([Privilege.helpdesk, Privilege.admin]))
        result = await session.scalars(query)
        return result.all()


class SubscriptionDAO(BaseDAO):
    _model = Subscription


class PaymentDAO(BaseDAO):
    _model = Payment


class PromocodeDAO(BaseDAO):
    _model = Promocode


class UserLimitDAO(BaseDAO):
    _model = UserLimit

    @classmethod
    @with_session
    async def decrease_limit_by_user_id(cls, session: AsyncSession, user_id: int, **kwargs) -> UserLimit:
        """
        Decreases limit for a specific parameter passed as keyword argument.
        Example: decrease_limit_by_user_id(user_id=1, video=1) - decreases video limit by 1.
        :param session: passed by decorator
        :param user_id: id of user
        """
        query = select(cls._model).where(cls._model.user_id == user_id)
        result = await session.scalars(query)
        instance = result.first()
        for key, value in kwargs.items():
            curr_value = getattr(instance, key)
            setattr(instance, key, curr_value - value)
        await session.flush()
        return instance
