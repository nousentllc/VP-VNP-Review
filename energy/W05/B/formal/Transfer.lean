import Anchor
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset

namespace W05
open scoped BigOperators

/-- Greatest affine contribution from one independent component of a box. -/
theorem corner_bound {q l h x : ℝ} (hl : l ≤ x) (hh : x ≤ h) :
    q*x ≤ max (q*l) (q*h) := by
  rcases le_total 0 q with hp | hn
  · exact (mul_le_mul_of_nonneg_left hh hp).trans (le_max_right _ _)
  · exact (mul_le_mul_of_nonpos_left hl hn).trans (le_max_left _ _)

theorem affine_box_support {I : Type*} [Fintype I] (q l h x : I → ℝ)
    (hl : ∀ i, l i ≤ x i) (hh : ∀ i, x i ≤ h i) (offset : ℝ) :
    offset + ∑ i, q i*x i ≤ offset + ∑ i, max (q i*l i) (q i*h i) := by
  have hsum : (∑ i, q i*x i) ≤ ∑ i, max (q i*l i) (q i*h i) :=
    Finset.sum_le_sum (fun i _ => corner_bound (hl i) (hh i))
  linarith

/-- For a full-to-reduced projection, certify its cost representation error
    over the full feasible set using a larger coordinate box. -/
theorem projection_support {X Y I : Type*} [Fintype I]
    (J : X → ℝ) (K : Y → ℝ) (p : X → Y) (coord : X → I → ℝ)
    (q l h : I → ℝ) (offset : ℝ)
    (hl : ∀ x i, l i ≤ coord x i) (hh : ∀ x i, coord x i ≤ h i)
    (representation : ∀ x, K (p x)-J x = offset + ∑ i, q i*coord x i) :
    ∀ x, K (p x) ≤ J x + max 0 (offset + ∑ i, max (q i*l i) (q i*h i)) := by
  intro x
  have hb := affine_box_support q l h (coord x) (hl x) (hh x) offset
  have hx := representation x
  linarith [le_max_right 0 (offset + ∑ i, max (q i*l i) (q i*h i))]

theorem outer_embedding {X Y : Type*} (J : X → ℝ) (K : Y → ℝ) (p : X → Y)
    (cost : ∀ x, K (p x) = J x) : ∀ x, K (p x) ≤ J x + 0 := by simp [cost]

/-- A numerical objective mismatch must also be budgeted. Signed mismatch and
    signed affine loss can be evaluated before taking the positive part. -/
theorem cost_mismatch {jx ku ja jfixed t tau : ℝ}
    (id : jfixed-jx=t*(ja-jx)) (mismatch : jx-ku ≤ tau) :
    jfixed ≤ ku + max 0 (tau+t*(ja-jx)) := by
  linarith [le_max_right 0 (tau+t*(ja-jx))]

/-- Preserve the uniform projection obligation and the ε-suboptimality of y. -/
theorem aipc_from_repair {X Y : Type*} {J : X → ℝ} {K : Y → ℝ}
    {a beta eps : ℝ} (bj : BddBelow (Set.range J)) (bk : BddBelow (Set.range K))
    (p : X → Y) (hp : ∀ u, K (p u) ≤ J u + a)
    (y : Y) (x : X) (hy : K y ≤ W04.value K + eps) (hx : J x-K y ≤ beta) :
    0 ≤ J x-W04.value J ∧ J x-W04.value J ≤ a+beta+eps :=
  W04.candidate_regret bj bk p hp y x hy (by linarith)

/-- A validated affine cost cap D against the anchor and a uniform mixing
    cap obey a product bound even if the returned point costs less. -/
theorem uniform_affine_beta {jfinal jraw ja betaRaw D cap t : ℝ}
    (aff : jfinal-jraw = t*(ja-jraw)) (mismatch : jraw ≤ betaRaw)
    (ht : 0 ≤ t) (hc : t ≤ cap) (hD : 0 ≤ D) (gap : ja-jraw ≤ D) :
    jfinal ≤ betaRaw + cap*D := by
  linarith [mul_le_mul_of_nonneg_left gap ht,mul_le_mul_of_nonneg_right hc hD]

end W05
