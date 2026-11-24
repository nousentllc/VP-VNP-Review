import Mathlib.Data.Real.Basic

/- In D.2 Step 6, the matrices are binary and the reflected quantity is real.
   These lemmas isolate the final scalar implication. The geometric reflection
   law and equality of the values on transversal rank-one pairs are premises. -/
namespace Pass07Reflection

/-- If V, W, and V + W are rank one, the two-step path and the direct move
    end at the same base point. For example take V = E₁₁, W = E₁₂ over F₂. -/
theorem rank_one_triangle {M : Type*} [AddSemigroup M] (rankOne : M → Prop)
    (value : M → ℝ) (reflect : ∀ a V, rankOne V → value (a + V) = -value a)
    (V W : M) (hV : rankOne V) (hW : rankOne W) (hVW : rankOne (V + W))
    (a : M) : value a = 0 := by
  have first := reflect a V hV
  have second := reflect (a + V) W hW
  have direct := reflect a (V + W) hVW
  rw [add_assoc] at second
  apply eq_zero_of_neg_eq
  calc
    -(value a) = value (a + (V + W)) := direct.symm
    _ = -value (a + V) := second
    _ = value a := by rw [first, neg_neg]

/-- The publisher uses two independent diagonal moves. Their sum has rank two,
    so the direct reflection equation for the cross term carries a factor 2. -/
theorem rank_two_diagonal (base afterFirst endpoint : ℝ)
    (first : afterFirst = -base) (second : endpoint = -afterFirst)
    (direct : 2 * endpoint = -(2 * base)) : base = 0 := by
  rw [second, first, neg_neg] at direct
  have h : 2 * base = 0 := eq_zero_of_neg_eq direct.symm
  exact (mul_eq_zero.mp h).resolve_left two_ne_zero

#print axioms rank_one_triangle
#print axioms rank_two_diagonal

end Pass07Reflection
