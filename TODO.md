# TODO
 
## Angle and complex-number related gaps (missing tokens/features)

►DMS display conversion — entering DMS literals (30°15'20") now works, but
the separate ►DMS instruction that formats a plain decimal answer as
D°M'S" for display (valid only at the end of a Disp/Pause line, per the
TI-83 Plus/TI-84 Plus guidebook) still has no equivalent. pitybas has no
precedent for a "►"-style display-only conversion (Store just uses a
literal "->" instead of the real STO► glyph), so this needs its own
mechanism in Disp/Pause rather than reusing the DMS literal work.

Polar/rectangular conversions — R►Pr(, R►Pθ(, P►Rx(, P►Ry(, and Angle( are
angle-mode-dependent TI-BASIC functions with no equivalent in pitybas at all.

►Polar / re^θi complex display mode — depends on complex-number support (a
literal `i` token, complex arithmetic) that pitybas doesn't really have;
Angle( and ►Polar on complex numbers would need that foundation first.

## Runtime behavior

getKey in the simple backend — Core to every game loop in the document. Raising NotImplementedError means the default backend can't run any real-time program at all. Even returning 0
unconditionally would be better than crashing.
