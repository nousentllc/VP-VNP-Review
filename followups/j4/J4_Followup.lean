import Paper.Cuts

/-!
The setup and code-size argument of `j4_iterate_bounds` adapt lines 460–540 of
`Paper/Cuts.lean` at anthropics/formal-math commit
11b6c7e3c927df2658f513b6b68ea7f8929c62c5.
Copyright (c) 2026 Anthropic, PBC for the adapted source.
SPDX-License-Identifier: Apache-2.0
The final budget comparisons retain slack from the published induction.
-/

namespace Review.J4

open Finset NS1 Nc.Vp Nc.Tow Paper
open Nc.Tower (ee)
open _root_.NS1.Tree

variable {A : Type} [CommRing A]

theorem j4_iterate_bounds {θ : List Bool → A} (hθ : Generates θ) {h' : ℕ} [NeZero h']
    (VL : VLaws A (cNear (h := h')) (dNear (h := h')) 1 (2 ^ ee h')) (h3 : 3 ≤ h')
    (hgain : 1 + 8 * VL.C₁ ≤ (h' : ℝ) / 4) :
    ∃ H C₀ v₀ : ℕ, 272 ≤ H ∧ 16 ∣ H ∧ ∀ v, v₀ ≤ v → ∀ α τ s, lg v ^ (C₀ * α) ≤ v → v ^ H ≤ τ → τ ≤ v ^ (H * α) →
      s * v ^ 48 ≤ τ → ∃ G : Tree, G.size ≤ v ^ H ∧
        CutD θ τ s (v ^ H) (v ^ (H - 47)) (τ * v / v ^ H) (τ / v ^ 47) G := by
  obtain ⟨a₀, C, v₀, hv₀⟩ := thm_onecut hθ VL h3 hgain
  obtain ⟨h, hhdef⟩ : ∃ h, h = a₀ + 217 := ⟨_, rfl⟩
  have hh : a₀ + 200 ≤ 16 * h := by omega
  refine ⟨16 * h, (3 * C + 4) * (32 * h + 2), v₀ + 2 ^ 100 + 4000, by omega, dvd_mul_right 16 h,
    fun v hv α τ s hlog hτ hτα hs => ?_⟩
  obtain ⟨r, hr⟩ : ∃ r, r = 16 * h * α := ⟨_, rfl⟩
  have hv1 : 4000 ≤ v := by omega
  have hv0 : 1 ≤ v := by omega
  have hl100 : 100 ≤ lg v := (Nat.le_succ _).trans (le_lg_of_two_pow_le (by omega))
  have hα : 1 ≤ α := by
    by_contra hne
    have h0 : α = 0 := by omega
    rw [h0, Nat.mul_zero, pow_zero] at hτα
    have : v ≤ v ^ (16 * h) := Nat.le_self_pow (by omega) v
    omega
  have hαl : 2 * r ≤ lg v := by
    refine le_trans ?_ (le_lg_of_lg_pow_le (by omega) hlog)
    rw [hr, Nat.mul_assoc (3 * C + 4), ← Nat.mul_assoc 2]
    refine le_trans (Nat.mul_le_mul_right _ (?_ : 2 * (16 * h) ≤ 32 * h + 2)) (Nat.le_mul_of_pos_left _ (by omega))
    omega
  obtain ⟨q4, hq4⟩ : ∃ n, n = 4 ^ (r + 1) := ⟨_, rfl⟩
  obtain ⟨Λ, hΛ⟩ : ∃ n, n = lg v ^ (C + 1) := ⟨_, rfl⟩
  have hl2 := lg_ge_two (show 4 ≤ v by omega)
  have hΛ2 : 2 ≤ Λ := by
    rw [hΛ]
    exact hl2.trans (Nat.le_self_pow (by omega) _)
  have hΛ1 : 1 ≤ Λ := by omega
  have hX : (100 * Λ ^ 3) ^ (r + 1) ≤ v := hΛ ▸ hr ▸ polylog_loss_le hl100 hα hlog
  have hq4v : q4 ≤ v := by
    refine hq4 ▸ le_trans (Nat.pow_le_pow_left ?_ _) hX
    exact le_trans (by norm_num) (Nat.le_mul_of_pos_right 100 (Nat.pow_pos (show 0 < Λ by omega)))
  have hX1 : 100 * Λ ^ 3 ≤ v := (Nat.le_self_pow (by omega) _).trans hX
  have hL3 : Λ ≤ Λ ^ 3 := Nat.le_self_pow (by norm_num) Λ
  have hL2 : Λ ^ 2 ≤ Λ ^ 3 := Nat.pow_le_pow_right hΛ1 (by norm_num)
  have hat0 : OneCutAt θ v a₀ (16 * h * α) (lg v ^ C) := by
    intro τ' s' k' h1 h2 h3' h4 h5
    refine hv₀ v (by omega) τ' s' k' h1 ?_ h3' h4 h5
    have h6 : lg τ' ≤ 16 * h * α * lg v := (lg_mono h2).trans (lg_pow_le (Nat.mul_pos (by omega) hα))
    have h7 : 4 * (16 * h * α) ≤ lg v := by
      refine le_trans ?_ (le_lg_of_lg_pow_le (by omega) hlog)
      have h8 : 4 * (16 * h) * α ≤ (3 * C + 4) * (32 * h + 2) * α := by
        refine Nat.mul_le_mul_right _ ?_
        calc 4 * (16 * h) ≤ 4 * (32 * h + 2) := by omega
          _ ≤ _ := Nat.mul_le_mul_right _ (by omega)
      calc 4 * (16 * h * α) = 4 * (16 * h) * α := by ring
        _ ≤ _ := h8
    calc 4 * lg τ' ≤ 4 * (16 * h * α * lg v) := Nat.mul_le_mul_left _ h6
      _ = 4 * (16 * h * α) * lg v := by ring
      _ ≤ lg v * lg v := Nat.mul_le_mul_right _ h7
      _ = lg v ^ 2 := by ring
  have hat : OneCutAt θ v a₀ (16 * h * α) Λ := OneCutAt.mono (Λ := lg v ^ C) hat0 (by
    rw [hΛ]
    exact Nat.pow_le_pow_right (by omega) (Nat.le_succ C))
  have pmono : ∀ {a b}, a ≤ b → v ^ a ≤ v ^ b := fun h => Nat.pow_le_pow_right hv0 h
  have ppos : ∀ a, 0 < v ^ a := fun a => Nat.pow_pos (by omega)
  obtain ⟨G, P, t, s', hcut, hP, ht, hs', hG⟩ := thm_cut_iterate hat (by omega) hΛ2 (by omega) (H := 16 * h) (by omega) (by omega)
    r τ s 1 hτ hτα (by
      calc τ * Λ < τ * v := Nat.mul_lt_mul_of_pos_left (by omega) (lt_of_lt_of_le (ppos _) hτ)
        _ ≤ v ^ (16 * h * α) * v := Nat.mul_le_mul_right _ hτα
        _ = v ^ (r + 1) := by rw [hr, pow_succ]
        _ ≤ v ^ (16 * h + (64 + 62 * r)) := pmono (by omega)
        _ = _ := pow_add _ _ _) (by simpa using hs) le_rfl (by rw [one_mul, ← hq4]; omega)
  have e8 : (8 * Λ) ^ (r + 1) ≤ v := (Nat.pow_le_pow_left (by omega) _).trans hX
  have e4 : (4 * Λ ^ 2) ^ (r + 1) ≤ v := (Nat.pow_le_pow_left (by omega) _).trans hX
  refine ⟨G, ?_, hcut.mono le_rfl ?_ ((Nat.le_div_iff_mul_le (ppos _)).2 ?_) ((Nat.le_div_iff_mul_le (ppos _)).2 ?_)⟩
  · have hq : 4 ^ r ≤ v := (Nat.pow_le_pow_right (by norm_num) (Nat.le_succ r)).trans (by rw [← hq4]; omega)
    calc G.size ≤ 4 ^ r * (v ^ a₀ + 3000) := hG
      _ ≤ v * (v ^ a₀ + v) := Nat.mul_le_mul hq (by omega)
      _ ≤ v * (v ^ (a₀ + 1) + v ^ (a₀ + 1)) := Nat.mul_le_mul_left _ (Nat.add_le_add (pmono (Nat.le_succ _)) (by
          calc v = v ^ 1 := (pow_one v).symm
            _ ≤ _ := pmono (by omega)))
      _ = 2 * v ^ (a₀ + 2) := by rw [pow_succ v (a₀ + 1)]; ring
      _ ≤ v * v ^ (a₀ + 2) := Nat.mul_le_mul_right _ (by omega)
      _ = v ^ (a₀ + 3) := by rw [pow_succ v (a₀ + 2)]; ring
      _ ≤ v ^ (16 * h) := pmono (by omega)

  · have hs47 : s' * v ^ 48 ≤ v ^ (16 * h - 47) * v ^ 48 := by
      calc s' * v ^ 48 ≤ 1 * v ^ (16 * h) * (8 * Λ) ^ (r + 1) := hs'
        _ ≤ v ^ (16 * h) * v := by simpa only [one_mul] using Nat.mul_le_mul_left (v ^ (16 * h)) e8
        _ = v ^ (16 * h - 47) * v ^ 48 := by
          rw [← pow_add, ← pow_succ]
          congr 1
          omega
    exact Nat.le_of_mul_le_mul_right hs47 (ppos 48)
  · exact hP.trans (Nat.mul_le_mul_left _ e4)
  · have htv : t * v ^ 47 * v ≤ τ * v := by
      simpa only [pow_succ v 47, mul_assoc, one_mul] using
        (ht.trans (Nat.mul_le_mul_left (1 * τ) hX))
    exact Nat.le_of_mul_le_mul_right htv (by omega)

/-- Evaluate the two principal K.5 budgets with the stronger J.4 bounds. -/
theorem k5_listing_and_traversal {v H e t n : ℕ} (hv : 31 ≤ v) (hH : 16 ≤ H)
    (he : 47 ≤ e + 9) (hn : H ≤ e + 10)
    (ht : t * v ^ 47 ≤ v ^ (e + 9)) (hcount : n * v ^ H ≤ v ^ (e + 10)) :
    t ≤ v ^ (e - 38) ∧
      n ≤ v ^ (e + 10 - H) ∧
      (v ^ (H - 16) + 30) * n ≤ v ^ (e - 5) := by
  have hpos (a : ℕ) : 0 < v ^ a := Nat.pow_pos (by omega)
  have t_eq : e + 9 = (e - 38) + 47 := by omega
  have n_eq : e + 10 = (e + 10 - H) + H := by omega
  rw [t_eq, pow_add] at ht
  rw [n_eq, pow_add] at hcount
  have hpieces := Nat.le_of_mul_le_mul_right hcount (hpos H)
  refine ⟨Nat.le_of_mul_le_mul_right ht (hpos 47), hpieces, ?_⟩
  have small : 30 ≤ 30 * v ^ (H - 16) := by
    simpa using Nat.mul_le_mul_left 30 (Nat.one_le_pow _ _ (by omega : 0 < v))
  have exponents : (H - 16) + (e + 10 - H) = e - 6 := by omega
  calc
    (v ^ (H - 16) + 30) * n ≤ (31 * v ^ (H - 16)) * n := by
      exact Nat.mul_le_mul_right n (by rw [show 31 = 1 + 30 by decide, add_mul, one_mul]; omega)
    _ ≤ (v * v ^ (H - 16)) * v ^ (e + 10 - H) :=
      Nat.mul_le_mul (Nat.mul_le_mul_right _ hv) hpieces
    _ = v ^ (e - 5) := by
      rw [mul_assoc, ← pow_add, exponents, ← pow_succ']
      congr 1
      omega

end Review.J4

#print axioms Review.J4.j4_iterate_bounds
#print axioms Review.J4.k5_listing_and_traversal
