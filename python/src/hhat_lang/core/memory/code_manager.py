from __future__ import annotations

from typing import Any, Generic, Iterator, TypeVar

from hhat_lang.core.fn_system.base import BaseFunctionData
from hhat_lang.core.type_system import FullName
from hhat_lang.core.type_system.base import BaseDataType

T = TypeVar("T")


class CodeReference(Generic[T]):
    """
    Stores reference for types and functions that are used in the program.
    """

    _ref: dict[FullName, T] = dict()

    def add(self, name: FullName, value: T) -> None:
        if isinstance(name, FullName):
            self._ref[name] = value
        else:
            raise ValueError(f"name must be a FullName; got {name} ({type(name)})")

    def get(self, name: FullName) -> T:
        return self._ref[name]

    def __getitem__(self, name: FullName) -> T:
        return self.get(name)

    def __setitem__(self, name: FullName, value: T) -> None:
        return self.add(name, value)

    def __contains__(self, name: FullName) -> bool:
        return name in self._ref

    def __iter__(self) -> Iterator:
        yield from self._ref.items()

    def names(self) -> Iterator[FullName]:
        yield from self._ref.keys()

    def items(self) -> Iterator:
        yield from self._ref.items()

    def view(self) -> str:
        res = "#CodeReference\n  "
        res += "\n  ".join(f"{k}:{v}" for k, v in self._ref.items())
        res += "\n" + "-" * 40 + "\n#.\n"
        return res

    def __repr__(self) -> str:
        return f"CodeRef({' '.join(f'{k}:{v}' for k, v in self._ref.items())})"


class CodeManager:
    _type_ref: CodeReference[BaseDataType]
    _fn_ref: CodeReference[BaseFunctionData]

    def __init__(self):
        self._type_ref = CodeReference()
        self._fn_ref = CodeReference()

    def add_type(self, name: FullName, body: BaseDataType) -> None:
        self._type_ref.add(name, body)

    def get_type(self, name: FullName) -> BaseDataType:
        return self._type_ref.get(name)

    def add_fn(self, name: FullName, body: BaseFunctionData) -> None:
        self._fn_ref.add(name, body)

    def get_fn(self, name: FullName) -> BaseFunctionData:
        return self._fn_ref.get(name)

    def find_name(self, name: FullName) -> Any:
        if name in self._type_ref:
            return self._type_ref[name]
        if name in self._fn_ref:
            return self._fn_ref[name]
        raise ValueError(
            f"{name} not found in type or function references for this code"
        )
