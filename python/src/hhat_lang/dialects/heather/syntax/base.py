from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Any, Iterable
from enum import StrEnum

from hhat_lang.core.utils.dialect_descriptor import DialectDescriptor


class SymbolTypes(StrEnum):
    VARIABLE = "VARIABLE"
    FUNCTION = "FUNCTION"
    MACRO = "MACRO"


class Assignable:
    type: Any


class AST(ABC):
    _value: Any
    dialect: DialectDescriptor

    @property
    @abstractmethod
    def value(self) -> Any:
        pass


class NullNode(AST):
    nodes: list = []
    _value: str = ".null-node"

    @property
    def value(self):
        return self._value

    def __hash__(self) -> int:
        return hash((self.value, self.dialect))

    def __eq__(self, other: Any) -> bool:
        return True if isinstance(other, NullNode) else False

    def __iter__(self) -> Iterable:
        yield from self.nodes

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class Node(AST):
    nodes: list[AST] | AST

    def __init__(self, value: Any, nodes: list[AST] | AST, dialect: DialectDescriptor):
        self._value = value
        self.nodes = nodes
        if isinstance(dialect, DialectDescriptor):
            self.dialect = dialect
        else:
            raise ValueError("dialect must be a DialectDescriptor instance.")

    @property
    def value(self) -> Any:
        return self._value

    def __hash__(self) -> int:
        return hash((self.value, self.nodes, self.dialect))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Node):
            return (
                self.value == other.value
                and self.nodes == other.nodes
                and self.dialect == other.dialect
            )
        return False

    def __getitem__(self, item: int) -> Any:
        return self.nodes[item]

    def __iter__(self) -> Iterable:
        yield from self.nodes

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}|{self.dialect}|({' '.join(str(k) for k in self)})"


class Terminal(AST):
    _value: str

    def __init__(self, value: str, dialect: DialectDescriptor):
        self._value = value
        if isinstance(dialect, DialectDescriptor):
            self.dialect = dialect
        else:
            raise ValueError("dialect must be a DialectDescriptor instance.")

    @property
    def value(self) -> str:
        return self._value

    def __hash__(self) -> int:
        return hash((self.value, self.dialect))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Terminal):
            return self.value == other.value and self.dialect == other.dialect
        return False

    def __repr__(self) -> str:
        return f"{self.value}|{self.dialect}|"


class Symbol(Terminal):
    is_generic: bool = False

    def __init__(self, value: str, is_generic: bool, dialect: DialectDescriptor):
        self.is_generic = is_generic
        super().__init__(value, dialect)

    @property
    def value(self) -> str:
        return self._value

    def __hash__(self) -> int:
        return hash((self.value, self.is_generic, self.dialect))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return (
                self.value == other.value
                and self.is_generic == other.is_generic
                and self.dialect == other.dialect
            )
        return False

    def _generic_mark(self) -> str:
        return "?" if self.is_generic else ""

    def __repr__(self) -> str:
        return f"{self._generic_mark()}{self.value}|{self.dialect}|"


class CSymbol(Symbol):
    pass

class QSymbol(Symbol):
    pass


class Literal(Terminal, Assignable):
    type: str

    def __new__(cls, value: Any, lit_type: str, dialect: DialectDescriptor):
        if "array" in lit_type:
            return CompositeLiteral(value, lit_type, dialect)
        literal = super().__new__(cls)
        literal.type = lit_type
        literal._value = value
        if isinstance(dialect, DialectDescriptor):
            literal.dialect = dialect
            return literal
        else:
            raise ValueError("dialect must be a DialectDescriptor instance.")

    def __init__(self, value: Any, lit_type: str, dialect: DialectDescriptor):
        self.type = f"@{lit_type[3:]}" if lit_type.startswith("q__") else lit_type
        super().__init__(value, dialect)

    def __hash__(self) -> int:
        return hash((self.value, self.type, self.dialect))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Literal):
            return (
                self.value == other.value
                and self.type == other.type
                and self.dialect == other.dialect
            )
        return False

    def __repr__(self) -> str:
        return f"{self.value}<{self.type}>|{self.dialect}|"


class CompositeLiteral(Node, Assignable):
    type: str

    def __init__(self, value: list[Any], lit_type: str, dialect: DialectDescriptor):
        self.type = f"@{lit_type[3:]}" if lit_type.startswith("q__") else lit_type
        super().__init__(".array", value, dialect)

    def __hash__(self) -> int:
        return hash((self.value, self.type, self.dialect))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, CompositeLiteral):
            return (
                self.value == other.value
                and self.type == other.type
                and self.dialect == other.dialect
            )
        return False

    def __repr__(self) -> str:
        return f"({' '.join(str(k) for k in self)})<{self.type}>|{self.dialect}|"



class FnArgId(Symbol):
    def __init__(self, arg: Symbol):
        super().__init__(arg.value, arg.is_generic, arg.dialect)


class FnArgType(Symbol):
    def __init__(self, arg: Symbol):
        super().__init__(arg.value, arg.is_generic, arg.dialect)


class FnArgItem:
    def __init__(self, arg_id: Symbol, arg_type: Symbol):
        self.arg_id = FnArgId(arg_id)
        self.arg_type = FnArgType(arg_type)

    def __repr__(self) -> str:
        return f"({self.arg_id}:{self.arg_type})"
