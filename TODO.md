# TODO
 
## Behavioral gaps (likely to cause silent wrong results)

Trig mode (Degree/Radian) — pitybas always uses radians. Any program doing angle math in degrees (common in physics/geometry games) will produce wrong results with no error.

Tilde (~) encodes as a negation token in .8xp, but pitybas is missing a token
for this.

## Runtime behavior

getKey in the simple backend — Core to every game loop in the document. Raising NotImplementedError means the default backend can't run any real-time program at all. Even returning 0
unconditionally would be better than crashing.
