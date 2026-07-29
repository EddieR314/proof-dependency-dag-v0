# Algebra DAG Human Review Packet v0.2-rc1

This packet records the completed human semantic checks that automatic
validators cannot establish. Mathematical proof review, DAG semantic
review, and mutation realism review have passed for all five artifacts.

## 00q2 (polynomials)

### Automatic Evidence

- Reference target derivable: `True`
- Candidate target derivable: `False`
- Computed First Break: `I5`
- Declared/computed match: `True`
- Mutation checker passed: `True`

These automatic results establish structural consistency only. They do
not establish that the natural-language claims and edges are faithful.

### Facts

| ID | Scope | Kind | Statement |
| --- | --- | --- | --- |
| `F1` | `global` | `given` | n is a positive integer. |
| `F2` | `global` | `given` | f_n and g_n are the polynomials in the problem; g_n is homogeneous of degree 5n. |
| `F3` | `global/necessity` | `assumed` | Assume f_n divides g_n. |
| `F4` | `global/necessity` | `derived` | There is a nonzero polynomial h such that g_n=f_n h. |
| `F5` | `global/necessity/case_gt_one` | `case_assumed` | Assume n>1 inside the contradiction subcase. |
| `F6` | `global/necessity/case_gt_one` | `derived` | For n>1, f_n has nonzero extreme homogeneous components of degrees 2 and 2n. |
| `F7` | `global/necessity/case_gt_one` | `derived` | Let l and u be the lowest and highest nonzero homogeneous degrees of h. |
| `F8` | `global/necessity/case_gt_one` | `derived` | The extreme indices satisfy l<=u. |
| `F9` | `global/necessity/case_gt_one` | `derived` | The nonzero lowest homogeneous component of f_n h has degree l+2. |
| `F10` | `global/necessity/case_gt_one` | `derived` | The nonzero highest homogeneous component of f_n h has degree u+2n. |
| `F11` | `global/necessity/case_gt_one` | `derived` | The lowest-degree comparison gives l+2=5n. |
| `F12` | `global/necessity/case_gt_one` | `derived` | The highest-degree comparison gives u+2n=5n. |
| `F13` | `global/necessity/case_gt_one` | `derived` | l=5n-2. |
| `F14` | `global/necessity/case_gt_one` | `derived` | u=3n. |
| `F15` | `global/necessity/case_gt_one` | `derived` | The extreme-index order forces n<=1. |
| `F16` | `global/necessity/case_gt_one` | `derived` | The assumptions n>1 and n<=1 contradict. |
| `F17` | `global/necessity` | `derived` | Within the divisibility branch, n<=1. |
| `F18` | `global/necessity` | `derived` | Within the divisibility branch, n=1. |
| `F19` | `global` | `derived` | If f_n divides g_n, then n=1. |
| `F20` | `global/sufficiency` | `case_assumed` | Assume n=1 for the sufficiency branch. |
| `F21` | `global/sufficiency` | `constructed` | Define p=x-y, q=y-z, and r=z-x. |
| `F22` | `global/sufficiency` | `derived` | p+q+r=0. |
| `F23` | `global/sufficiency` | `derived` | p^5+q^5+r^5=(5/2)pqr(p^2+q^2+r^2). |
| `F24` | `global/sufficiency` | `derived` | f_1=(1/2)(p^2+q^2+r^2). |
| `F25` | `global/sufficiency` | `derived` | g_1=5pqr f_1. |
| `F26` | `global/sufficiency` | `derived` | f_1 divides g_1. |
| `F27` | `global` | `derived` | If n=1, then f_n divides g_n. |
| `F28` | `global` | `derived` | For positive integers n, f_n divides g_n if and only if n=1. |

### Inferences

| ID | Scope | Rule application | Inputs by premise role | Output |
| --- | --- | --- | --- | --- |
| `I1` | `global/necessity` | Expand polynomial divisibility as a quotient identity | `divisibility=F3` | `F4` |
| `I2` | `global/necessity/case_gt_one` | Identify the degree-2 and degree-2n components of f_n when n>1 | `definitions=F2`; `case=F5` | `F6` |
| `I3` | `global/necessity/case_gt_one` | Choose the lowest and highest nonzero homogeneous parts of h | `quotient=F4` | `F7` |
| `I4` | `global/necessity/case_gt_one` | The lowest nonzero degree does not exceed the highest | `extrema=F7` | `F8` |
| `I5` | `global/necessity/case_gt_one` | The unique lowest product component is F_2 h_l | `decomposition=F6`; `extrema=F7`; `quotient=F4` | `F9` |
| `I6` | `global/necessity/case_gt_one` | The unique highest product component is F_2n h_u | `decomposition=F6`; `extrema=F7`; `quotient=F4` | `F10` |
| `I7` | `global/necessity/case_gt_one` | A nonzero component of a homogeneous polynomial has degree 5n | `definitions=F2`; `lowest=F9` | `F11` |
| `I8` | `global/necessity/case_gt_one` | The highest component also has homogeneous degree 5n | `definitions=F2`; `highest=F10` | `F12` |
| `I9` | `global/necessity/case_gt_one` | Solve l+2=5n | `equation=F11` | `F13` |
| `I10` | `global/necessity/case_gt_one` | Solve u+2n=5n | `equation=F12` | `F14` |
| `I11` | `global/necessity/case_gt_one` | Combine l<=u with the solved extreme degrees | `order=F8`; `lowest_value=F13`; `highest_value=F14` | `F15` |
| `I12` | `global/necessity/case_gt_one` | The assumptions n>1 and n<=1 contradict | `case=F5`; `bound=F15` | `F16` |
| `I13` | `global/necessity/case_gt_one` | Discharge the n>1 contradiction inside the necessity branch | `case=F5`; `contradiction=F16` | `F17` |
| `I14` | `global/necessity` | A positive integer not exceeding 1 equals 1 | `positive_integer=F1`; `bound=F17` | `F18` |
| `I15` | `global/necessity` | Discharge the divisibility assumption as the necessity implication | `divisibility=F3`; `equals_one=F18` | `F19` |
| `I16` | `global/sufficiency` | Introduce p=x-y, q=y-z, r=z-x for n=1 | `case=F20`; `definitions=F2` | `F21` |
| `I17` | `global/sufficiency` | The cyclic differences sum to zero | `differences=F21` | `F22` |
| `I18` | `global/sufficiency` | Apply the fifth-power identity under p+q+r=0 | `sum_zero=F22` | `F23` |
| `I19` | `global/sufficiency` | Rewrite f_1 as half the cyclic squared-difference sum | `definitions=F2`; `differences=F21` | `F24` |
| `I20` | `global/sufficiency` | Combine the two identities to factor g_1 by f_1 | `fifth_identity=F23`; `quadratic_identity=F24`; `definitions=F2` | `F25` |
| `I21` | `global/sufficiency` | An explicit polynomial factorization proves divisibility | `factorization=F25` | `F26` |
| `I22` | `global/sufficiency` | Discharge n=1 as the sufficiency implication | `case=F20`; `divisibility=F26` | `F27` |
| `I23` | `global` | Combine both implications into the exact classification | `necessity=F19`; `sufficiency=F27` | `F28` |

### Controlled Mutation

- Operation: `remove_required_premise`
- Primary site: `F6->I5`
- Injection anchor: `I5`
- Before: `{"input_fact_id": "F6", "consumer_inference_id": "I5", "premise_role": "decomposition", "mathematical_content": "For n>1, f_n has distinct nonzero lowest and highest homogeneous components of degrees 2 and 2n."}`
- After: `{"edge_removed": true, "remaining_claim": "The proof declares F_2 h_l to be the unique nonzero lowest product component without establishing the extreme-degree decomposition of f_n."}`
- Expected First Break: `I5`

### Human Decision

- [ ] Every Fact statement is mathematically correct and atomic enough.
- [ ] Every input edge is genuinely required by the stated rule.
- [ ] No required mathematical premise is absent from the Reference DAG.
- [ ] Scope and source order match the reviewed proof.
- [ ] The mutation introduces exactly one real and plausible primary error.
- [ ] The declared First Break is the earliest invalid inference.

Reviewer: Ruan Haochen (Eddie)

Date: 2026-07-29

DAG semantics: `passed`

Mutation realism: `passed`

Notes:

## 06og (inequalities)

### Automatic Evidence

- Reference target derivable: `True`
- Candidate target derivable: `False`
- Computed First Break: `I8`
- Declared/computed match: `True`
- Mutation checker passed: `True`

These automatic results establish structural consistency only. They do
not establish that the natural-language claims and edges are faithful.

### Facts

| ID | Scope | Kind | Statement |
| --- | --- | --- | --- |
| `F1` | `global` | `given` | n>=2 and all a_i are positive. |
| `F2` | `global` | `constructed` | S=sum a_i, E2=sum_{i<j} a_i a_j, and L is the left side. |
| `F3` | `global` | `derived` | The target is equivalent to 2SL <= nE2 because 2S>0. |
| `F4` | `global` | `derived` | 2SL equals 2E2 plus the residual sum collected by triples. |
| `F5` | `global` | `derived` | For positive a,b,c, 1/a+1/b >= 4/(a+b). |
| `F6` | `global` | `derived` | For each positive triple, 2abc sum_cyc 1/(a+b) <= ab+bc+ca. |
| `F7` | `global` | `derived` | Summing the local triple inequality bounds the residual triple sum. |
| `F8` | `global` | `derived` | Every unordered pair occurs in exactly n-2 unordered triples. |
| `F9` | `global` | `derived` | The pair sum over all triples equals (n-2)E2. |
| `F10` | `global` | `derived` | The residual triple sum is at most (n-2)E2. |
| `F11` | `global` | `derived` | 2SL <= nE2. |
| `F12` | `global` | `derived` | The required inequality holds. |

### Inferences

| ID | Scope | Rule application | Inputs by premise role | Output |
| --- | --- | --- | --- | --- |
| `I1` | `global` | Scale by the positive total sum | `positivity=F1`; `definitions=F2` | `F3` |
| `I2` | `global` | Expand the total sum and regroup by unordered triples | `definitions=F2` | `F4` |
| `I3` | `global` | Apply AM-HM to each reciprocal pair | `positivity=F1` | `F5` |
| `I4` | `global` | Sum three cyclic bounds and multiply by abc | `pair_bound=F5`; `positivity=F1` | `F6` |
| `I5` | `global` | Sum the local inequality over all triples | `local_bound=F6` | `F7` |
| `I6` | `global` | Count how many triples contain a fixed pair | `index_range=F1` | `F8` |
| `I7` | `global` | Convert the triple pair sum to (n-2)E2 | `multiplicity=F8`; `definitions=F2` | `F9` |
| `I8` | `global` | Combine the local bound with pair multiplicity | `summed_bound=F7`; `count_identity=F9` | `F10` |
| `I9` | `global` | Insert the residual estimate into the expansion | `expansion=F4`; `residual_bound=F10` | `F11` |
| `I10` | `global` | Undo the positive scaling | `equivalence=F3`; `scaled_result=F11` | `F12` |

### Controlled Mutation

- Operation: `remove_required_premise`
- Primary site: `F9->I8`
- Injection anchor: `I8`
- Before: `{"fact_id": "F9", "premise_role": "count_identity"}`
- After: `{"edge_removed": true, "remaining_claim": "The proof bounds the residual without using the n-2 pair multiplicity identity."}`
- Expected First Break: `I8`

### Human Decision

- [ ] Every Fact statement is mathematically correct and atomic enough.
- [ ] Every input edge is genuinely required by the stated rule.
- [ ] No required mathematical premise is absent from the Reference DAG.
- [ ] Scope and source order match the reviewed proof.
- [ ] The mutation introduces exactly one real and plausible primary error.
- [ ] The declared First Break is the earliest invalid inference.

Reviewer: Ruan Haochen (Eddie)

Date: 2026-07-29

DAG semantics: `passed`

Mutation realism: `passed`

Notes:

## 0ldq (recurrences_sequences)

### Automatic Evidence

- Reference target derivable: `True`
- Candidate target derivable: `False`
- Computed First Break: `I7`
- Declared/computed match: `True`
- Mutation checker passed: `True`

These automatic results establish structural consistency only. They do
not establish that the natural-language claims and edges are faithful.

### Facts

| ID | Scope | Kind | Statement |
| --- | --- | --- | --- |
| `F1` | `global` | `given` | x_1=2 and x_{n+1}=sqrt(x_n+8)-sqrt(x_n+3). |
| `F2` | `global` | `derived` | All x_n are positive. |
| `F3` | `global` | `constructed` | F(x)=sqrt(x+8)-sqrt(x+3) and F(1)=1. |
| `F4` | `global` | `derived` | x_{n+1}-1=-rho(x_n)(x_n-1) with the stated rho. |
| `F5` | `global` | `derived` | For x>=0, 0<rho(x)<1. |
| `F6` | `global` | `derived` | The deviations alternate sign and have nonincreasing magnitude. |
| `F7` | `global` | `derived` | The orbit remains in the compact interval [0,2]. |
| `F8` | `global` | `derived` | There is q<1 with rho(x)<=q throughout the orbit. |
| `F9` | `global` | `derived` | \|x_n-1\| <= q^(n-1), hence x_n tends to 1. |
| `F10` | `global` | `derived` | Every partial sum of d_i=x_i-1 lies in [0,1]. |
| `F11` | `global` | `derived` | n <= sum_{i=1}^n x_i <= n+1. |
| `F12` | `global` | `derived` | The limit is 1 and the required sum bound holds for every n. |

### Inferences

| ID | Scope | Rule application | Inputs by premise role | Output |
| --- | --- | --- | --- | --- |
| `I1` | `global` | Positivity is preserved by the recurrence | `recurrence=F1` | `F2` |
| `I2` | `global` | Identify the fixed point | `recurrence=F1` | `F3` |
| `I3` | `global` | Rationalize both differences from the fixed point | `recurrence=F1`; `fixed_point=F3` | `F4` |
| `I4` | `global` | Bound the signed multiplier pointwise | `positivity=F2`; `identity=F4` | `F5` |
| `I5` | `global` | Read sign alternation and magnitude monotonicity | `identity=F4`; `pointwise_bound=F5` | `F6` |
| `I6` | `global` | Prove the orbit remains in [0,2] | `recurrence=F1`; `positivity=F2` | `F7` |
| `I7` | `global` | Upgrade pointwise contraction to a uniform one on a compact invariant interval | `pointwise_bound=F5`; `compact_invariant=F7` | `F8` |
| `I8` | `global` | Iterate the uniform contraction | `identity=F4`; `uniform_bound=F8` | `F9` |
| `I9` | `global` | Apply the finite alternating-sum estimate | `alternation=F6`; `initial_value=F1` | `F10` |
| `I10` | `global` | Translate deviation sums back to x_i | `deviation_sum=F10` | `F11` |
| `I11` | `global` | Combine the limit and sum conclusions | `limit=F9`; `sum_bound=F11` | `F12` |

### Controlled Mutation

- Operation: `remove_required_premise`
- Primary site: `F7->I7`
- Injection anchor: `I7`
- Before: `{"fact_id": "F7", "premise_role": "compact_invariant"}`
- After: `{"edge_removed": true, "remaining_claim": "The proof claims a uniform q<1 from pointwise rho(x)<1 without a compact invariant interval."}`
- Expected First Break: `I7`

### Human Decision

- [ ] Every Fact statement is mathematically correct and atomic enough.
- [ ] Every input edge is genuinely required by the stated rule.
- [ ] No required mathematical premise is absent from the Reference DAG.
- [ ] Scope and source order match the reviewed proof.
- [ ] The mutation introduces exactly one real and plausible primary error.
- [ ] The declared First Break is the earliest invalid inference.

Reviewer: Ruan Haochen (Eddie)

Date: 2026-07-29

DAG semantics: `passed`

Mutation realism: `passed`

Notes:

## 0le0 (discrete_algebra)

### Automatic Evidence

- Reference target derivable: `True`
- Candidate target derivable: `False`
- Computed First Break: `I1`
- Declared/computed match: `True`
- Mutation checker passed: `True`

These automatic results establish structural consistency only. They do
not establish that the natural-language claims and edges are faithful.

### Facts

| ID | Scope | Kind | Statement |
| --- | --- | --- | --- |
| `F1` | `global` | `given` | a is in [1/2,2/3], M=2019, and h=2^-M. |
| `F2` | `global` | `constructed` | Define finite digits d_j by the floor recurrence. |
| `F3` | `global` | `derived` | (-1)^floor(2^j a)=1-2d_j. |
| `F4` | `global` | `constructed` | Define odd and even digit masses O,E and s=O+E. |
| `F5` | `global` | `derived` | O,E are constant on each half-open binary cylinder [s,s+h). |
| `F6` | `global` | `derived` | The two finite sums equal the explicit expressions A and C. |
| `F7` | `global` | `derived` | It suffices to check the quadratic bound at a=s. |
| `F8` | `global` | `derived` | After substitution the target is equivalent to G>=0. |
| `F9` | `global/case_even_mass_zero` | `case_assumed` | E=0. |
| `F10` | `global/case_even_mass_zero` | `derived` | G>=0 in the E=0 case, with equality at s=2/3-h/3. |
| `F11` | `global` | `derived` | If E=0 then the reduced inequality holds with the stated equality condition. |
| `F12` | `global/case_even_mass_positive` | `case_assumed` | E>0. |
| `F13` | `global/case_even_mass_positive` | `derived` | The least positive even-position contribution is 2h. |
| `F14` | `global/case_even_mass_positive` | `derived` | G>0 in the E>0 case. |
| `F15` | `global` | `derived` | If E>0 then the reduced inequality is strict. |
| `F16` | `global` | `derived` | Exactly one of E=0 and E>0 holds. |
| `F17` | `global` | `derived` | The required inequality holds and equality occurs only at a=2/3-1/(3*2^2019). |

### Inferences

| ID | Scope | Rule application | Inputs by premise role | Output |
| --- | --- | --- | --- | --- |
| `I1` | `global` | Read floor parity from the last finite binary digit | `domain=F1`; `digits=F2` | `F3` |
| `I2` | `global` | Finite floor digits determine the binary cylinder | `digits=F2`; `digit_masses=F4` | `F5` |
| `I3` | `global` | Evaluate odd and even finite geometric sums | `parity=F3`; `digit_masses=F4`; `odd_length=F1` | `F6` |
| `I4` | `global` | Use monotonicity of the quadratic on each cylinder | `domain=F1`; `constancy=F5`; `sum_formula=F6` | `F7` |
| `I5` | `global` | Algebraically reduce the endpoint inequality to G>=0 | `sum_formula=F6`; `endpoint=F7` | `F8` |
| `I6` | `global/case_even_mass_zero` | Use the truncated upper endpoint when E=0 | `case=F9`; `domain=F1`; `reduction=F8` | `F10` |
| `I7` | `global/case_even_mass_zero` | Discharge the E=0 case | `case=F9`; `bound=F10` | `F11` |
| `I8` | `global/case_even_mass_positive` | Identify the least positive even-position digit mass | `case=F12`; `digits=F2`; `scale=F1` | `F13` |
| `I9` | `global/case_even_mass_positive` | Lower-bound G using E>=2h and d_1=1 | `case=F12`; `least_mass=F13`; `reduction=F8`; `domain=F1` | `F14` |
| `I10` | `global/case_even_mass_positive` | Discharge the E>0 case | `case=F12`; `strict_bound=F14` | `F15` |
| `I11` | `global` | Split the nonnegative even digit mass | `digit_masses=F4` | `F16` |
| `I12` | `global` | Combine both cases and translate the equality prefix | `zero_case=F11`; `positive_case=F15`; `exhaustiveness=F16`; `endpoint_reduction=F7` | `F17` |

### Controlled Mutation

- Operation: `remove_required_premise`
- Primary site: `F2->I1`
- Injection anchor: `I1`
- Before: `{"fact_id": "F2", "premise_role": "digits"}`
- After: `{"edge_removed": true, "remaining_claim": "The proof reads floor parity as a binary digit without defining the finite floor-based digit convention."}`
- Expected First Break: `I1`

### Human Decision

- [ ] Every Fact statement is mathematically correct and atomic enough.
- [ ] Every input edge is genuinely required by the stated rule.
- [ ] No required mathematical premise is absent from the Reference DAG.
- [ ] Scope and source order match the reviewed proof.
- [ ] The mutation introduces exactly one real and plausible primary error.
- [ ] The declared First Break is the earliest invalid inference.

Reviewer: Ruan Haochen (Eddie)

Date: 2026-07-29

DAG semantics: `passed`

Mutation realism: `passed`

Notes:

## 0chi (complex_algebra)

### Automatic Evidence

- Reference target derivable: `True`
- Candidate target derivable: `False`
- Computed First Break: `I5`
- Declared/computed match: `True`
- Mutation checker passed: `True`

These automatic results establish structural consistency only. They do
not establish that the natural-language claims and edges are faithful.

### Facts

| ID | Scope | Kind | Statement |
| --- | --- | --- | --- |
| `F1` | `global` | `given` | a is nonzero. |
| `F1b` | `global` | `given` | b is nonzero. |
| `F1c` | `global` | `given` | c is nonzero. |
| `F2` | `global` | `given` | a and b have the same modulus. |
| `F2c` | `global` | `given` | a and c have the same modulus. |
| `F3` | `global` | `given` | A is real. |
| `F4` | `global` | `given` | B is real. |
| `F5` | `global` | `constructed` | A = a + b + c. |
| `F6` | `global` | `constructed` | B = a*b*c. |
| `F7` | `global` | `constructed` | S = a*b + b*c + c*a. |
| `F8` | `global` | `constructed` | For every n, C_n = a^n + b^n + c^n. |
| `F9` | `global` | `derived` | S is real. |
| `F10` | `global` | `derived` | C_0 is real. |
| `F11` | `global` | `derived` | C_1 is real. |
| `F12` | `global` | `derived` | C_2 is real. |
| `F13` | `global` | `derived` | For every n, C_(n+3) = A*C_(n+2) - S*C_(n+1) + B*C_n. |
| `F14` | `global` | `derived` | For every natural number n, C_n is real. |

### Inferences

| ID | Scope | Rule application | Inputs by premise role | Output |
| --- | --- | --- | --- | --- |
| `I1` | `global` | Equal modulus and real symmetric sums | `nonzero_anchor=F1`; `equal_norm_ab=F2`; `equal_norm_ac=F2c`; `real_first_sum=F3`; `real_product=F4`; `definition_A=F5`; `definition_B=F6`; `definition_S=F7` | `F9` |
| `I2` | `global` | Expand C(0) | `definition_C=F8` | `F10` |
| `I3` | `global` | Rewrite C(1) as A | `real_A=F3`; `definition_A=F5`; `definition_C=F8` | `F11` |
| `I4` | `global` | Use C(2)=A^2-2S | `real_A=F3`; `real_S=F9`; `definition_A=F5`; `definition_S=F7`; `definition_C=F8` | `F12` |
| `I5` | `global` | Vieta power-sum recurrence | `definition_A=F5`; `definition_B=F6`; `definition_S=F7`; `definition_C=F8` | `F13` |
| `I6` | `global` | Strong induction over the recurrence | `real_A=F3`; `real_B=F4`; `real_S=F9`; `base_C0=F10`; `base_C1=F11`; `base_C2=F12`; `recurrence=F13` | `F14` |

### Controlled Mutation

- Operation: `alter_output_sign`
- Primary site: `I5`
- Injection anchor: `I5`
- Before: `"C_(n+3) = A*C_(n+2) - S*C_(n+1) + B*C_n"`
- After: `"C_(n+3) = A*C_(n+2) - S*C_(n+1) - B*C_n"`
- Expected First Break: `I5`

### Human Decision

- [ ] Every Fact statement is mathematically correct and atomic enough.
- [ ] Every input edge is genuinely required by the stated rule.
- [ ] No required mathematical premise is absent from the Reference DAG.
- [ ] Scope and source order match the reviewed proof.
- [ ] The mutation introduces exactly one real and plausible primary error.
- [ ] The declared First Break is the earliest invalid inference.

Reviewer: Ruan Haochen (Eddie)

Date: 2026-07-29

DAG semantics: `passed`

Mutation realism: `passed`

Notes:

