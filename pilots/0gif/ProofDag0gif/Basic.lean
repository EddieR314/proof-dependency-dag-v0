import Mathlib

namespace ProofDag0gif

open Function Finset
open scoped Function

def Satisfies (f : ℝ → ℝ) : Prop :=
  (∀ x, 0 < x → 0 < f x) ∧
    ∀ x y, 0 < x → 0 < y →
      (f (f x) + y) * f y ≤ x * (f x + f y)

def orbit (f : ℝ → ℝ) (x : ℝ) (n : ℕ) : ℝ :=
  (f^[n]) x

def drop (f : ℝ → ℝ) (x : ℝ) (n : ℕ) : ℝ :=
  orbit f x n - orbit f x (n + 2)

noncomputable def candidate (c x : ℝ) : ℝ :=
  c / x

theorem positive_forward_orbit {f : ℝ → ℝ} (hf : Satisfies f)
    {x : ℝ} (hx : 0 < x) :
    ∀ n : ℕ, 0 < orbit f x n := by
  intro n
  induction n with
  | zero => simpa [orbit] using hx
  | succ n ih =>
      rw [orbit, iterate_succ_apply']
      exact hf.1 _ ih

theorem two_step_descent {f : ℝ → ℝ} (hf : Satisfies f)
    {x : ℝ} (hx : 0 < x) :
    f (f x) ≤ x := by
  have hfx : 0 < f x := hf.1 x hx
  have hffx : 0 < f (f x) := hf.1 (f x) hfx
  have h := hf.2 x (f x) hx hfx
  have hmul :
      f (f x) * (f x + f (f x)) ≤ x * (f x + f (f x)) := by
    nlinarith
  nlinarith [add_pos hfx hffx]

theorem iterate_two_step_descent {f : ℝ → ℝ} (hf : Satisfies f)
    {x : ℝ} (hx : 0 < x) (n : ℕ) :
    orbit f x (n + 2) ≤ orbit f x n := by
  have hpos := positive_forward_orbit hf hx n
  have h := two_step_descent hf hpos
  simpa [orbit, Function.iterate_succ_apply', Nat.add_assoc] using h

theorem adjacent_point_inequality {f : ℝ → ℝ} (hf : Satisfies f)
    {z : ℝ} (hz : 0 < z) :
    z + f (f (f z)) ≤ f z + f (f z) := by
  have hfz : 0 < f z := hf.1 z hz
  have h := hf.2 (f z) z hfz hz
  have hmul :
      f z * (z + f (f (f z))) ≤ f z * (f z + f (f z)) := by
    nlinarith
  nlinarith

theorem adjacent_drop_comparison {f : ℝ → ℝ} (hf : Satisfies f)
    {x : ℝ} (hx : 0 < x) (n : ℕ) :
    orbit f x n + orbit f x (n + 3) ≤
      orbit f x (n + 1) + orbit f x (n + 2) := by
  have hpos := positive_forward_orbit hf hx n
  have h := adjacent_point_inequality hf hpos
  simpa [orbit, Function.iterate_succ_apply', Nat.add_assoc] using h

theorem drops_nonnegative {f : ℝ → ℝ} (hf : Satisfies f)
    {x : ℝ} (hx : 0 < x) (n : ℕ) :
    0 ≤ drop f x n := by
  exact sub_nonneg.mpr (iterate_two_step_descent hf hx n)

theorem drops_nondecreasing {f : ℝ → ℝ} (hf : Satisfies f)
    {x : ℝ} (hx : 0 < x) (n : ℕ) :
    drop f x n ≤ drop f x (n + 1) := by
  have h := adjacent_drop_comparison hf hx n
  unfold drop
  linarith

theorem even_telescoping (s : ℕ → ℝ) (N : ℕ) :
    s (2 * N) =
      s 0 - ∑ j ∈ range N, (s (2 * j) - s (2 * j + 2)) := by
  induction N with
  | zero => simp
  | succ N ih =>
      calc
        s (2 * (N + 1)) = s (2 * N + 2) := by
          congr 1
        _ = s (2 * N) - (s (2 * N) - s (2 * N + 2)) := by ring
        _ = s 0 - (∑ j ∈ range N, (s (2 * j) - s (2 * j + 2))) -
              (s (2 * N) - s (2 * N + 2)) := by rw [ih]
        _ = s 0 -
              ∑ j ∈ range (N + 1), (s (2 * j) - s (2 * j + 2)) := by
          rw [sum_range_succ]
          ring

theorem even_drop_sum_bound {f : ℝ → ℝ} (hf : Satisfies f)
    {x : ℝ} (hx : 0 < x) (N : ℕ) :
    (∑ j ∈ range N, drop f x (2 * j)) < x := by
  have htel' :
      orbit f x (2 * N) =
        orbit f x 0 - ∑ j ∈ range N, drop f x (2 * j) := by
    simpa [drop] using even_telescoping (orbit f x) N
  have hzero : orbit f x 0 = x := by simp [orbit]
  have hpos := positive_forward_orbit hf hx (2 * N)
  rw [hzero] at htel'
  linarith

theorem monotone_drops_vanish (d : ℕ → ℝ) (B : ℝ)
    (hnonneg : ∀ n, 0 ≤ d n)
    (hstep : ∀ n, d n ≤ d (n + 1))
    (hbound : ∀ N, (∑ j ∈ range N, d (2 * j)) < B) :
    ∀ n, d n = 0 := by
  have hmono : Monotone d := monotone_nat_of_le_succ hstep
  intro n
  apply le_antisymm
  · by_contra hnot
    have hpos : 0 < d n := lt_of_not_ge hnot
    obtain ⟨N, hN⟩ := exists_nat_gt (B / d n)
    have hlarge : B < (N : ℝ) * d n := by
      exact (div_lt_iff₀ hpos).mp hN
    have hsegment :
        (N : ℝ) * d n ≤
          ∑ j ∈ Ico n (n + N), d (2 * j) := by
      calc
        (N : ℝ) * d n =
            ∑ j ∈ Ico n (n + N), d n := by simp
        _ ≤ ∑ j ∈ Ico n (n + N), d (2 * j) := by
          apply sum_le_sum
          intro j hj
          apply hmono
          have hjn : n ≤ j := (mem_Ico.mp hj).1
          omega
    have hprefix : 0 ≤ ∑ j ∈ range n, d (2 * j) := by
      exact sum_nonneg fun j _ => hnonneg (2 * j)
    have hsplit :=
      sum_range_add_sum_Ico (fun j => d (2 * j)) (Nat.le_add_right n N)
    have hfull :
        (N : ℝ) * d n ≤ ∑ j ∈ range (n + N), d (2 * j) := by
      rw [← hsplit]
      linarith
    have := hbound (n + N)
    linarith
  · exact hnonneg n

theorem composition_identity {f : ℝ → ℝ} (hf : Satisfies f)
    {x : ℝ} (hx : 0 < x) :
    f (f x) = x := by
  have hzero :=
    monotone_drops_vanish (drop f x) x
      (fun n => drops_nonnegative hf hx n)
      (fun n => drops_nondecreasing hf hx n)
      (fun N => even_drop_sum_bound hf hx N)
  have := hzero 0
  simp [drop, orbit, Function.iterate_succ_apply'] at this
  linarith

theorem product_order {f : ℝ → ℝ} (hf : Satisfies f)
    {x y : ℝ} (hx : 0 < x) (hy : 0 < y) :
    y * f y ≤ x * f x := by
  have h := hf.2 x y hx hy
  rw [composition_identity hf hx] at h
  nlinarith

theorem reverse_product_order {f : ℝ → ℝ} (hf : Satisfies f)
    {x y : ℝ} (hx : 0 < x) (hy : 0 < y) :
    x * f x ≤ y * f y := by
  exact product_order hf hy hx

theorem product_constant {f : ℝ → ℝ} (hf : Satisfies f)
    {x y : ℝ} (hx : 0 < x) (hy : 0 < y) :
    x * f x = y * f y :=
  le_antisymm (reverse_product_order hf hx hy) (product_order hf hx hy)

theorem reciprocal_necessity {f : ℝ → ℝ} (hf : Satisfies f) :
    ∃ c : ℝ, 0 < c ∧ ∀ x, 0 < x → f x = c / x := by
  let c := f 1
  have hc : 0 < c := hf.1 1 zero_lt_one
  refine ⟨c, hc, ?_⟩
  intro x hx
  have hprod := product_constant hf hx zero_lt_one
  dsimp [c]
  field_simp
  nlinarith

theorem candidate_positive {c x : ℝ} (hc : 0 < c) (hx : 0 < x) :
    0 < candidate c x := by
  exact div_pos hc hx

theorem candidate_involution {c x : ℝ} (hc : 0 < c) (hx : 0 < x) :
    candidate c (candidate c x) = x := by
  unfold candidate
  field_simp

theorem candidate_satisfies {c : ℝ} (hc : 0 < c) :
    Satisfies (candidate c) := by
  constructor
  · intro x hx
    exact candidate_positive hc hx
  · intro x y hx hy
    rw [candidate_involution hc hx]
    unfold candidate
    field_simp
    ring_nf
    exact le_rfl

theorem all_solutions :
    ∀ f : ℝ → ℝ, Satisfies f ↔
      ∃ c : ℝ, 0 < c ∧ ∀ x, 0 < x → f x = c / x := by
  intro f
  constructor
  · exact reciprocal_necessity
  · rintro ⟨c, hc, hfc⟩
    have hg := candidate_satisfies hc
    constructor
    · intro x hx
      rw [hfc x hx]
      exact hg.1 x hx
    · intro x y hx hy
      rw [hfc x hx]
      rw [hfc (c / x) (div_pos hc hx)]
      rw [hfc y hy]
      exact hg.2 x y hx hy

end ProofDag0gif
