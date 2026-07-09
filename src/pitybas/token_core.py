# -*- coding: utf-8 -*-
from .common import Pri
from .expression import Expression, Arguments


def get(f):
    def run(self, vm, left, right):
        return f(self, vm, vm.get(left), vm.get(right))

    return run


class Tracker(type):
    def __new__(self, name, bases, attrs):
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

    def __init__(cls, name, bases, attrs):
        if bases:
            bases[-1].add(cls, name, attrs)


class InvalidOperation(Exception):
    pass


class Parent(metaclass=Tracker):
    @classmethod
    def add(cls, sub, name, attrs):
        if "token" in attrs:
            name = attrs["token"]

        if name and not cls == Parent:
            cls.tokens[name] = sub

    can_run = False
    can_get = False
    can_set = False
    absorbs = ()
    arg = None

    # used for evaluation order inside expressions
    priority = Pri.INVALID

    def absorb(self, token):
        if isinstance(token, Expression):
            flat = token.flatten()
            for typ in self.absorbs:
                if isinstance(flat, typ):
                    token = flat

        self.arg = token
        self.absorbs = ()

    def __lt__(self, token):
        try:
            return self.priority < token.priority
        except AttributeError:
            return NotImplemented

    def __gt__(self, token):
        try:
            return self.priority > token.priority
        except AttributeError:
            return NotImplemented

    def __eq__(self, token):
        try:
            return self.priority == token.priority
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return repr(self.token)


class Stub:
    @classmethod
    def add(cls, sub, name, attrs):
        pass


class Token(Parent):
    tokens = {}

    def run(self, vm):
        raise NotImplementedError

    def __repr__(self):
        if self.arg:
            return "%s %s" % (repr(self.token), repr(self.arg))
        else:
            return repr(self.token)


class StubToken(Token, Stub):
    def run(self, vm):
        pass


class Variable(Parent):
    priority = Pri.NONE
    tokens = {}

    def get(self, vm):
        raise NotImplementedError


class Function(Parent):
    priority = Pri.NONE
    tokens = {}

    absorbs = (Arguments,)

    @classmethod
    def add(cls, sub, name, attrs):
        if "token" in attrs:
            name = attrs["token"]

        if name:
            name += "("
            cls.tokens[name] = sub

    def __init__(self):
        if self.can_run:
            self.priority = Pri.INVALID

        Parent.__init__(self)

    def get(self, vm):
        return self.call(vm, vm.get(self.arg))

    def call(self, vm, args):
        raise NotImplementedError

    def __repr__(self):
        if self.arg:
            return "%s%s" % (repr(self.token), repr(self.arg).replace("A", "", 1))
        else:
            return "%s()" % repr(self.token)


class StubFunction(Function, Stub):
    def call(self, vm, args):
        pass
