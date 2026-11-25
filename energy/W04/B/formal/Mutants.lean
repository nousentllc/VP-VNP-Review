import Controls
open W04.Controls

-- Expected to fail. Controls.lean separately proves each concrete obstruction.
example : (0:ℚ) = 1 := by norm_num -- missing lift would equate the two optima
example : |(1:ℤ)-0|+|(0:ℤ)-1| = |(1+0:ℤ)-(0+1)| := by norm_num -- labeled ends
example : (2:ℕ) ≤ 1 := by norm_num -- discharge both units in one step from (2,0)
example : (1:ℚ) ≤ cost true := by norm_num [cost] -- restricted lower bound
example : (((1:ℚ)/2)*((81/100)*1-4/5)/(9/10) ≤ 1/180) → (1:ℚ)=0 := by norm_num -- tolerance
example : rampAdmissible 0 3 := by norm_num [rampAdmissible] -- omitted history
example : (1:ℚ)/2 = 1 := by norm_num -- LP vs integer optimum
example : (1:ℕ) ≤ 0 := by norm_num -- overwrite incumbent
