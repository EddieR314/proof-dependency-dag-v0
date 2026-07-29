import Mathlib

namespace ProofDag0chi

open Complex
open scoped ComplexConjugate

def IsReal (z : ℂ) : Prop := conj z = z

def firstSymmetric (a b c : ℂ) : ℂ := a + b + c

def secondSymmetric (a b c : ℂ) : ℂ := a * b + b * c + c * a

def thirdSymmetric (a b c : ℂ) : ℂ := a * b * c

def powerSum (a b c : ℂ) (n : ℕ) : ℂ := a ^ n + b ^ n + c ^ n

lemma isReal_add {x y : ℂ} (hx : IsReal x) (hy : IsReal y) :
    IsReal (x + y) := by
  unfold IsReal at hx hy ⊢
  simp [hx, hy]

lemma isReal_neg {x : ℂ} (hx : IsReal x) : IsReal (-x) := by
  unfold IsReal at hx ⊢
  simp [hx]

lemma isReal_sub {x y : ℂ} (hx : IsReal x) (hy : IsReal y) :
    IsReal (x - y) := by
  simpa [sub_eq_add_neg] using isReal_add hx (isReal_neg hy)

lemma isReal_mul {x y : ℂ} (hx : IsReal x) (hy : IsReal y) :
    IsReal (x * y) := by
  unfold IsReal at hx hy ⊢
  simp [hx, hy]

lemma isReal_pow {x : ℂ} (hx : IsReal x) (n : ℕ) : IsReal (x ^ n) := by
  unfold IsReal at hx ⊢
  simp [hx]

lemma isReal_natCast (n : ℕ) : IsReal (n : ℂ) := by
  unfold IsReal
  exact Complex.conj_natCast n

theorem secondSymmetric_isReal {a b c : ℂ}
    (ha : a ≠ 0)
    (hab : ‖a‖ = ‖b‖)
    (hac : ‖a‖ = ‖c‖)
    (hA : IsReal (firstSymmetric a b c))
    (hB : IsReal (thirdSymmetric a b c)) :
    IsReal (secondSymmetric a b c) := by
  have hA' : conj (firstSymmetric a b c) = firstSymmetric a b c := hA
  have hB' : conj (thirdSymmetric a b c) = thirdSymmetric a b c := hB
  have habSq : normSq a = normSq b := by
    rw [normSq_eq_norm_sq, normSq_eq_norm_sq, hab]
  have hacSq : normSq a = normSq c := by
    rw [normSq_eq_norm_sq, normSq_eq_norm_sq, hac]
  have hq_ne : (normSq a : ℂ) ≠ 0 := by
    exact_mod_cast (mt normSq_eq_zero.mp ha)
  have hidentity :
      thirdSymmetric a b c * conj (firstSymmetric a b c) =
        (normSq a : ℂ) * secondSymmetric a b c := by
    simp only [firstSymmetric, secondSymmetric, thirdSymmetric, map_add]
    rw [mul_add, mul_add]
    rw [show a * b * c * conj a = (normSq a : ℂ) * (b * c) by
      calc
        a * b * c * conj a = (a * conj a) * (b * c) := by ring
        _ = (normSq a : ℂ) * (b * c) := by rw [mul_conj]]
    rw [show a * b * c * conj b = (normSq a : ℂ) * (c * a) by
      calc
        a * b * c * conj b = (b * conj b) * (c * a) := by ring
        _ = (normSq b : ℂ) * (c * a) := by rw [mul_conj]
        _ = (normSq a : ℂ) * (c * a) := by rw [habSq]]
    rw [show a * b * c * conj c = (normSq a : ℂ) * (a * b) by
      calc
        a * b * c * conj c = (c * conj c) * (a * b) := by ring
        _ = (normSq c : ℂ) * (a * b) := by rw [mul_conj]
        _ = (normSq a : ℂ) * (a * b) := by rw [hacSq]]
    ring
  have hqS :
      (normSq a : ℂ) * secondSymmetric a b c =
        thirdSymmetric a b c * firstSymmetric a b c := by
    rw [← hidentity, hA']
  have hqConjS :
      (normSq a : ℂ) * conj (secondSymmetric a b c) =
        thirdSymmetric a b c * firstSymmetric a b c := by
    have h := congrArg conj hqS
    simpa [map_mul, hA', hB'] using h
  apply (mul_left_cancel₀ hq_ne)
  exact hqConjS.trans hqS.symm

theorem powerSum_recurrence (a b c : ℂ) (n : ℕ) :
    powerSum a b c (n + 3) =
      firstSymmetric a b c * powerSum a b c (n + 2) -
        secondSymmetric a b c * powerSum a b c (n + 1) +
          thirdSymmetric a b c * powerSum a b c n := by
  simp only [powerSum, firstSymmetric, secondSymmetric, thirdSymmetric, pow_add]
  ring

theorem wrongSign_recurrence_counterexample :
    ¬(powerSum 1 1 1 (0 + 3) =
      firstSymmetric 1 1 1 * powerSum 1 1 1 (0 + 2) -
        secondSymmetric 1 1 1 * powerSum 1 1 1 (0 + 1) -
          thirdSymmetric 1 1 1 * powerSum 1 1 1 0) := by
  norm_num [powerSum, firstSymmetric, secondSymmetric, thirdSymmetric]

theorem all_powerSums_real {a b c : ℂ}
    (ha : a ≠ 0)
    (hab : ‖a‖ = ‖b‖)
    (hac : ‖a‖ = ‖c‖)
    (hA : IsReal (firstSymmetric a b c))
    (hB : IsReal (thirdSymmetric a b c)) :
    ∀ n : ℕ, IsReal (powerSum a b c n) := by
  have hS : IsReal (secondSymmetric a b c) :=
    secondSymmetric_isReal ha hab hac hA hB
  intro n
  induction n using Nat.strong_induction_on with
  | h n ih =>
      by_cases hn : n < 3
      · interval_cases n
        · simp [powerSum, IsReal]
        · simpa [powerSum, firstSymmetric] using hA
        · have hC2 :
              powerSum a b c 2 =
                firstSymmetric a b c ^ 2 - 2 * secondSymmetric a b c := by
            simp [powerSum, firstSymmetric, secondSymmetric]
            ring
          rw [hC2]
          exact isReal_sub (isReal_pow hA 2) (isReal_mul (isReal_natCast 2) hS)
      · obtain ⟨k, rfl⟩ : ∃ k, n = k + 3 := ⟨n - 3, by omega⟩
        rw [powerSum_recurrence]
        exact isReal_add
          (isReal_sub
            (isReal_mul hA (ih (k + 2) (by omega)))
            (isReal_mul hS (ih (k + 1) (by omega))))
          (isReal_mul hB (ih k (by omega)))

end ProofDag0chi
