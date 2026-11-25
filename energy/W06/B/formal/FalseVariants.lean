import Tests
open W06

-- These examples are expected to fail elaboration. Their exact source lines are checked.
example : ¬(1:ℝ) ≤ 10-9 := by norm_num
example : (1:ℝ) ≤ 0 := by norm_num
example : (2:ℝ) ≤ 0 := by norm_num
example : (-1:ℝ)*1 ≤ (-1)*2 := by norm_num
example : max (0:ℝ) 80 ≤ max 50 50 := by norm_num
example : Dual.floorTerm .free 1 = some 0 := by norm_num [Dual.floorTerm]
example (v : Amount Unit Unit) : Amount Bool Unit := v
example (v : Amount Unit Unit) : Amount Unit Bool := v
