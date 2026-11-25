import Obstructions
-- Each statement below has an explicit contrary witness in the positive modules.
example : (1/2:ℝ) = 0 ∨ (1/2:ℝ) = 1 := by norm_num
example : (((-1:ℝ)+1)/2)^2 = 1 := by norm_num
example : (1-(1/2:ℝ))*2+(1/2:ℝ)*0 = 0 := by norm_num
example : W05.rowNeed 1 0 < 1 := by norm_num [W05.rowNeed]
example : (∀ x ∈ ({1} : Set ℝ), (1:ℝ) ≤ x) → ∀ x ∈ Set.Icc (0:ℝ) 1, 1 ≤ x := by norm_num
example : ∃ q : ℝ, 0 ≤ q ∧ q ≤ 1 ∧ q = 2 := by norm_num
example : (0:ℝ)+2*(1-0) ≤ 1 := by norm_num
