from collections import defaultdict
import datetime
import decimal
import os
import time
import traceback
from typing import Any, Iterator, List, Optional, Tuple, Type

from .parse import Parser, ParseError
from .tokens import EOF, Value, REPL
from .common import ExecutionError, StopError, ReturnError
from .graph import GraphState

from pitybas.io.base import IOBase
from pitybas.io.simple import IO
from .expression import Base


class Interpreter(object):
    @classmethod
    def from_string(cls, string: str, *args: Any, **kwargs: Any) -> "Interpreter":
        code = Parser(string).parse()
        return Interpreter(code, *args, **kwargs)

    @classmethod
    def from_file(cls, filename: str, *args: Any, **kwargs: Any) -> "Interpreter":
        string = open(filename, "r", encoding="utf8").read()
        vm = Interpreter.from_string(string, *args, **kwargs)
        vm.name = os.path.basename(filename)
        return vm

    def __init__(
        self,
        code: List[List[Any]],
        history: int = 10,
        io: Optional[Type[IOBase]] = None,
        name: Optional[str] = None,
        strict: bool = False,
    ) -> None:
        if not io:
            io = IO
        self.io = io(self)

        self.name = name
        self.code = code
        self.code.append([EOF()])
        self.line = 0
        self.col = 0
        self.expression = None
        self.blocks: List[Any] = []
        self.running: List[Tuple[int, int, Any]] = []
        self.history: List[Tuple[int, int, Any]] = []
        self.hist_len = history
        self.strict = strict

        self.vars: dict = {}
        self.lists: defaultdict = defaultdict(list)
        self.matrix: dict = {}
        self.fixed = -1
        self.degree_mode = False
        self.graph = GraphState()

        # date/time clock: real wall-clock time offset by this amount, so
        # setDate(/setTime( can rewrite the "current" date/time without
        # touching the host system clock
        self.clock_offset = datetime.timedelta()
        self.date_fmt = 1
        self.time_fmt = 12

        self.serial: float = 0
        self.repl_serial = 0

    def cur(self) -> Any:
        return self.code[self.line][self.col]

    def inc(self) -> Any:
        self.col += 1
        if self.col >= len(self.code[self.line]):
            self.col = 0
            return self.inc_row()

        return self.cur()

    def inc_row(self) -> Any:
        self.line = min(self.line + 1, len(self.code) - 1)
        self.expression = None
        return self.cur()

    def get_var(self, var: str, default: Any = None) -> Any:
        if var not in self.vars:
            if self.strict:
                raise ExecutionError("ERR:UNDEFINED")
            if default is not None:
                return default
        return self.vars[var]

    def set_var(self, var: str, value: Any) -> Any:
        if isinstance(value, (Value, Base)):
            value = value.get(self)

        self.vars[var] = value
        return value

    def get_matrix(self, name: str) -> Any:
        return self.matrix[name]

    def set_matrix(self, name: str, value: Any) -> None:
        self.matrix[name] = value

    def get_list(self, name: str) -> Any:
        return self.lists[name]

    def set_list(self, name: str, value: Any) -> None:
        self.lists[name] = value

    def push_block(self, block: Any = None) -> None:
        if not block and self.running:
            block = self.running[-1]

        if block:
            self.blocks.append(block)
        else:
            raise ExecutionError("tried to push an invalid block to the stack")

    def pop_block(self) -> Any:
        if self.blocks:
            return self.blocks.pop()
        else:
            raise ExecutionError("tried to pop an empty block stack")

    def find(self, *types: type, **kwargs: Any) -> Iterator[Tuple[int, int, Any]]:
        if "wrap" in kwargs:
            wrap = kwargs["wrap"]
        else:
            wrap = False

        if "pos" in kwargs:
            pos = kwargs["pos"]
        else:
            pos = self.line

        def y(i: int) -> Optional[Tuple[int, int, Any]]:
            line = self.code[i]
            if line:
                cur = line[0]
                if isinstance(cur, types):
                    return i, 0, cur
            return None

        for i in range(pos, len(self.code)):
            ret = y(i)
            if ret:
                yield ret

        if wrap:
            for i in range(0, pos):
                ret = y(i)
                if ret:
                    yield ret

    def goto(self, row: int, col: int) -> None:
        if row >= 0 and row < len(self.code) and col >= 0 and col < len(self.code[row]):
            self.line = row
            self.col = col
        else:
            raise ExecutionError("cannot goto (%i, %i)" % (row, col))

    def get(self, *var: Any) -> Any:
        ret = []
        for v in var:
            val = v.get(self)
            if isinstance(val, complex):
                if not val.imag:
                    val = val.real

            if isinstance(val, (float)):
                # TODO: perhaps limit precision here
                i = int(val)
                if val == i:
                    val = i

            ret.append(val)

        if len(ret) == 1:
            return ret[0]

        return ret

    def disp_round(self, num: Any) -> Any:
        if not isinstance(num, (decimal.Decimal, int, float, complex)):
            return num

        if self.fixed < 0:
            return num
        else:
            # round() rejects complex; pre-existing behavior, not addressed here.
            return round(num, self.fixed)  # type: ignore[arg-type]

    def run(self, cur: Any) -> None:
        self.history.append((self.line, self.col, cur))
        self.history = self.history[-self.hist_len :]

        cur.line, cur.col = self.line, self.col

        if cur.can_run:
            self.running.append((self.line, self.col, cur))
            self.inc()
            cur.run(self)
            self.running.pop()
        elif cur.can_get:
            self.inc()
            self.set_var("Ans", cur.get(self))
            self.serial = time.time()
        else:
            raise ExecutionError("cannot seem to run token: %s" % cur)

    def execute(self) -> None:
        with self.io:
            try:
                while not isinstance(self.cur(), EOF):
                    cur = self.cur()
                    self.run(cur)
            except StopError as e:
                if e.args:
                    print()
                    print("Stopped:", e.args[0])
            except ReturnError as e:
                if e.args:
                    print()
                    print("Returned:", e.args[0])

    def print_tokens(self) -> None:
        for line in self.code:
            print((", ".join(repr(n) for n in line)).replace("u'", "'"))

    def print_ast(
        self,
        start: int = 0,
        end: Optional[int] = None,
        highlight: Optional[int] = None,
    ) -> None:
        if end is None:
            end = len(self.code)

        for i in range(max(start, 0), min(end, len(self.code))):
            line = self.code[i]
            if highlight is not None and i == highlight - 1:
                print(">>>> {}".format(line))
            else:
                print("{:3}: {}".format(i, line))

    def print_stacktrace(
        self, num: Optional[int] = None, vardump: bool = False
    ) -> None:
        if not num:
            num = self.hist_len

        if self.name:
            print("-===[ Dumping {} ]===-".format(self.name))

        if self.history:
            print()
            print("-===[ Stacktrace ]===-")

        for row, col, cur in self.history[-num:]:
            print(
                ("[{}, {}]:".format(row, col)).ljust(9),
                repr(cur).replace("u'", "").replace("'", ""),
            )

        if self.history:
            print()

        print("-===[ Code (row {}, col {}) ]===-".format(self.line, self.col))
        h = num // 2
        self.print_ast(self.line - h, self.line + h, highlight=self.line)
        print()

        if vardump:
            print()
            print("-===[ Variable Dump ]===-")
            import pprint

            pprint.pprint(self.vars)
            print()

    def run_prgm(self, name: str) -> None:
        for ref in os.listdir("."):
            if ref.endswith(".bas"):
                test = ref.rsplit(".", 1)[0]
                if test.lower() == name.lower():
                    sub = Interpreter.from_file(ref)
                    sub.execute()
                    return
        raise ExecutionError("prgm{} not found".format(name))


class Repl(Interpreter):
    def __init__(self, code: Optional[List[List[Any]]] = None, **kwargs: Any) -> None:
        super(Repl, self).__init__(code if code is not None else [], **kwargs)
        self.code.insert(-2, [REPL()])

    def execute(self) -> None:
        while not isinstance(self.cur(), EOF):
            try:
                super(Repl, self).execute()
            except ParseError as e:
                print(e)
            except Exception:
                print(traceback.format_exc())
