import AIPC
import Mathlib.Analysis.Convex.Basic
import Mathlib.Analysis.Normed.Module.Basic
import Mathlib.LinearAlgebra.AffineSpace.AffineMap
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Module

/- Exact line clipping for affine rows. u is the signed candidate residual,
   s the anchor slack. Never divide by zero on a violated anchored row. -/
namespace W05

noncomputable def rowNeed (u s : ℝ) : ℝ := if 0 < u then u / (u + s) else 0
noncomputable def need {I : Type*} (rows : List I) (u s : I → ℝ) : ℝ :=
  rows.foldr (fun i z => max (rowNeed (u i) (s i)) z) 0

theorem need_le_iff {I : Type*} (rs : List I) (u s : I → ℝ) (t : ℝ) :
    need rs u s ≤ t ↔ 0 ≤ t ∧ ∀ i ∈ rs, rowNeed (u i) (s i) ≤ t := by
  induction rs with
  | nil => simp [need]
  | cons i rs ih =>
    change max _ (need rs u s) ≤ t ↔ _
    rw [max_le_iff, ih]
    simp only [List.mem_cons, forall_eq_or_imp]
    tauto

theorem rowNeed_iff {u s t : ℝ} (hs : 0 ≤ s) (ht : 0 ≤ t) (ht1 : t ≤ 1) :
    rowNeed u s ≤ t ↔ (1-t)*u - t*s ≤ 0 := by
  by_cases h : 0 < u
  · simp only [rowNeed, if_pos h]
    rw [div_le_iff₀ (by linarith : 0 < u+s)]
    constructor <;> intro h' <;> linarith only [h',show (1-t)*u-t*s = u-t*(u+s) by ring]
  · simp only [rowNeed,if_neg h]
    have hn : (1-t)*u ≤ 0 := mul_nonpos_of_nonneg_of_nonpos (by linarith) (le_of_not_gt h)
    have hn' := mul_nonneg ht hs
    constructor <;> intro _ <;> linarith

theorem need_unit {I : Type*} (rs : List I) (u s : I → ℝ)
    (hs : ∀ i ∈ rs, 0 ≤ s i) : 0 ≤ need rs u s ∧ need rs u s ≤ 1 := by
  refine ⟨((need_le_iff _ _ _ _).1 le_rfl).1, (need_le_iff _ _ _ _).2 ⟨by norm_num,?_⟩⟩
  intro i hi
  exact (rowNeed_iff (hs i hi) (by norm_num : (0:ℝ) ≤ 1) le_rfl).2 (by simpa using hs i hi)

theorem minimal_fraction {I : Type*} (rs : List I) (u s : I → ℝ)
    (hs : ∀ i ∈ rs, 0 ≤ s i) {t : ℝ} (h0 : 0 ≤ t) (h1 : t ≤ 1) :
    need rs u s ≤ t ↔ ∀ i ∈ rs, (1-t)*u i-t*s i ≤ 0 := by
  rw [need_le_iff]
  constructor
  · intro h i hi
    exact (rowNeed_iff (hs i hi) h0 h1).1 (h.2 i hi)
  · intro h
    exact ⟨h0,fun i hi => (rowNeed_iff (hs i hi) h0 h1).2 (h i hi)⟩

theorem empty_rows {I : Type*} (u s : I → ℝ) : need [] u s = 0 := rfl

theorem boundary_fallback {I : Type*} (rs : List I) (u s : I → ℝ)
    (hs : ∀ i ∈ rs, 0 ≤ s i) {i : I} (hi : i ∈ rs) (hu : 0 < u i) (hz : s i = 0) :
    need rs u s = 1 := by
  have bounds := need_unit rs u s hs
  have h := ((need_le_iff rs u s _).1 le_rfl).2 i hi
  simp [rowNeed,hu,hz,ne_of_gt hu] at h
  exact le_antisymm bounds.2 h

/-- Row-specific violation envelopes can use boundary anchors. -/
theorem envelope {I : Type*} (rs : List I) (u h s : I → ℝ)
    (hs : ∀ i ∈ rs, 0 ≤ s i) (hu : ∀ i ∈ rs, u i ≤ h i) :
    need rs u s ≤ need rs h s := by
  obtain ⟨h0,h1⟩ := need_unit rs h s hs
  have feasible := (minimal_fraction rs h s hs h0 h1).1 le_rfl
  apply (minimal_fraction rs u s hs h0 h1).2
  intro i hi
  have w := mul_le_mul_of_nonneg_left (hu i hi) (sub_nonneg.mpr h1)
  linarith [feasible i hi]

theorem uniform_fraction {I : Type*} (rs : List I) (u s : I → ℝ) {bar sigma : ℝ}
    (hb : 0 ≤ bar) (hσ : 0 < sigma)
    (hu : ∀ i ∈ rs, 0 < u i → u i ≤ bar ∧ sigma ≤ s i) :
    need rs u s ≤ bar / (bar+sigma) := by
  have dp : 0 < bar+sigma := by linarith
  have h0 : 0 ≤ bar / (bar+sigma) := div_nonneg hb dp.le
  apply (need_le_iff _ _ _ _).2 ⟨h0,?_⟩
  intro i hi
  by_cases h : 0 < u i
  · obtain ⟨hbar,hsl⟩ := hu i hi h
    have dd : 0 < u i + s i := by linarith
    rw [rowNeed,if_pos h,div_le_div_iff₀ dd dp]
    nlinarith [mul_le_mul hbar hsl hσ.le hb]
  · simpa [rowNeed,h] using h0

section Vector
variable {V I G : Type*} [NormedAddCommGroup V] [NormedSpace ℝ V]
noncomputable def mix (t : ℝ) (x a : V) : V := (1-t) • x + t • a

theorem affine_mix (g : V →ᵃ[ℝ] ℝ) (x a : V) (t : ℝ) :
    g (mix t x a) = (1-t)*g x + t*g a := by
  simpa [mix,smul_eq_mul] using
    (Convex.combo_affine_apply (f:=g) (x:=x) (y:=a) (a:=1-t) (b:=t) (by ring))

theorem objective_identity (J : V →ᵃ[ℝ] ℝ) (x a : V) (t : ℝ) :
    J (mix t x a) - J x = t*(J a-J x) := by rw [affine_mix]; ring

theorem feasible_anchor (S : Set V) (conv : Convex ℝ S) (x a : V) (hx : x ∈ S) (ha : a ∈ S)
    (rows : List I) (g : I → V →ᵃ[ℝ] ℝ) (e : G → V →ᵃ[ℝ] ℝ)
    (hxa : ∀ j, e j x = 0) (hea : ∀ j, e j a = 0) (hga : ∀ i ∈ rows, g i a ≤ 0) :
    let t := need rows (fun i => g i x) (fun i => -g i a)
    mix t x a ∈ S ∧ (∀ j, e j (mix t x a) = 0) ∧ ∀ i ∈ rows, g i (mix t x a) ≤ 0 := by
  intro t
  have hs : ∀ i ∈ rows, 0 ≤ -g i a := fun i hi => neg_nonneg.mpr (hga i hi)
  obtain ⟨h0,h1⟩ := need_unit rows (fun i => g i x) (fun i => -g i a) hs
  have hh := (minimal_fraction rows (fun i => g i x) (fun i => -g i a) hs h0 h1).1 le_rfl
  refine ⟨conv hx ha (sub_nonneg.mpr h1) h0 (by ring),?_,?_⟩
  · intro j; rw [affine_mix,hxa,hea]; ring
  · intro i hi
    rw [affine_mix]
    simpa [t] using hh i hi

theorem equality_obstruction (e : V →ᵃ[ℝ] ℝ) (x a : V) (h : e a = 0) (t : ℝ) :
    e (mix t x a) = 0 ↔ t = 1 ∨ e x = 0 := by
  rw [affine_mix,h,mul_zero,add_zero,mul_eq_zero,sub_eq_zero]; tauto

theorem lipschitz_loss (J : V → ℝ) (x a : V) {L D t : ℝ} (hL : 0 ≤ L) (ht : 0 ≤ t)
    (hs : |J (mix t x a)-J x| ≤ L*‖mix t x a-x‖) (hd : ‖a-x‖ ≤ D) :
    max 0 (J (mix t x a)-J x) ≤ L*t*D := by
  have hm : mix t x a-x = t • (a-x) := by unfold mix; module
  have h := hs
  rw [hm,norm_smul,Real.norm_eq_abs,abs_of_nonneg ht] at h
  have h' := mul_le_mul_of_nonneg_left hd (mul_nonneg hL ht)
  apply max_le
  · exact mul_nonneg (mul_nonneg hL ht) ((norm_nonneg _).trans hd)
  · linarith [le_abs_self (J (mix t x a)-J x),show L*(t*‖a-x‖)=L*t*‖a-x‖ by ring]

/-- The manuscript equation with Lipschitz continuity required only on the
    chosen convex base, and strict margin required only on violated rows. -/
theorem uniform_loss (J : V → ℝ) (S : Set V) (hS : Convex ℝ S) (x a : V)
    (hx : x ∈ S) (ha : a ∈ S) (rows : List I) (u s : I → ℝ)
    (hs : ∀ i ∈ rows, 0 ≤ s i) {L D bar sigma : ℝ}
    (hL : 0 ≤ L) (hJ : ∀ z ∈ S, ∀ v ∈ S, |J z-J v| ≤ L*‖z-v‖)
    (hD : ‖a-x‖ ≤ D) (hb : 0 ≤ bar) (hp : 0 < sigma)
    (hbnd : ∀ i ∈ rows, 0 < u i → u i ≤ bar ∧ sigma ≤ s i) :
    max 0 (J (mix (need rows u s) x a)-J x) ≤ L*D*(bar/(bar+sigma)) := by
  obtain ⟨hn,hn1⟩ := need_unit rows u s hs
  have hm : mix (need rows u s) x a ∈ S :=
    hS hx ha (sub_nonneg.mpr hn1) hn (by ring)
  have h := lipschitz_loss J x a hL hn (hJ _ hm _ hx) hD
  have h' := mul_le_mul_of_nonneg_left (uniform_fraction rows u s hb hp hbnd)
    (mul_nonneg hL ((norm_nonneg _).trans hD))
  linarith [show L*(need rows u s)*D=L*D*(need rows u s) by ring]

end Vector

section Equality
variable {V W : Type*} [AddCommGroup V] [Module ℝ V] [AddCommGroup W] [Module ℝ W]

/-- A candidate-specific right inverse on the measured residual suffices. -/
theorem equality_repair (E : V →ₗ[ℝ] W) (R : W →ₗ[ℝ] V) (x : V) (d : W)
    (checked : E (R (d-E x)) = d-E x) : E (x + R (d-E x)) = d := by rw [map_add,checked]; abel

theorem right_inverse_repair (E : V →ₗ[ℝ] W) (R : W →ₗ[ℝ] V)
    (checked : Function.RightInverse R E) (x : V) (d : W) :
    E (x+R (d-E x)) = d := equality_repair E R x d (checked _)
end Equality

end W05
