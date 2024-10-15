from abc import abstractmethod
from typing import Callable, Any, TypeVar

ExecutorResultT = TypeVar("ExecutorResultT")


class AbstractExecutor:
    _q_size: int = 500
    _target: Callable[..., ExecutorResultT]
    _target_args: tuple[Any, ...]
    _target_kwargs: dict[Any, Any]
    _name: str | None = "default name"

    def __init__(self, target: Callable[..., ExecutorResultT], *target_args, **target_kwargs):  # TODO config
        self._target = target
        self._target_args = target_args
        self._target_kwargs = target_kwargs

    def configure(self, q_size: int):
        self._q_size = q_size

    def set_name(self, name: str):
        self._name = name

    def get_q_size(self) -> int:
        return self._q_size

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def __repr__(self):
        pass
