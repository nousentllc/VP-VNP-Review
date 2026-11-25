import Nc.Tow.Load

#check @Nc.Tow.Tower.load_step
#print axioms Nc.Tow.Tower.load_step

/-- The additive load is absorbed by the shrinkage in the number of vertices. -/
theorem compensated_load_bound
    (Q V : ℕ → ℝ) (d : ℝ) (hd : 0 ≤ d)
    (hstep : ∀ j, Q (j + 1) ≤ Q j / 2 + d * V (j + 1))
    (hshrink : ∀ j, 4 * V (j + 1) ≤ V j) (j : ℕ) :
    Q j + d * V j ≤ (1 / 2 : ℝ) ^ j * (Q 0 + d * V 0) := by
  induction j with
  | zero => simp
  | succ j ih =>
    have h := mul_le_mul_of_nonneg_left (hshrink j) hd
    rw [pow_succ]
    linarith [hstep j]

#print axioms compensated_load_bound
