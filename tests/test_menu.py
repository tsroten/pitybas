from pitybas.interpret import Interpreter
from pitybas.io.scripted import ScriptedIO


def make_menu_vm(source, menu_fn):
    class RecordingIO(ScriptedIO):
        def menu(self, menu):
            return menu_fn(self, menu)

    vm = Interpreter.from_string(source, io=lambda vm: RecordingIO(vm))
    vm.execute()
    return vm


def test_menu_title_and_descriptions_are_evaluated_display_strings():
    """IO.menu() must receive plain, already-evaluated display text for
    the title and each option's description -- not a raw parse-tree
    token/Expression. Comparing an unevaluated Expression directly to a
    string silently never matches (no error), which is an easy way to
    write a menu-driving bot that looks like it works but always falls
    through to a default case."""
    captured = {}

    def menu_fn(io, menu):
        for title, entries in menu:
            captured["title"] = title
            captured["descs"] = [desc for desc, _ in entries]
        return entries[0][1]

    make_menu_vm(
        'Menu("TITLE","OPT1",A,"OPT2",B)\nDisp "no\nLbl A\nDisp "yes',
        menu_fn,
    )

    assert captured["title"] == "TITLE"
    assert captured["descs"] == ["OPT1", "OPT2"]


def test_menu_label_stays_an_unevaluated_token_for_goto():
    """Unlike title/description, each option's label must stay a raw,
    unevaluated token: Goto.goto()/Lbl.guess_label() need its parse-tree
    shape (Value/Variable/Expression), not a plain string, to resolve the
    jump target."""
    vm = make_menu_vm(
        'Menu("TITLE","OPT1",A,"OPT2",B)\nDisp "no\nLbl A\nDisp "yes',
        lambda io, menu: next(iter(menu))[1][0][1],
    )
    assert vm.io.disps == ["yes"]


def test_menu_choosing_second_option_reaches_its_label():
    program = (
        'Menu("TITLE","OPT1",A,"OPT2",B)\n'
        'Disp "no\n'
        "Lbl A\n"
        'Disp "wrong\n'
        "Lbl B\n"
        'Disp "right'
    )
    vm = make_menu_vm(
        program,
        lambda io, menu: next(iter(menu))[1][1][1],
    )
    assert vm.io.disps == ["right"]
