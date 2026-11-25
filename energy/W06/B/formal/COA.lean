import Mathlib.Data.Real.Archimedean
import Mathlib.Order.ConditionallyCompleteLattice.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring

namespace W06

universe u
variable {P : Type u}

/-- Feasible objective values in the single, declared contract. -/
def values (D : Set P) (J : P → ℝ) : Set ℝ := J '' D

theorem pointCeiling {u l j : ℝ} (h : l ≤ j) : u - j ≤ u - l := by linarith

theorem strictStop {u l j e : ℝ} (h : l ≤ j) (hg : u-l < e) : ¬ e ≤ u-j := by linarith

theorem weakStop {u l j e : ℝ} (h : l ≤ j) (hg : u-l ≤ e) : ¬ e < u-j := by linarith

theorem minInterval (D : Set P) (J : P → ℝ) (b : P) (hb : b ∈ D)
    (l : ℝ) (hl : ∀ p ∈ D, l ≤ J p) :
    0 ≤ J b - sInf (values D J) ∧ J b - sInf (values D J) ≤ J b - l := by
  have hV : l ∈ lowerBounds (values D J) := by rintro _ ⟨p, hp, rfl⟩; exact hl p hp
  have hB : J b ∈ values D J := ⟨b, hb, rfl⟩
  have h₁ := csInf_le (show BddBelow (values D J) from ⟨l, hV⟩) hB
  have h₂ := le_csInf (show (values D J).Nonempty from ⟨J b,hB⟩) hV
  exact ⟨by linarith, by linarith⟩

theorem maxInterval (D : Set P) (J : P → ℝ) (b : P) (hb : b ∈ D)
    (h : ℝ) (hh : ∀ p ∈ D, J p ≤ h) :
    0 ≤ sSup (values D J) - J b ∧ sSup (values D J) - J b ≤ h - J b := by
  have hV : h ∈ upperBounds (values D J) := by rintro _ ⟨p, hp, rfl⟩; exact hh p hp
  have hB : J b ∈ values D J := ⟨b, hb, rfl⟩
  have h₁ := le_csSup (show BddAbove (values D J) from ⟨h, hV⟩) hB
  have h₂ := csSup_le (show (values D J).Nonempty from ⟨J b,hB⟩) hV
  exact ⟨by linarith, by linarith⟩

theorem maxStops {h j b e : ℝ} (hj : j ≤ h) :
    (h-b < e → ¬ e ≤ j-b) ∧ (h-b ≤ e → ¬ e < j-b) := by constructor <;> intro ht <;> linarith

theorem feasibleGain (D : Set P) (J : P → ℝ) {candidate : P} (hc : candidate ∈ D)
    (hl : BddBelow (values D J)) (u : ℝ) : u-J candidate ≤ u-sInf (values D J) := by
  have := csInf_le hl (show J candidate ∈ values D J from ⟨candidate,hc,rfl⟩)
  linarith

/-- Lower bound under a potentially many-to-one realization map and objective domination. -/
theorem transferBound {Q : Type*} {D : Set P} {R : Set Q} (f : P → Q) (J : P → ℝ)
    (K : Q → ℝ) (l : ℝ) (hm : ∀ p ∈ D, f p ∈ R)
    (hd : ∀ p ∈ D, K (f p) ≤ J p) (hl : ∀ q ∈ R, l ≤ K q) : ∀ p ∈ D, l ≤ J p :=
  fun p hp => le_trans (hl _ (hm p hp)) (hd p hp)

theorem nestedInf (R F N C : Set P) (J : P → ℝ) (b : P) (hb : b ∈ C)
    (hCN : C ⊆ N) (hNF : N ⊆ F) (hFR : F ⊆ R) (l : ℝ) (hl : ∀ p ∈ R, l ≤ J p) :
    l ≤ sInf (values R J) ∧ sInf (values R J) ≤ sInf (values F J) ∧
    sInf (values F J) ≤ sInf (values N J) ∧ sInf (values N J) ≤ sInf (values C J) ∧
    sInf (values C J) ≤ J b := by
  have vR : l ∈ lowerBounds (values R J) := by rintro _ ⟨p,hp,rfl⟩; exact hl p hp
  have vf : values F J ⊆ values R J := Set.image_mono hFR
  have vn : values N J ⊆ values F J := Set.image_mono hNF
  have vc : values C J ⊆ values N J := Set.image_mono hCN
  have cb : J b ∈ values C J := ⟨b,hb,rfl⟩
  have neC : (values C J).Nonempty := ⟨_,cb⟩
  have br : BddBelow (values R J) := ⟨l,vR⟩
  exact ⟨le_csInf (((neC.mono vc).mono vn).mono vf) vR,
    csInf_le_csInf br ((neC.mono vc).mono vn) vf,
    csInf_le_csInf (br.mono vf) (neC.mono vc) vn,
    csInf_le_csInf ((br.mono vf).mono vn) neC vc,
    csInf_le (((br.mono vf).mono vn).mono vc) cb⟩

variable {S : Type*} [Fintype S]
noncomputable def total (w x : S → ℝ) : ℝ := ∑ s, w s * x s

theorem totalMono (w x y : S → ℝ) (hw : ∀ s, 0 ≤ w s) (h : ∀ s, x s ≤ y s) :
    total w x ≤ total w y :=
  Finset.sum_le_sum fun s _ => mul_le_mul_of_nonneg_left (h s) (hw s)

theorem weightedPanel (w u l j : S → ℝ) (hw : ∀ s, 0 ≤ w s) (hl : ∀ s, l s ≤ j s) :
    total w (fun s => u s-j s) ≤ total w (fun s => u s-l s) :=
  totalMono _ _ _ hw fun s => pointCeiling (hl s)

theorem partialPanel (known : S → Prop) [DecidablePred known] (w u l fallback j : S → ℝ)
    (hw : ∀ s, 0 ≤ w s) (hk : ∀ s, known s → l s ≤ j s)
    (hf : ∀ s, ¬known s → fallback s ≤ j s) :
    total w (fun s => u s-j s) ≤
      total w (fun s => u s - (if known s then l s else fallback s)) := by
  apply weightedPanel _ _ _ _ hw
  intro s
  split <;> rename_i h
  · exact hk s h
  · exact hf s h

theorem centeredPenalty (w l j penalty : S → ℝ) (hw : ∀ s, 0 ≤ w s)
    (hl : ∀ s, l s ≤ j s + penalty s) (hp : total w penalty ≤ 0) :
    total w l ≤ total w j := by
  have h := totalMono w l (fun s => j s + penalty s) hw hl
  have hx : total w (fun s => j s + penalty s) = total w j + total w penalty := by
    simp [total, mul_add, Finset.sum_add_distrib]
  linarith

omit [Fintype S] in
theorem riskCeiling (risk : (S → ℝ) → ℝ) (u l j : S → ℝ) (e : ℝ)
    (mono : ∀ x y : S → ℝ, (∀ s, x s ≤ y s) → risk x ≤ risk y)
    (cash : ∀ x : S → ℝ, risk (fun s => x s + e) = risk x + e)
    (hl : ∀ s, l s ≤ j s) (hu : ∀ s, u s-l s ≤ e) : risk u - risk j ≤ e := by
  have h := mono u (fun s => j s + e) (fun s => by have := hl s; have := hu s; linarith)
  rw [cash] at h
  linarith

/-- A quantity's unit and accounting horizon enter its type. -/
structure Amount (unit horizon : Type) where
  value : ℝ

theorem netBound {unit horizon : Type} (u l j k floor : Amount unit horizon)
    (hl : l.value ≤ j.value) (hf : floor.value ≤ k.value) :
    u.value-j.value-k.value ≤ u.value-l.value-floor.value := by linarith

theorem netStop {unit horizon : Type} (u l j k floor : Amount unit horizon)
    (hl : l.value ≤ j.value) (hf : floor.value ≤ k.value)
    (stop : u.value-l.value ≤ floor.value) : u.value-j.value-k.value ≤ 0 := by linarith

theorem discountedNet (w u l j k f : S → ℝ) (hw : ∀ s, 0 ≤ w s)
    (hl : ∀ s, l s ≤ j s) (hf : ∀ s, f s ≤ k s) :
    total w (fun s => u s-j s-k s) ≤ total w (fun s => u s-l s-f s) := by
  apply totalMono _ _ _ hw
  intro s
  have := hl s
  have := hf s
  linarith


/-- Observation labels identify scenarios indistinguishable at the action time.
    Include time in the index to represent multiple stage/history pairs. -/
def adapted {Ω O A : Type*} (obs : Ω → O) (p : Ω → A) : Prop :=
  ∀ s t, obs s = obs t → p s = p t

theorem ignoreInformation {Ω O F A : Type*} (coarse : Ω → O) (fine : Ω → F)
    (p : Ω → A) (refines : ∀ s t, fine s = fine t → coarse s = coarse t)
    (h : adapted coarse p) : adapted fine p :=
  fun s t hst => h s t (refines s t hst)

theorem operationalChain {Ω O A : Type*} (physical relaxed : Set (Ω → A))
    (obs : Ω → O) (deadline : (Ω → A) → Prop) (J : (Ω → A) → ℝ)
    (base : Ω → A) (hb : base ∈ physical) (hobs : adapted obs base)
    (hclock : deadline base) (incl : physical ⊆ relaxed) (l : ℝ)
    (hl : ∀ p ∈ relaxed, l ≤ J p) :
    let N := {p | p ∈ physical ∧ adapted obs p}
    let C := {p | p ∈ N ∧ deadline p}
    l ≤ sInf (values relaxed J) ∧ sInf (values relaxed J) ≤ sInf (values physical J) ∧
    sInf (values physical J) ≤ sInf (values N J) ∧ sInf (values N J) ≤ sInf (values C J) ∧
    sInf (values C J) ≤ J base := by
  dsimp only
  exact nestedInf relaxed physical {p | p ∈ physical ∧ adapted obs p}
    {p | (p ∈ physical ∧ adapted obs p) ∧ deadline p} J base ⟨⟨hb,hobs⟩,hclock⟩ (fun _ hp => hp.1)
    (fun _ hp => hp.1) incl l hl

theorem contractCost (D : Set P) (J service risk stock : P → ℝ) (b p : P)
    (l : ℝ) (hl : ∀ a ∈ D, service a = service b → risk a ≤ risk b →
        stock a = stock b → l ≤ J a)
    (hp : p ∈ D) (hs : service p = service b) (hr : risk p ≤ risk b)
    (ht : stock p = stock b) : J b-J p ≤ J b-l :=
  pointCeiling (hl p hp hs hr ht)


/-- At the boundary, failure to attain the certified floor can separately justify strict exclusion. -/
theorem strictAtNonattainment (D : Set P) (J : P → ℝ) (l u e : ℝ)
    (hl : ∀ p ∈ D, l ≤ J p) (miss : ¬∃ p ∈ D, J p = l) (hg : u-l ≤ e) :
    ∀ p ∈ D, ¬e ≤ u-J p := by
  intro p hp
  have hn : J p ≠ l := fun he => miss ⟨p,hp,he⟩
  have hh := hl p hp
  rcases lt_or_eq_of_le hh with hlt | heq
  · linarith
  · exact False.elim (hn heq.symm)

/-- Accounting for certified one-sided baseline and lower-model discrepancies. -/
theorem enclosureCeiling (baseline candidate baselineUpper modelCost lower allowance : ℝ)
    (hb : baseline ≤ baselineUpper) (hl : lower ≤ modelCost)
    (transfer : modelCost ≤ candidate + allowance) :
    baseline - candidate ≤ baselineUpper - lower + allowance := by linarith

theorem infoPanelInf (D : Set P) (b : P) (hb : b ∈ D) (w l : S → ℝ)
    (j penalty : P → S → ℝ) (hw : ∀ s, 0 ≤ w s)
    (hl : ∀ p ∈ D, ∀ s, l s ≤ j p s + penalty p s)
    (hp : ∀ p ∈ D, total w (penalty p) ≤ 0) :
    0 ≤ total w (j b) - sInf (values D (fun p => total w (j p))) ∧
    total w (j b) - sInf (values D (fun p => total w (j p))) ≤ total w (j b)-total w l :=
  minInterval D _ b hb _ (fun p h => centeredPenalty _ _ _ _ hw (hl p h) (hp p h))

end W06
