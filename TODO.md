# TODO
 
## Behavioral gaps (likely to cause silent wrong results)

Element-wise list operations — On a real calculator, arithmetic and most math functions apply element-wise to lists: {1,2,3}+10 → {11,12,13}, abs(∟VX) negates each velocity. This is
extremely common in games. pitybas's MathExprFunction subclasses call Python's scalar abs()/int()/fPart() etc., which will error or misbehave on a Python list. Worth verifying — this could
be silently broken for a wide class of programs.

Fix N not wired to Disp — Fix sets vm.fixed but Disp calls vm.disp_round() only for the return value display, not for all output paths. A program using Fix 2 to control decimal places
probably doesn't get the right output.

Trig mode (Degree/Radian) — pitybas always uses radians. Any program doing angle math in degrees (common in physics/geometry games) will produce wrong results with no error.

## Missing commands worth adding

IS>( and DS<( — "Increment and skip if greater / Decrement and skip if less." These are TI-BASIC's only native loop-counter shortcuts and occasionally used in tight loops. Unusual enough
that most Python TI-BASIC implementations miss them.

ClrList — Empties a named list without deleting it. Different from DelVar (which removes the variable entirely). Simple to add.

toString( — TI-84+ only, converts a number to its string representation. Needed for any program that builds display strings containing numbers.

Archive/Unarchive as no-ops — Right now a program that calls Archive ∟SAVE crashes. Stubbing them out silently is the right behavior for a desktop interpreter and unblocks any save-game
program that uses them.

## Runtime behavior

getKey in the simple backend — Core to every game loop in the document. Raising NotImplementedError means the default backend can't run any real-time program at all. Even returning 0
unconditionally would be better than crashing.

Undefined variable defaulting to 0 — On a real calculator, reading an unset variable raises ERR:UNDEFINED. pitybas returns 0 silently. This masks bugs: a program with a typo in a variable
name will silently compute wrong values instead of failing visibly. An optional strict mode would help during development.

L1–L6 are the six built-in named lists on every TI-83/84, accessed via [2nd][1]–[2nd][6], and the overwhelming majority of online TI-BASIC programs and tutorials write
them with uppercase L. Any program copied from a guide that uses L1 would silently misparse — the parser would consume L as the real variable, then 1 as the number 1, producing implied
multiplication (L * 1) with no error. The current design already accepts lowercase l as an ASCII substitute for ∟, which is a deliberate choice that sidesteps the ambiguity: uppercase L is also a valid real variable, so L1 is genuinely ambiguous in flat ASCII. That's a defensible reason for the current behavior. The fix would be a one-line change in the parser's elif char in u'l∟' check — add L to the recognized prefixes but only when the next character is a digit.

