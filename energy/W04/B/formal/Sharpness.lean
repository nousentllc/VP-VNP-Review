import AIPC

namespace W04.Sharpness

noncomputable def J (a b ε : ℝ) (i : Bool) : ℝ := if i then a+b+ε else 0
noncomputable def K (a ε : ℝ) (i : Bool) : ℝ := if i then a+ε else a

/-- Equality in the three-term abstract bound for every nonnegative error triple. -/
theorem sharp (a b ε : ℝ) (ha : 0 ≤ a) (hb : 0 ≤ b) (he : 0 ≤ ε) :
    (∀ x, K a ε false ≤ J a b ε x + a) ∧
    (∀ y, J a b ε y ≤ K a ε y + b) ∧
    K a ε true = value (K a ε) + ε ∧
    J a b ε true - value (J a b ε) = a+b+ε := by
  have hJ : value (J a b ε) = 0 := attained_value false (by
    intro u
    cases u <;> simp [J] <;> linarith)
  have hK : value (K a ε) = a := attained_value false (by
    intro u
    cases u <;> simp [K] <;> linarith)
  refine ⟨?_,?_,?_,?_⟩
  · intro u
    cases u <;> simp [J,K] <;> linarith
  · intro u
    cases u <;> simp [J,K] <;> linarith
  · simp [K,hK]
  · simp [J,hJ]
end W04.Sharpness
