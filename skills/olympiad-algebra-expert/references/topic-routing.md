# Topic Routing

Choose one primary module by the proof mechanism, not by surface keywords.

| Module | Strong signals | Route notes |
| --- | --- | --- |
| Functional equations | substitutions, injectivity, surjectivity, iteration, orbit constraints | Use `algebra-iteration-proof` only when repeated application is central |
| Inequalities | extremal bounds, convexity, means, Cauchy, Jensen, smoothing, majorization | Track signs and equality conditions as explicit obligations |
| Polynomials | roots, coefficients, interpolation, divisibility, Vieta, irreducibility | Separate identities from claims about roots or degree |
| Recurrences and sequences | induction, telescoping, monotonicity, boundedness, closed forms | Keep base cases and index domains explicit |
| Complex algebra | roots of unity, modulus/argument, polynomial roots | Record whether an order argument is illegal over `C` |
| Discrete algebra | floors, ceilings, integer-valued expressions, finite cases | Separate real inequalities from integrality steps |

Assign secondary modules when the proof genuinely combines mechanisms. If the
decisive step is modular arithmetic, graph counting, or a geometric
configuration, route to the corresponding domain instead.
