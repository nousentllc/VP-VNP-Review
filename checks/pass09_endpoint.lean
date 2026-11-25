import Mathlib.Algebra.Order.Archimedean.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

/-! Audit of the scalar conclusion of Theorem C.1 (Appendix C.3, p. 28).
From the lattice second-difference bound and fan claims (i)–(iv), obtain a
finite-T remainder and then the midpoint inequality. Fan construction, the
averaging, and the C.2 upper parallelogram inequality supply premises here.
Run with the release's Lean/mathlib environment: lean -j1 pass09_endpoint.lean
-/

namespace Pass09Endpoint

/-- This declaration is reproduced from Nc/Cat/Window.lean, lines 127–137,
    copyright 2026 Anthropic, PBC, Apache-2.0. The initial value φ stands
    for f(−1). The quadratic correction contributes +ω to the slope. -/
theorem conc {f : ℕ → ℝ} {φ ω : ℝ} (h0 : f 1 + φ ≤ 2 * f 0 + 2 * ω)
    (h : ∀ j, f (j + 2) + f j ≤ 2 * f (j + 1) + 2 * ω) (A : ℕ) :
    f A ≤ f 0 + A * (f 0 - φ + ω) + A ^ 2 * ω := by
  have key : ∀ j, f (j + 1) - f j ≤ (f 0 - φ + ω) + (2 * j + 1) * ω := by
    intro j
    induction j with
    | zero => norm_num; linarith
    | succ j ih => have := h j; push_cast; linarith
  induction A with
  | zero => simp
  | succ A ih => have := key A; push_cast; nlinarith

/-- Fix T and its fan. Compare upper and lower bounds at every A before
    invoking Archimedes. f(0) and Λ may depend on T, but never on A. -/
theorem shear_limit {f : ℕ → ℝ} {φ θ Λ Γ D B : ℝ}
    (first : f 1 + φ ≤ 2 * f 0 + 2 * (θ ^ 2 * Λ))
    (steps : ∀ j, f (j + 2) + f j ≤ 2 * f (j + 1) + 2 * (θ ^ 2 * Λ))
    (lower : ∀ A : ℕ, (A : ℝ) ^ 2 * (θ ^ 2 * Λ)
      + A * (θ * Γ - 4 * θ ^ 2 * D * (D + B)) ≤ f A)
    (horizontal : D ^ 2 ≤ φ)
    (diagonal : f 0 ≤ D ^ 2 * (1 - θ + θ ^ 2)) :
    θ * Γ - 4 * θ ^ 2 * D * (D + B) ≤ D ^ 2 * (-θ + θ ^ 2) + θ ^ 2 * Λ := by
  let δ := θ * Γ - 4 * θ ^ 2 * D * (D + B) - (f 0 - φ + θ ^ 2 * Λ)
  have bounded (A : ℕ) : (A : ℝ) * δ ≤ f 0 := by
    dsimp [δ]
    nlinarith [lower A, conc first steps A]
  have slope : δ ≤ 0 := by
    by_contra! positive
    obtain ⟨A, large⟩ := exists_nat_gt (f 0 / δ)
    rw [div_lt_iff₀ positive] at large
    linarith [bounded A]
  dsimp [δ] at slope
  linarith

/-- For each T divide out exactly one positive factor θ. A common upper
    bound on Λ suffices for the same coefficient at every mesh size. -/
theorem mesh_remainder {θ Λ Γ D B : ℝ} (positive : 0 < θ)
    (moment : Λ ≤ (D + B) ^ 2)
    (slope : θ * Γ - 4 * θ ^ 2 * D * (D + B) ≤ D ^ 2 * (-θ + θ ^ 2) + θ ^ 2 * Λ) :
    Γ + D ^ 2 ≤ θ * (6 * D ^ 2 + 6 * D * B + B ^ 2) := by
  refine le_of_mul_le_mul_left ?_ positive
  nlinarith [mul_le_mul_of_nonneg_left moment (sq_nonneg θ)]

/-- An Archimedean proof of the second limit. Neither D nor B is a divisor.
    The cutoff T ≥ 2 is absorbed by taking T = N+2. -/
theorem mesh_limit {Γ D B : ℝ}
    (bound : ∀ T : ℕ, 2 ≤ T → Γ + D ^ 2 ≤
      (6 * D ^ 2 + 6 * D * B + B ^ 2) / (T : ℝ)) : Γ ≤ -D ^ 2 := by
  by_contra! greater
  have positive : 0 < Γ + D ^ 2 := by linarith
  obtain ⟨N, large⟩ := exists_nat_gt ((6 * D ^ 2 + 6 * D * B + B ^ 2) / (Γ + D ^ 2))
  rw [div_lt_iff₀ positive] at large
  have cutoff : 2 ≤ N + 2 := by omega
  have meshpos : (0 : ℝ) < ((N + 2 : ℕ) : ℝ) := by positivity
  have upper := (le_div_iff₀ meshpos).mp (bound (N + 2) cutoff)
  push_cast at upper
  nlinarith

/-- Assemble both limits with the fan data selected *after* T is fixed.
    The fourth claim then holds at all A for those same data. -/
theorem two_limits {Γ D B : ℝ}
    (fan : ∀ T : ℕ, 2 ≤ T → ∃ (f : ℕ → ℝ) (φ Λ : ℝ),
      let θ : ℝ := 1 / T
      D ^ 2 ≤ φ ∧ f 0 ≤ D ^ 2 * (1 - θ + θ ^ 2) ∧ Λ ≤ (D + B) ^ 2 ∧
      f 1 + φ ≤ 2 * f 0 + 2 * (θ ^ 2 * Λ) ∧
      (∀ j, f (j + 2) + f j ≤ 2 * f (j + 1) + 2 * (θ ^ 2 * Λ)) ∧
      (∀ A : ℕ, (A : ℝ) ^ 2 * (θ ^ 2 * Λ)
        + A * (θ * Γ - 4 * θ ^ 2 * D * (D + B)) ≤ f A)) :
    Γ ≤ -D ^ 2 := by
  apply mesh_limit (B := B)
  intro T cutoff
  obtain ⟨f, φ, Λ, hφ, hdiag, moment, first, steps, lower⟩ := fan T cutoff
  have posT : 0 < T := by omega
  have posθ : 0 < 1 / (T : ℝ) := by positivity
  have slope := shear_limit first steps lower hφ hdiag
  simpa only [div_eq_mul_inv, one_mul, mul_one, mul_comm] using mesh_remainder posθ moment slope

#print axioms conc
#print axioms shear_limit
#print axioms mesh_remainder
#print axioms mesh_limit
#print axioms two_limits

end Pass09Endpoint
