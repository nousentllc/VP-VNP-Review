import Mathlib.Data.Real.Archimedean
import Mathlib.Order.ConditionallyCompleteLattice.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum

namespace W07.Info

variable {P S T H A : Type*}

/-- D t i j requires equality of commands on paths i and j at t. -/
def relaxedDomain (physical : Set (T → S → A)) (D : T → S → S → Prop) :
    Set (T → S → A) := {z | z ∈ physical ∧ ∀ t i j, D t i j → z t i = z t j}

theorem strengthen (F : Set (T → S → A)) (D E : T → S → S → Prop)
    (h : ∀ t i j, D t i j → E t i j) : relaxedDomain F E ⊆ relaxedDomain F D :=
  fun _ hz => ⟨hz.1, fun t i j hij => hz.2 t i j (h t i j hij)⟩

theorem projection (F : Set (T → S → A)) (D : T → S → S → Prop)
    (hist : T → S → H) (policy : T → H → A)
    (cover : ∀ t i j, D t i j → hist t i = hist t j)
    (phy : (fun t s => policy t (hist t s)) ∈ F) :
    (fun t s => policy t (hist t s)) ∈ relaxedDomain F D :=
  ⟨phy, fun t i j hij => congrArg (policy t) (cover t i j hij)⟩

noncomputable def value (J : P → ℝ) (F : Set P) : ℝ := sInf (J '' F)

theorem lower_transfer (J : P → ℝ) {F : Set P} {l : ℝ}
    (hn : F.Nonempty) (hl : ∀ p ∈ F, l ≤ J p) : l ≤ value J F :=
  le_csInf (hn.image J) (by rintro _ ⟨p,hp,rfl⟩; exact hl _ hp)

theorem restrict_value (J : P → ℝ) {large small : Set P}
    (hs : small ⊆ large) (hn : small.Nonempty) (hb : BddBelow (J '' large)) :
    value J large ≤ value J small := csInf_le_csInf hb (hn.image J) (Set.image_mono hs)

theorem nested_information (J : P → ℝ) {pf d₁ d₂ causal deadline : Set P}
    {b : P} (h₀ : d₁ ⊆ pf) (h₁ : d₂ ⊆ d₁) (h₂ : causal ⊆ d₂)
    (h₃ : deadline ⊆ causal) (hb : b ∈ deadline) (lower : BddBelow (J '' pf)) :
    value J pf ≤ value J d₁ ∧ value J d₁ ≤ value J d₂ ∧
    value J d₂ ≤ value J causal ∧ value J causal ≤ value J deadline ∧
    value J deadline ≤ J b := by
  have hD : deadline.Nonempty := ⟨b,hb⟩
  have hC := hD.mono h₃
  have hB := hC.mono h₂
  have hA := hB.mono h₁
  have b₁ := lower.mono (Set.image_mono h₀)
  have b₂ := b₁.mono (Set.image_mono h₁)
  have b₃ := b₂.mono (Set.image_mono h₂)
  exact ⟨restrict_value J h₀ hA lower, restrict_value J h₁ hB b₁,
    restrict_value J h₂ hC b₂, restrict_value J h₃ hD b₃,
    csInf_le (b₃.mono (Set.image_mono h₃)) ⟨b,hb,rfl⟩⟩

theorem max_floor {a b j : ℝ} (ha : a ≤ j) (hb : b ≤ j) : max a b ≤ j :=
  max_le ha hb

theorem strict_stop {U L J ε : ℝ} (floor : L ≤ J) (test : U-L < ε) :
    ¬ ε ≤ U-J := by linarith

theorem equality_stop_nonattained {U L J ε : ℝ} (h : L < J) (e : U-L = ε) :
    ¬ ε ≤ U-J := by linarith

theorem covered_weight [Fintype S] (w u j l b : S → ℝ) (valid : S → Prop)
    [DecidablePred valid] (mass : ∀ s, 0 ≤ w s) (base : ∀ s, u s ≤ b s)
    (localFloor : ∀ s, valid s → l s ≤ j s)
    (backup : S → ℝ) (other : ∀ s, ¬valid s → backup s ≤ j s) :
    ∑ s, w s*(u s - j s) ≤ ∑ s, w s*(b s - if valid s then l s else backup s) := by
  apply Finset.sum_le_sum
  intro s _
  apply mul_le_mul_of_nonneg_left _ (mass s)
  have := base s
  split <;> rename_i hv
  · have := localFloor s hv; linarith
  · have := other s hv; linarith

/-- Different types permit many-to-one engineering projections. The lower bound must
cover the entire relaxed domain and the penalized cost must dominate in the proper direction. -/
theorem penalty_transfer {Q : Type*} (causal : Set P) (relax : Set Q) (map : P → Q)
    (J : P → ℝ) (F M : Q → ℝ) (L : ℝ) (projection : ∀ p ∈ causal, map p ∈ relax)
    (cost : ∀ p ∈ causal, F (map p) ≤ J p) (center : ∀ p ∈ causal, M (map p) ≤ 0)
    (floor : ∀ z ∈ relax, L ≤ F z + M z) : ∀ p ∈ causal, L ≤ J p := by
  intro p hp
  have h := floor _ (projection p hp)
  have := cost p hp
  have := center p hp
  linarith

/-- An exact conditional mean at each history for *each* selected action implies
uniform centering. H can encode endogenous state/history; zero-weight cells need no division. -/
theorem history_centering [Fintype S] [Fintype H] [DecidableEq H]
    (w : S → ℝ) (hist : S → H) (inc : S → A → ℝ) (choose : H → A)
    (center : ∀ h a, (∑ s, if hist s = h then w s * inc s a else 0) = 0) :
    (∑ s, w s * inc s (choose (hist s))) = 0 := by
  calc
    _ = ∑ s, ∑ h, (if hist s = h then w s * inc s (choose h) else 0) := by simp
    _ = ∑ h, ∑ s, (if hist s = h then w s * inc s (choose h) else 0) := Finset.sum_comm
    _ = 0 := by simp [center]

theorem accumulated_centering [Fintype S] [Fintype T] (w : S → ℝ) (m : T → S → ℝ)
    (center : ∀ t, (∑ s, w s * m t s) = 0) :
    (∑ s, w s * ∑ t, m t s) = 0 := by
  simp only [Finset.mul_sum]
  rw [Finset.sum_comm]
  simp [center]


/-- A uniform, checked upper bound on centering residuals can be debited.
The bound is allowed to be conservative; estimated bias on a fitted policy is insufficient. -/
theorem penalty_debit {P Q : Type*} (causal : Set P) (relax : Set Q) (map : P → Q)
    (J : P → ℝ) (F M : Q → ℝ) (L η : ℝ) (cover : ∀ p ∈ causal, map p ∈ relax)
    (cost : ∀ p ∈ causal, F (map p) ≤ J p) (bias : ∀ p ∈ causal, M (map p) ≤ η)
    (floor : ∀ z ∈ relax, L ≤ F z + M z) : ∀ p ∈ causal, L - η ≤ J p := by
  intro p hp
  have := floor _ (cover p hp)
  have := cost p hp
  have := bias p hp
  linarith

theorem history_upper [Fintype S] [Fintype H] [DecidableEq H]
    (w : S → ℝ) (hist : S → H) (inc : S → A → ℝ) (choose : H → A) (cap : H → ℝ)
    (valid : ∀ h a, (∑ s, if hist s = h then w s * inc s a else 0) ≤ cap h) :
    (∑ s, w s * inc s (choose (hist s))) ≤ ∑ h, cap h := by
  calc
    _ = ∑ s, ∑ h, (if hist s = h then w s * inc s (choose h) else 0) := by simp
    _ = ∑ h, ∑ s, (if hist s = h then w s * inc s (choose h) else 0) := Finset.sum_comm
    _ ≤ ∑ h, cap h := Finset.sum_le_sum fun h _ => valid h (choose h)

end W07.Info
