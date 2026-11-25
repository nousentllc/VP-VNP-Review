import Mathlib

namespace Review.Pass13B

/-- If input and output rounding and the common label satisfy the stated budgets,
the law's total channel norm is at most twice its ideal charge. -/
theorem channel_budget (a q c Z₁ Z₂ ε label : ℝ)
    (ha : 4 * (Z₁ + Z₂) + 1 ≤ a) (hq : 1 ≤ q) (hc : 1 ≤ c)
    (hZ₁ : 0 ≤ Z₁) (hZ₂ : 0 ≤ Z₂) (hε : ε * Z₂ ≤ a / 4)
    (hlabel : label ≤ ε * q + 2) :
    label * Z₂ + q * (c * (a + Z₁) + Z₂) ≤ 2 * c * a * q := by
  have ha0 : 0 ≤ a := by linarith
  have hq0 : 0 ≤ q := by linarith
  have hca : a * q ≤ c * (a * q) :=
    le_mul_of_one_le_left (mul_nonneg ha0 hq0) hc
  have haq : a ≤ a * q := le_mul_of_one_le_right ha0 hq
  have hround : c * Z₁ + Z₂ ≤ c * (a / 4) := by
    have h₁ : Z₂ ≤ c * Z₂ := le_mul_of_one_le_left hZ₂ hc
    have h₂ : c * (Z₁ + Z₂) ≤ c * (a / 4) :=
      mul_le_mul_of_nonneg_left (by linarith) (by linarith)
    linarith only [h₁, h₂]
  have hlabel : label * Z₂ ≤ 3 / 4 * (c * (a * q)) := by
    calc
      label * Z₂ ≤ (ε * q + 2) * Z₂ := mul_le_mul_of_nonneg_right hlabel hZ₂
      _ = ε * Z₂ * q + 2 * Z₂ := by ring
      _ ≤ a / 4 * q + 2 * Z₂ := by linarith only [mul_le_mul_of_nonneg_right hε hq0]
      _ ≤ 3 / 4 * (c * (a * q)) := by linarith
  linarith only [hlabel, mul_le_mul_of_nonneg_right hround hq0]

/-- If the squared gap constant could grow like h/32, increasing h would
never admit rho = 1/2 in this sufficient stage condition. -/
theorem growing_constant (h : ℝ) : ¬ (1 + 8 * (h / 32) ≤ (1 / 2 : ℝ) ^ 2 * h) := by
  norm_num
  linarith

#print axioms channel_budget
#print axioms growing_constant
end Review.Pass13B
