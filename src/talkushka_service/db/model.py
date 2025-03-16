import enum
from datetime import datetime

from sqlalchemy import BIGINT, ForeignKeyConstraint, text
from sqlalchemy import Enum as pgEnum
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from talkushka_service.config.settings import settings


class Base(DeclarativeBase):
    type_annotation_map = {
        int: BIGINT,
    }


class Privilege(enum.Enum):
    admin = "admin"
    helpdesk = "helpdesk"
    user = "user"


class SubscriptionType(enum.Enum):
    week = 1
    month = 2
    year = 3
    lifetime = 4


class User(Base):
    __table_args__ = (
        ForeignKeyConstraint(["subscription_id"], [f"{settings.DB_SCHEMA}.subscription.id"]),
        {"schema": settings.DB_SCHEMA}
    )
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    chat_id: Mapped[int]
    username: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))
    subscription_id: Mapped[int | None]
    privilege: Mapped[Privilege] = mapped_column(pgEnum(Privilege, name="privilege_enum"), default=Privilege.user)
    lc: Mapped[str] = mapped_column(server_default="ru")

    user_limit = relationship("UserLimit", back_populates="user", passive_deletes=True)
    payment = relationship("Payment", back_populates="user")


class Subscription(Base):
    __table_args__ = {"schema": settings.DB_SCHEMA}
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=text("TIMEZONE('utc', now())"))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    type: Mapped[SubscriptionType]
    payment_uuid: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True))

    payment = relationship("Payment", back_populates="subscription")


class Payment(Base):
    __table_args__ = (
        ForeignKeyConstraint(["user_id"], [f"{settings.DB_SCHEMA}.user.user_id"]),
        ForeignKeyConstraint(["subscription_id"], [f"{settings.DB_SCHEMA}.subscription.id"]),
        {"schema": settings.DB_SCHEMA}
    )
    __tablename__ = "payment"

    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, unique=True,
                                       server_default=text("gen_random_uuid()"))
    user_id: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=text("TIMEZONE('utc', now())"))
    amount: Mapped[float]
    method: Mapped[str]
    link: Mapped[str | None]
    subscription_id: Mapped[int]

    user = relationship("User", back_populates="payment")
    subscription = relationship("Subscription", back_populates="payment")


class Promocode(Base):
    __table_args__ = {"schema": settings.DB_SCHEMA}
    __tablename__ = "promocode"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("TIMEZONE('utc', now())"))
    total_use: Mapped[int]
    actual_use: Mapped[int] = mapped_column(default=0)
    type: Mapped[SubscriptionType]


class UserLimit(Base):
    __table_args__ = (
        ForeignKeyConstraint(["user_id"], [f"{settings.DB_SCHEMA}.user.user_id"], ondelete="CASCADE"),
        {"schema": settings.DB_SCHEMA}
    )
    __tablename__ = "user_limit"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    user_id: Mapped[int]
    video: Mapped[int] = mapped_column(default=10)
    audio: Mapped[int] = mapped_column(default=30)
    subtitle: Mapped[int] = mapped_column(default=100)
    transcription: Mapped[int] = mapped_column(default=1)

    user = relationship("User", back_populates="user_limit")
