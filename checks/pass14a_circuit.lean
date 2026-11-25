/-
Sections adapted from Paper/Rate.lean, lines 168–257 and 299–314.
Copyright (c) 2026 Anthropic, PBC. Released under Apache 2.0; see
primary/vp-vnp/LICENSE and NOTICE. Review changes: separate namespace,
the strict /12 target, the budget invocation, and its circuit-level caller.
-/
import Paper.Rate
import pass14a_margin

namespace Review.Pass14A
open Finset Nc Nc.Price Nc.CaseI Ov Paper

theorem price_bound12 {K : Type} [Field K] (hK : Flat K) {k : ℕ} (hk : 2 ≤ k) {ℓ s : ℕ}
    (hℓ : 100 * √k ≤ (ℓ : ℝ)) (hs : 1 ≤ s) (hfew : ∀ φ : Spec K (RPt k), SomeSetPays φ ℓ s) :
    (ℓ : ℝ) * (k * √k) / 12 < Real.logb 2 s := by
  classical
  have hk1 : (1 : ℝ) ≤ k := by exact_mod_cast (by omega : 1 ≤ k)
  have hhub : ∀ A : Finset (Fin k), ∃ x : EuclideanSpace ℝ (Fin k), A ∈ bal (univ : Finset (Fin k)) →
      ‖x‖ = 2 / (9 * √k) ∧
      ∑ e : Pr k, (dist (endPos e 0) (if e.1.1 ∈ A then x else -x) + dist (endPos e 1) (if e.1.2 ∈ A then x else -x)) ≤
        (k : ℝ) * (k - 1) / 2 - 4 / 81 * k := by
    intro A
    by_cases hA : A ∈ bal (univ : Finset (Fin k))
    · obtain ⟨-, h1, h2⟩ := mem_bal.1 hA
      obtain ⟨x, hx⟩ := prop_flat_rate_lengths (by omega) A h1 h2
      exact ⟨x, fun _ => hx⟩
    · exact ⟨0, fun h => absurd h hA⟩
  choose x hx using hhub
  set ε : ℝ := 1 / (1000 * k) with hε
  have hε0 : 0 < ε := by positivity
  let pos : RPt k → EuclideanSpace ℝ (Fin k) := Sum.elim ratePos fun z => if z.2 then x z.1 else -x z.1
  let e₀ : Pr k := ⟨(⟨0, by omega⟩, ⟨1, by omega⟩), by simp [Fin.lt_def]⟩
  have hPV : univ.image ratePos ⊆ univ.image pos := fun y hy => by
    obtain ⟨a, -, rfl⟩ := mem_image.1 hy
    exact mem_image.2 ⟨Sum.inl a, mem_univ _, rfl⟩
  obtain ⟨φ, c, hc, hφ, hg⟩ := prop_cube hK (univ.image pos) (univ.image ratePos) hPV
    ⟨ratePos ⟨e₀, 0⟩, mem_image_of_mem _ (mem_univ _)⟩ (fun y hy => by
      obtain ⟨a, -, rfl⟩ := mem_image.1 hy
      exact ⟨a.1.1.1, decide (a.2 = 0), rfl⟩) hε0
  -- pulled back to the ends and hubs regarded as different parties
  let place : RPt k → univ.image pos := fun z => ⟨pos z, mem_image_of_mem _ (mem_univ z)⟩
  let F := φ.pull place
  have hF : ∀ a b, |dist (pos a) (pos b) - c * F.e a b| < ε := fun a b => by
    rw [φ.pull_e, abs_sub_comm, ← Subtype.dist_eq (place a) (place b)]
    exact hφ _ _
  have hG : c * hexp F (Sum.inl : End k → RPt k) ≤ √k + ε := by
    refine le_of_eq_of_le ?_ hg
    rw [hexp_pull]
    refine congrArg _ ?_
    let atP : univ.image ratePos → univ.image pos := fun y => ⟨y.1, hPV y.2⟩
    have himg : univ.image (place ∘ (Sum.inl : End k → RPt k)) = univ.image atP := by
      ext y
      simp only [mem_image, mem_univ, true_and, Function.comp]
      constructor
      · rintro ⟨a, rfl⟩
        exact ⟨⟨ratePos a, mem_image_of_mem _ (mem_univ a)⟩, rfl⟩
      · rintro ⟨⟨z, hz⟩, rfl⟩
        obtain ⟨a, -, rfl⟩ := mem_image.1 hz
        exact ⟨a, rfl⟩
    rw [hexp_image φ (place ∘ Sum.inl), himg]
    exact (hexp_image φ atP).symm
  have hlog : 0 ≤ Real.logb 2 s := Real.logb_nonneg (by norm_num) (by exact_mod_cast hs)
  obtain ⟨A, hA, h1⟩ := hfew F
  obtain ⟨hxn, hxs⟩ := hx A hA
  refine margin12 hk1 hℓ hc hlog hε ?_ ?_ ?_ hG (by simpa only [hubCost, add_assoc] using h1)
  · rw [Finset.mul_sum]
    have e1 : (k : ℝ) * (k - 1) / 2 * (1 - ε) = ∑ _e : Pr k, (1 - ε) := by
      rw [← sum_pairs_one, Finset.sum_mul]
      simp
    rw [e1]
    refine Finset.sum_le_sum fun e _ => ?_
    have h2 := (abs_lt.1 (hF (Sum.inl ⟨e, 0⟩) (Sum.inl ⟨e, 1⟩))).2
    simp only [pos, Sum.elim_inl, ratePos, dist_endPos] at h2
    linarith
  · have h2 : ∀ (e : Pr k) (i : Fin 2), c * F.e (Sum.inl ⟨e, i⟩) (hubOf hubPt A ⟨e, i⟩) ≤
        dist (endPos e i) (if endNode e i ∈ A then x A else -x A) + ε := by
      intro e i
      have h3 := (abs_lt.1 (hF (Sum.inl ⟨e, i⟩) (hubOf hubPt A ⟨e, i⟩))).1
      simp only [pos, hubOf, hubPt, Sum.elim_inl, Sum.elim_inr, decide_eq_true_eq, ratePos] at h3
      simp only [hubOf, hubPt]
      linarith
    rw [Finset.mul_sum]
    calc ∑ e : Pr k, c * ∑ i, F.e (Sum.inl ⟨e, i⟩) (hubOf hubPt A ⟨e, i⟩) ≤
        ∑ e : Pr k, ((dist (endPos e 0) (if e.1.1 ∈ A then x A else -x A) +
          dist (endPos e 1) (if e.1.2 ∈ A then x A else -x A)) + 1 * (2 * ε)) := by
          refine Finset.sum_le_sum fun e _ => ?_
          rw [Fin.sum_univ_two, mul_add]
          refine (add_le_add (h2 e 0) (h2 e 1)).trans (le_of_eq ?_)
          simp only [endNode, if_true, Fin.one_eq_zero_iff, OfNat.ofNat_ne_one, if_false]
          ring
      _ ≤ _ := by
        rw [Finset.sum_add_distrib, ← Finset.sum_mul, sum_pairs_one]
        linarith
  · have h2 := (abs_lt.1 (hF (hubPt A true) (hubPt A false))).1
    simp only [pos, hubPt, Sum.elim_inr, if_true, Bool.false_eq_true, if_false] at h2
    have h3 : dist (x A) (-x A) = 4 / (9 * √k) := by
      rw [dist_eq_norm, sub_neg_eq_add, ← two_smul ℝ, norm_smul, hxn]
      norm_num
      ring
    rw [h3] at h2
    simp only [hubPt]
    linarith

theorem circuit12 {K : Type} [Field K] (hK : Flat K) {k : ℕ} (hk : 2 ≤ k) {ℓ s : ℕ}
    (hℓ : 100 * √k ≤ (ℓ : ℝ)) (hcomp : Computes (fkl K k ℓ) s) :
    (ℓ : ℝ) * (k * √k) / 12 < Real.logb 2 s := by
  classical
  have hs : 1 ≤ s := by
    obtain ⟨l, -, a, ha, -⟩ := hcomp
    omega
  refine price_bound12 hK hk hℓ hs fun φ => ?_
  have := bal_nonempty hk
  have : NeZero (Fintype.card (bal (univ : Finset (Fin k)))) := ⟨Fintype.card_ne_zero⟩
  have : Nonempty (RPt k) := ⟨hubPt ∅ true⟩
  -- the tensor of f is a sum of at most 2^k hub tensors
  have hsum := prop_flat_lower_sum hk hcomp (Sum.inl : End k → RPt k) hubPt
  rw [show ((fklTen K k ℓ).withVal fun z => cf univ (fkl K k ℓ) (tables z)) = fklTen K k ℓ from
    congrArg _ (funext fun z => (fklTen_val K z).symm)] at hsum
  exact someSetPays_of_few φ hs (lem_few φ _ _ (fklTen_onEnds K k ℓ) _ (hsum.reindex (balEnum k)))


theorem printed_circuit12 {K : Type} [Field K] (hK : Flat K) {k : ℕ} (hk : 2 ≤ k) {ℓ s : ℕ}
    (hℓ : 100 * √k ≤ (ℓ : ℝ)) (hcomp : Computes (fklExact K k ℓ) s) :
    (ℓ : ℝ) * (k * √k) / 12 < Real.logb 2 s :=
  circuit12 hK hk hℓ (fklExact_computes.1 hcomp)

#check @Review.Pass14A.printed_circuit12
#print axioms Review.Pass14A.printed_circuit12
end Review.Pass14A
