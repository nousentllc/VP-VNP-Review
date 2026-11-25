import Paper.Extension

/- Pass 11B. Inspect the publisher declarations used for selection and its
   A.7 caller. The independent additive-monoid examples at the end isolate
   what breaks when directedness or the multiplier quantifier is discarded. -/
#check @Paper.prop_gauge_chain
#print axioms Paper.prop_gauge_chain
#check @Paper.prop_gauge_minimal
#print axioms Paper.prop_gauge_minimal
#check @Paper.prop_gauge_radius_cover
#print axioms Paper.prop_gauge_radius_cover
#check @Paper.prop_gauge_radius
#print axioms Paper.prop_gauge_radius
#check @Paper.prop_gauge_radius_keeps
#print axioms Paper.prop_gauge_radius_keeps
#check @Paper.prop_gauge_radius_eq
#print axioms Paper.prop_gauge_radius_eq
#check @Paper.prop_gauge_radius_pow
#print axioms Paper.prop_gauge_radius_pow
#check @Paper.prop_gauge_localize
#print axioms Paper.prop_gauge_localize
#check @Paper.prop_gauge_monoid
#print axioms Paper.prop_gauge_monoid
#check @Paper.prop_gauge
#print axioms Paper.prop_gauge
#check @Paper.prop_extend
#print axioms Paper.prop_extend

namespace Pass11B

def left (v : ℕ × ℕ) : ℕ := 2 ^ v.1
def right (v : ℕ × ℕ) : ℕ := 2 ^ v.2
def lower (v : ℕ × ℕ) : ℕ := min (left v) (right v)
def upper (v : ℕ × ℕ) : ℕ := max (left v) (right v)

theorem characters (s t : ℕ × ℕ) :
    left (s + t) = left s * left t ∧ right (s + t) = right s * right t := by
  exact ⟨pow_add _ _ _, pow_add _ _ _⟩

theorem upper_submul (s t : ℕ × ℕ) : upper (s + t) ≤ upper s * upper t := by
  unfold upper
  rw [(characters s t).1, (characters s t).2]
  exact max_le (Nat.mul_le_mul (le_max_left _ _) (le_max_left _ _))
    (Nat.mul_le_mul (le_max_right _ _) (le_max_right _ _))

/-- The two characters are incomparable. Their lower envelope fails the
    product inequality on the two generators. -/
theorem undirected_minimum_fails :
    lower ((1, 0) + (0, 1)) > lower (1, 0) * lower (0, 1) := by decide

/-- Comparing the two generators at the identity succeeds for the upper
    envelope. Translating both by the first generator reverses the test. -/
theorem testing_at_identity_fails :
    upper (1, 0) = upper (0, 1) ∧ upper ((1, 0) + (1, 0)) > upper ((1, 0) + (0, 1)) := by decide

#print axioms characters
#print axioms upper_submul
#print axioms undirected_minimum_fails
#print axioms testing_at_identity_fails
end Pass11B
