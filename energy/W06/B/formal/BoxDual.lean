import Mathlib.Data.Real.Archimedean
import Mathlib.Order.ConditionallyCompleteLattice.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring

namespace W06.Dual
noncomputable section

inductive Interval where
  | closed (lo hi : ℝ)
  | lower (lo : ℝ)
  | upper (hi : ℝ)
  | free

def contains : Interval → ℝ → Prop
  | .closed lo hi, x => lo ≤ x ∧ x ≤ hi
  | .lower lo, x => lo ≤ x
  | .upper hi, x => x ≤ hi
  | .free, _ => True

/-- Finite support from below. An unsupported ray returns none. -/
def floorTerm : Interval → ℝ → Option ℝ
  | .closed lo hi, r => some (min (r*lo) (r*hi))
  | .lower lo, r => if 0 ≤ r then some (r*lo) else none
  | .upper hi, r => if r ≤ 0 then some (r*hi) else none
  | .free, r => if r = 0 then some 0 else none

theorem finiteEndpoint {r l u x : ℝ} (hl : l ≤ x) (hu : x ≤ u) :
    min (r*l) (r*u) ≤ r*x := by
  rcases le_total 0 r with hr | hr
  · exact le_trans (min_le_left _ _) (mul_le_mul_of_nonneg_left hl hr)
  · exact le_trans (min_le_right _ _) (mul_le_mul_of_nonpos_left hu hr)

theorem floorTermSound (D : Interval) (r x a : ℝ) (hx : contains D x)
    (ha : floorTerm D r = some a) : a ≤ r*x := by
  cases D with
  | closed lo hi =>
    simp only [floorTerm, Option.some.injEq] at ha
    rw [← ha]
    exact finiteEndpoint hx.1 hx.2
  | lower lo =>
    simp only [floorTerm] at ha
    split at ha
    · rename_i h
      cases ha
      exact mul_le_mul_of_nonneg_left hx h
    · contradiction
  | upper hi =>
    simp only [floorTerm] at ha
    split at ha
    · rename_i h
      cases ha
      exact mul_le_mul_of_nonpos_left hx h
    · contradiction
  | free =>
    simp only [floorTerm] at ha
    split at ha
    · rename_i h
      cases ha
      simp [h]
    · contradiction

variable {I J : Type*} [Fintype I] [Fintype J]

def dot (a x : J → ℝ) : ℝ := ∑ j, a j * x j

def back (A : I → J → ℝ) (z : I → ℝ) (j : J) : ℝ := ∑ i, z i * A i j

theorem transposePair (A : I → J → ℝ) (z : I → ℝ) (x : J → ℝ) :
    dot (back A z) x = ∑ i, z i * dot (A i) x := by
  simp only [dot, back, Finset.sum_mul, Finset.mul_sum, mul_assoc]
  rw [Finset.sum_comm]

/-- Mixed row bounds: apply the same endpoint function with the row activity as x.
    A singleton gives an unrestricted equality multiplier; an upper row requires a
    nonpositive multiplier; a free row only contributes at zero multiplier. -/
theorem mixedRowDual (A : I → J → ℝ) (c x : J → ℝ) (z : I → ℝ)
    (rows : I → Interval) (cols : J → Interval) (rowTerms : I → ℝ) (colTerms : J → ℝ)
    (hrow : ∀ i, contains (rows i) (dot (A i) x))
    (hcol : ∀ j, contains (cols j) (x j))
    (hr : ∀ i, floorTerm (rows i) (z i) = some (rowTerms i))
    (hc : ∀ j, floorTerm (cols j) (c j - back A z j) = some (colTerms j)) :
    (∑ i, rowTerms i) + (∑ j, colTerms j) ≤ dot c x := by
  have a : (∑ i, rowTerms i) ≤ ∑ i, z i * dot (A i) x := by
    apply Finset.sum_le_sum
    exact fun i _ => floorTermSound _ _ _ _ (hrow i) (hr i)
  have b : (∑ j, colTerms j) ≤ ∑ j, (c j-back A z j) * x j := by
    apply Finset.sum_le_sum
    exact fun j _ => floorTermSound _ _ _ _ (hcol j) (hc j)
  rw [← transposePair] at a
  simp only [sub_mul, Finset.sum_sub_distrib] at b
  unfold dot at *
  linarith

/-- The manuscript sign convention: Ex=d and Ax≤b, z≤0, r=c-Eᵀy-Aᵀz. -/
theorem boxedDual {K : Type*} [Fintype K] (E : K → J → ℝ) (A : I → J → ℝ)
    (c x l u : J → ℝ) (y d : K → ℝ) (z b : I → ℝ)
    (he : ∀ k, dot (E k) x = d k) (ha : ∀ i, dot (A i) x ≤ b i)
    (hz : ∀ i, z i ≤ 0) (hl : ∀ j, l j ≤ x j) (hu : ∀ j, x j ≤ u j) :
    dot y d + dot z b +
      (∑ j, min ((c j-back E y j-back A z j)*l j) ((c j-back E y j-back A z j)*u j))
      ≤ dot c x := by
  have ye : dot y d = dot (back E y) x := by rw [transposePair]; simp_rw [he]; rfl
  have za : dot z b ≤ dot (back A z) x := by
    rw [transposePair]
    exact Finset.sum_le_sum fun i _ => mul_le_mul_of_nonpos_left (ha i) (hz i)
  have box : (∑ j, min ((c j-back E y j-back A z j)*l j) ((c j-back E y j-back A z j)*u j))
      ≤ ∑ j, (c j-back E y j-back A z j)*x j :=
    Finset.sum_le_sum fun j _ => finiteEndpoint (hl j) (hu j)
  simp only [sub_mul, Finset.sum_sub_distrib] at box ⊢
  unfold dot at *
  linarith

end
end W06.Dual
