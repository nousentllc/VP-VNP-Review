import FlatTariff
-- Removing the terminal coefficient sign, nonnegative discharge coefficient, or common price.
example : 0 ≤ (50+10)/(1:ℝ)-100 := by norm_num
example : 0 ≤ ((-100:ℝ)+10)*2/1+10-(-100) := by norm_num
example : (1:ℝ)*0+0*100 = 0*0+1*100 := by norm_num
