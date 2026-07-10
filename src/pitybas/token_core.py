# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable, Dict, Tuple, Type, TYPE_CHECKING

from .common import Pri
from .expression import Expression, Arguments

if TYPE_CHECKING:
    from .interpret import Interpreter


def get(f: Callable[..., Any]) -> Callable[..., Any]:
    def run(self: "Parent", vm: "Interpreter", left: Any, right: Any) -> Any:
        return f(self, vm, vm.get(left), vm.get(right))

    return run


class Tracker(type):
    def __new__(
        mcs, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]
    ) -> "Tracker":
        if "token" not in attrs:
            attrs["token"] = name

        attrs.update(
            {
                "can_run": False,
                "can_get": False,
                "can_set": False,
                "can_fill_left": False,
                "can_fill_right": False,
            }
        )

        # The object created here is a plain class, not an instance of
        # Tracker itself -- treat it as Any rather than fight mypy's
        # metaclass-return inference for the attrs set dynamically below.
        cls: Any = type.__new__(mcs, name, bases, attrs)

        if "run" in dir(cls):
            cls.can_run = True

        if "get" in dir(cls):
            cls.can_get = True

        if "set" in dir(cls):
            cls.can_set = True

        if "fill_left" in dir(cls):
            cls.can_fill_left = True

        if "fill_right" in dir(cls):
            cls.can_fill_right = True

        return cls

    def __init__(
        cls, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]
    ) -> None:
        if bases:
            bases[-1].add(cls, name, attrs)  # type: ignore[attr-defined]


class InvalidOperation(Exception):
    pass


class Parent(metaclass=Tracker):
    @classmethod
    def add(cls, sub: Type["Parent"], name: str, attrs: Dict[str, Any]) -> None:
        if "token" in attrs:
            name = attrs["token"]

        if name and not cls == Parent:
            cls.tokens[name] = sub

    can_run: bool = False
    can_get: bool = False
    can_set: bool = False
    can_fill_left: bool = False
    can_fill_right: bool = False
    absorbs: Tuple[Type[Any], ...] = ()
    arg: Any = None
    token: str = ""

    # tokens is populated per-registry by Token/Variable/Function below;
    # declared here so Parent.add() (shared by all three) type-checks.
    tokens: Dict[str, Type["Parent"]] = {}

    # used for evaluation order inside expressions
    priority: int = Pri.INVALID

    def absorb(self, token: Any) -> None:
        if isinstance(token, Expression):
            flat = token.flatten()
            for typ in self.absorbs:
                if isinstance(flat, typ):
                    token = flat

        self.arg = token
        self.absorbs = ()

    def __lt__(self, token: Any) -> bool:
        try:
            return self.priority < token.priority
        except AttributeError:
            return NotImplemented

    def __gt__(self, token: Any) -> bool:
        try:
            return self.priority > token.priority
        except AttributeError:
            return NotImplemented

    def __eq__(self, token: Any) -> bool:
        try:
            return self.priority == token.priority
        except AttributeError:
            return NotImplemented

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return repr(self.token)


class Stub:
    @classmethod
    def add(cls, sub: Type[Any], name: str, attrs: Dict[str, Any]) -> None:
        pass


class Token(Parent):
    tokens: Dict[str, Type["Parent"]] = {}

    def run(self, vm: "Interpreter") -> Any:
        raise NotImplementedError

    def __repr__(self) -> str:
        if self.arg:
            return "%s %s" % (repr(self.token), repr(self.arg))
        else:
            return repr(self.token)


class StubToken(Token, Stub):
    def run(self, vm: "Interpreter") -> None:
        pass


class Variable(Parent):
    priority = Pri.NONE
    tokens: Dict[str, Type["Parent"]] = {}

    def get(self, vm: "Interpreter") -> Any:
        raise NotImplementedError


class Function(Parent):
    priority = Pri.NONE
    tokens: Dict[str, Type["Parent"]] = {}

    absorbs: Tuple[Type[Any], ...] = (Arguments,)

    @classmethod
    def add(cls, sub: Type["Parent"], name: str, attrs: Dict[str, Any]) -> None:
        if "token" in attrs:
            name = attrs["token"]

        if name:
            name += "("
            cls.tokens[name] = sub

    def __init__(self) -> None:
        if self.can_run:
            self.priority = Pri.INVALID

        Parent.__init__(self)

    def get(self, vm: "Interpreter") -> Any:
        return self.call(vm, vm.get(self.arg))

    def call(self, vm: "Interpreter", args: Any) -> Any:
        raise NotImplementedError

    def __repr__(self) -> str:
        if self.arg:
            return "%s%s" % (repr(self.token), repr(self.arg).replace("A", "", 1))
        else:
            return "%s()" % repr(self.token)


class StubFunction(Function, Stub):
    def call(self, vm: "Interpreter", args: Any) -> None:
        pass
