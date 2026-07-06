# TODO
 
## Behavioral gaps (likely to cause silent wrong results)

Tilde (~) encodes as a negation token in .8xp, but pitybas is missing a token
for this.

## Angle and complex-number related gaps (missing tokens/features)

DMS (degrees-minutes-seconds) notation — TI-BASIC allows angle literals like
30°15'20" and a ►DMS conversion. pitybas doesn't tokenize the ' (minutes)
symbol, and the " (seconds) symbol would collide with pitybas's existing
string-quote token, so any program using DMS literals fails to parse.

Polar/rectangular conversions — R►Pr(, R►Pθ(, P►Rx(, P►Ry(, and Angle( are
angle-mode-dependent TI-BASIC functions with no equivalent in pitybas at all.

►Polar / re^θi complex display mode — depends on complex-number support (a
literal `i` token, complex arithmetic) that pitybas doesn't really have;
Angle( and ►Polar on complex numbers would need that foundation first.

## Runtime behavior

getKey in the simple backend — Core to every game loop in the document. Raising NotImplementedError means the default backend can't run any real-time program at all. Even returning 0
unconditionally would be better than crashing.
