import Mathlib

namespace Review12C

/-- A common family of scores supports simultaneous induction at every node.
The sum records one possible loss per level. -/
theorem midpoint_budget {A : Type*} (score : ℕ → A → ℝ) (left right : ℕ → A → A)
    (loss : ℕ → ℝ) (base : ℝ) (initial : ∀ a, score 0 a ≤ base)
    (step : ∀ j a, score (j+1) a ≤
      (score j (left j a) + score j (right j a)) / 2 + loss j) :
    ∀ j a, score j a ≤ base + ∑ i ∈ Finset.range j, loss i := by
  intro j
  induction j with
  | zero => simpa using initial
  | succ j ih =>
    intro a
    rw [Finset.sum_range_succ]
    linarith [step j a, ih (left j a), ih (right j a)]

#print axioms midpoint_budget
end Review12C
