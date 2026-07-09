try:
    import readline
except ImportError:
    pass

from pitybas.parse import Parser
from pitybas.common import ParseError
from pitybas.io.base import IOBase


class IO(IOBase):
    def clear(self):
        print('-'*16)

    def input(self, msg, is_str=False):
        while True:
            try:
                if msg:
                    print(msg, end=' ')

                line = input()
                if not is_str:
                    val = Parser.parse_line(self.vm, line)
                else:
                    val = line

                return val
            except ParseError:
                print('ERR:DATA')
                print()

    def getkey(self):
        raise NotImplementedError

    def output(self, x, y, msg):
        print(msg)

    def disp(self, msg=''):
        print(msg)

    def pause(self, msg=''):
        if msg: self.disp(msg)
        self.input('[press enter]', True)

    def menu(self, menu):
        # menu is a tuple of (title, [(desc, label)]) -- title/desc are
        # already-evaluated display strings; label is a raw, unevaluated
        # token for Goto to resolve.
        lookup = []
        while True:
            i = 1

            for title, entries in menu:
                print('-[ %s ]-' % title)
                for name, label in entries:
                    print('%i: %s' % (i, name))
                    lookup.append(label)
                    i += 1

            choice = self.input('choice?', True)
            print()
            if choice.isdigit() and 0 < int(choice) <= len(lookup):
                label = lookup[int(choice)-1]
                return label
            else:
                print('invalid choice')
