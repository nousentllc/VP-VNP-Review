import Terminal
import Transfer

namespace W05.Obstructions

theorem unverified_anchor : (1:ℝ) > 0 ∧ ∀ t ∈ Set.Icc (0:ℝ) 1,
    0 < (1-t)*1+t*2 := by
  constructor
  · norm_num
  · intro t ht
    linarith [ht.1]

theorem integral_midpoint : (1/2:ℝ) ≠ 0 ∧ (1/2:ℝ) ≠ 1 := by norm_num

theorem nonconvex_voltage : (-1:ℝ)^2 = 1 ∧ (1:ℝ)^2 = 1 ∧
    (((-1:ℝ)+1)/2)^2 ≠ 1 := by norm_num

theorem equality_after_mixing : (1-(1/2:ℝ))*2+(1/2:ℝ)*0 ≠ 0 := by norm_num

theorem inverse_can_break_bounds :
    let x : ℝ := 0; let y : ℝ := 0; let r := 1-x
    x=0 ∧ y=0 ∧ x+r=1 ∧ ¬ (y+2*r ≤ 1) := by norm_num

theorem box_gap_over_true_gap : (∀ x ∈ Set.Icc (0:ℝ) 1, x-x=0) ∧
    (1:ℝ)-0=1 := by simp

theorem bound_scope : (∀ x ∈ ({1} : Set ℝ), (1:ℝ) ≤ x) ∧
    ∃ x ∈ Set.Icc (0:ℝ) 1, ¬ (1:ℝ) ≤ x := by
  refine ⟨by simp,⟨0,?_,?_⟩⟩ <;> norm_num

/-- Candidate (ε,0), feasible anchor (0,1) and full set z₁ ≤ 0.
    Anchor and best repair have costs 1 and 0 for J(z)=z₂. -/
theorem arbitrarily_small_violation (e : ℝ) (he : 0 < e) :
    W05.rowNeed e 0 = 1 ∧ ((1-(1:ℝ))*0+1*1) - 0 = 1 := by
  simp [W05.rowNeed,he,ne_of_gt he]

/-- Two individually valid boundary anchors (-1,0) and (0,-1)
    against x=(1,1). Their common-mode midpoint has both slacks 1/2. -/
theorem mixture_of_anchors :
    max (W05.rowNeed 1 1) (W05.rowNeed 1 0) = 1 ∧
    max (W05.rowNeed 1 0) (W05.rowNeed 1 1) = 1 ∧
    max (W05.rowNeed 1 (1/2)) (W05.rowNeed 1 (1/2)) = 2/3 ∧
    ((1-(2/3:ℝ))*1+(2/3)*(-1/2))=0 := by
  norm_num [W05.rowNeed]

end W05.Obstructions
