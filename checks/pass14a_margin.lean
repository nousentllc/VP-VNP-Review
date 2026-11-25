import Mathlib

namespace Review.Pass14A

/-- A strict improvement of the scalar E.10 comparison. The four price bounds
and the cut inequality are the inputs of Paper.rate_numbers14 (Rate.lean 123–126). -/
theorem margin12 {k ell c delta S₁ S₂ S₃ G logL : ℝ}
    (hk : 1 ≤ k) (hell : 100 * √k ≤ ell)
    (hc : 0 ≤ c) (hlog : 0 ≤ logL) (hd : delta = 1 / (1000 * k))
    (hwire : k * (k - 1) / 2 * (1 - delta) ≤ c * S₁)
    (houter : c * S₂ ≤ k * (k - 1) / 2 - 4 / 81 * k + k * (k - 1) * delta)
    (hmiddle : c * S₃ ≤ 4 / (9 * √k) + delta)
    (hlabel : c * G ≤ √k + delta)
    (hcut : ell * S₁ ≤ k * G + ell * S₂ + S₃ * logL) :
    ell * (k * √k) / 12 < logL := by
  have hkpos : 0 < k := by linarith
  have hr : 1 ≤ √k := Real.one_le_sqrt.mpr hk
  have hrpos : 0 < √k := by linarith
  have hsquare := Real.sq_sqrt hkpos.le
  have hlen : 0 < ell := by linarith
  have hdk : delta * k = 1 / 1000 := by rw [hd]; field_simp
  have hdsmall : delta * √k ≤ 1 / 1000 := by
    have hle : √k ≤ k := by nlinarith [mul_nonneg (Real.sqrt_nonneg k) (sub_nonneg.mpr hr)]
    have hpos : 0 ≤ delta := by rw [hd]; positivity
    exact (mul_le_mul_of_nonneg_left hle hpos).trans hdk.le
  have label : k * (√k + delta) ≤ ell * k * (1 / 100 + 1 / 10000) := by
    nlinarith only [mul_le_mul_of_nonneg_right hell hkpos.le, hdk,
      show 100 ≤ ell * k by nlinarith [mul_nonneg (sub_nonneg.mpr hk) hlen.le]]
  have err : k * (k - 1) * delta * (3 / 2) ≤ 3 * k / 2000 := by
    calc
      k * (k - 1) * delta * (3 / 2) = (delta*k) * (k-1) * (3/2) := by ring
      _ ≤ _ := by rw [hdk]; linarith
  have coef : (4 / (9 * √k) + delta) * √k ≤ 4/9 + 1/1000 := by
    have h : 4 / (9 * √k) * √k = 4/9 := by field_simp
    rw [add_mul, h]; linarith
  have hbudget :
      ell * k * (4/81 - 3/2000 - 1/100 - 1/10000) ≤ (4/(9*√k) + delta) * logL := by
    nlinarith only [mul_le_mul_of_nonneg_left hcut hc, mul_le_mul_of_nonneg_left hwire hlen.le,
      mul_le_mul_of_nonneg_left houter hlen.le, mul_le_mul_of_nonneg_right hmiddle hlog,
      mul_le_mul_of_nonneg_left hlabel hkpos.le, label, mul_le_mul_of_nonneg_left err hlen.le]
  have combined :
      ell * k * √k * (4/81 - 3/2000 - 1/100 - 1/10000) ≤ (4/9 + 1/1000) * logL := by
    nlinarith only [mul_le_mul_of_nonneg_right hbudget hrpos.le, mul_le_mul_of_nonneg_right coef hlog]
  have hpos : 0 < ell * k * √k := by positivity
  linarith only [combined, hpos]

#print axioms margin12
end Review.Pass14A
