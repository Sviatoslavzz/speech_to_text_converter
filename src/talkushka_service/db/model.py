import enum
from datetime import datetime

from sqlalchemy import Enum as pgEnum
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class Privilege(enum.Enum):
    admin = "admin"
    helpdesk = "helpdesk"
    user = "user"


class SubscriptionType(enum.Enum):
    god = "god"
    week = "week"
    month = "month"
    year = "year"


class User(Base):
    # __table_args__ = {"schema": settings.SCHEMA_RESULT_NAME}
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, unique=True,
                                       server_default=text("gen_random_uuid()"))
    user_id: Mapped[int]
    chat_id: Mapped[int]
    username: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))
    subscription_uuid: Mapped[UUID | None]
    privilege: Mapped[Privilege] = mapped_column(pgEnum(Privilege, name="privilege_enum"))


class Subscription(Base):
    # __table_args__ = {"schema": settings.SCHEMA_RESULT_NAME}
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, unique=True,
                                       server_default=text("gen_random_uuid()"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=text("TIMEZONE('utc', now())"))
    ends_at: Mapped[datetime | None]
    type: Mapped[SubscriptionType]


class Payment(Base):
    # __table_args__ = {"schema": settings.SCHEMA_RESULT_NAME}
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, unique=True,
                                       server_default=text("gen_random_uuid()"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=text("TIMEZONE('utc', now())"))
    amount: Mapped[float]
    method: Mapped[str]
    link: Mapped[str]
    type: Mapped[SubscriptionType]


class Promocode(Base):
    # __table_args__ = {"schema": settings.SCHEMA_RESULT_NAME}
    __tablename__ = "promocode"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))
    total_use: Mapped[int]
    actual_use: Mapped[int]
    type: Mapped[SubscriptionType]


class Stats(Base):
    # __table_args__ = {"schema": settings.SCHEMA_RESULT_NAME}
    __tablename__ = "stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_uuid: Mapped[UUID]
    date: Mapped[datetime]
    video: Mapped[int]
    audio: Mapped[int]
    subtitle: Mapped[int]
    transcription: Mapped[int]
