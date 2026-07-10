# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable

from .common import Pri
from .expression import Expression, Arguments


def get(f: Callable[[Any, Any, Any, Any], Any]) -> Callable[[Any, Any, Any, Any], Any]:
    def run(self: Any, vm: Any, left: Any, right: Any) -> Any:
        return f(self, vm, vm.get(left), vm.get(right))

    return run


class Tracker(type):
    def __new__(
        self, name: str, bases: tuple[type, ...], attrs: dict[str, Any]
    ) -> type:
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

        cls = type.__new__(self, name, bases, attrs)
        typed_cls: Any = cls

        if "run" in dir(typed_cls):
            typed_cls.can_run = True

        if "get" in dir(typed_cls):
            typed_cls.can_get = True

        if "set" in dir(typed_cls):
            typed_cls.can_set = True

        if "fill_left" in dir(typed_cls):
            typed_cls.can_fill_left = True

        if "fill_right" in dir(typed_cls):
            typed_cls.can_fill_right = True

        return typed_cls

    def __init__(
        cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]
    ) -> None:
        if bases:
            base: Any = bases[-1]
            base.add(cls, name, attrs)


class InvalidOperation(Exception):
    pass


class Parent(metaclass=Tracker):
    @classmethod
    def add(cls, sub: type, name: str, attrs: dict[str, Any]) -> None:
        if "token" in attrs:
            name = attrs["token"]

        if name and not cls == Parent:
            cls.tokens[name] = sub

    can_run = False
    can_get = False
    can_set = False
    token = ""
    tokens: dict[str, type] = {}
    absorbs: tuple[type[Any], ...] = ()
    arg: Any = None

    # used for evaluation order inside expressions
    priority = Pri.INVALID

    def absorb(self, token: Any) -> None:
        if isinstance(token, Expression):
            flat = token.flatten()
            for typ in self.absorbs:
                if isinstance(flat, typ):
                    token = flat

        self.arg = token
        self.absorbs = ()

    def __lt__(self, token: object) -> Any:
        other = getattr(token, "priority", None)
        if other is None:
            return NotImplemented
        return self.priority < other

    def __gt__(self, token: object) -> Any:
        other = getattr(token, "priority", None)
        if other is None:
            return NotImplemented
        return self.priority > other

    def __eq__(self, token: object) -> Any:
        other = getattr(token, "priority", None)
        if other is None:
            return NotImplemented
        return self.priority == other

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return repr(self.token)


class Stub:
    @classmethod
    def add(cls, sub: type, name: str, attrs: dict[str, Any]) -> None:
        pass


class Token(Parent):
    tokens: dict[str, type] = {}

    def run(self, vm: Any) -> Any:
        raise NotImplementedError

    def __repr__(self) -> str:
        if self.arg:
            return "%s %s" % (repr(self.token), repr(self.arg))
        else:
            return repr(self.token)


class StubToken(Token, Stub):
    def run(self, vm: Any) -> None:
        pass


class Variable(Parent):
    priority = Pri.NONE
    tokens: dict[str, type] = {}

    def get(self, vm: Any) -> Any:
        raise NotImplementedError


class Function(Parent):
    priority = Pri.NONE
    tokens: dict[str, type] = {}

    absorbs = (Arguments,)

    @classmethod
    def add(cls, sub: type, name: str, attrs: dict[str, Any]) -> None:
        if "token" in attrs:
            name = attrs["token"]

        if name:
            name += "("
            cls.tokens[name] = sub

    def __init__(self) -> None:
        if self.can_run:
            self.priority = Pri.INVALID

        Parent.__init__(self)

    def get(self, vm: Any) -> Any:
        return self.call(vm, vm.get(self.arg))

    def call(self, vm: Any, args: Any) -> Any:
        raise NotImplementedError

    def __repr__(self) -> str:
        if self.arg:
            return "%s%s" % (repr(self.token), repr(self.arg).replace("A", "", 1))
        else:
            return "%s()" % repr(self.token)


class StubFunction(Function, Stub):
    def call(self, vm: Any, args: Any) -> None:
        pass
