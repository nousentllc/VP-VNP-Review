import Mathlib.Data.Real.Archimedean
import Mathlib.Order.ConditionallyCompleteLattice.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum

/-!
Cost-transfer contracts for constrained minimization. X and Y are feasible
point types, e.g. X = {a // feasible a}, so a function returning X carries
its feasibility evidence. Both may be empty. Numerical clocks, floating
point schedules and solver interfaces are outside this model.
-/
namespace W04

variable {X Y : Type*}

def AtMost (J : X → ℝ) (b : ℝ) : Prop := ∃ x, J x ≤ b
noncomputable def value (J : X → ℝ) : ℝ := sInf (Set.range J)
def Optimal (J : X → ℝ) (x : X) : Prop := ∀ u, J x ≤ J u

/-- One direction only. Projection can discard arbitrarily many trajectories. -/
theorem transport_threshold {J : X → ℝ} {K : Y → ℝ} {a b : ℝ}
    (p : X → Y) (hp : ∀ x, K (p x) ≤ J x + a) (h : AtMost J b) :
    AtMost K (b + a) := by
  obtain ⟨x,hx⟩ := h
  exact ⟨p x, by linarith [hp x]⟩

theorem threshold_iff {J : X → ℝ} {K : Y → ℝ} (p : X → Y) (f : Y → X)
    (hp : ∀ x, K (p x) ≤ J x) (hf : ∀ y, J (f y) ≤ K y) (b : ℝ) :
    AtMost J b ↔ AtMost K b := by
  constructor
  · rintro ⟨x,h⟩
    exact ⟨p x, (hp x).trans h⟩
  · rintro ⟨y,h⟩
    exact ⟨f y, (hf y).trans h⟩

theorem empty_threshold (b : ℝ) (J : Empty → ℝ) : ¬ AtMost J b := by
  rintro ⟨x,_⟩
  exact x.elim

/-- One reconstructed reduced optimum suffices; no lift for other y is needed. -/
theorem single_optimal_lift {J : X → ℝ} {K : Y → ℝ}
    (p : X → Y) (hp : ∀ x, K (p x) ≤ J x)
    (y : Y) (hy : Optimal K y) (x : X) (hx : J x ≤ K y) :
    J x = K y ∧ Optimal J x := by
  have hb (u : X) := (hy (p u)).trans (hp u)
  exact ⟨le_antisymm hx (hb x), fun u => hx.trans (hb u)⟩

/-- Every feasible cost bounds the infimum above when costs are bounded below. -/
theorem value_le_cost {J : X → ℝ} (bounded : BddBelow (Set.range J)) (x : X) :
    value J ≤ J x := csInf_le bounded ⟨x,rfl⟩

theorem attained_value {J : X → ℝ} (x : X) (h : Optimal J x) :
    value J = J x := by
  have lo : ∀ u ∈ Set.range J, J x ≤ u := by
    rintro _ ⟨z,rfl⟩
    exact h z
  exact le_antisymm (value_le_cost ⟨J x,lo⟩ x)
    (le_csInf ⟨J x, x, rfl⟩ lo)

theorem projected_value {J : X → ℝ} {K : Y → ℝ} {a : ℝ}
    (nx : Nonempty X) (bk : BddBelow (Set.range K))
    (p : X → Y) (hp : ∀ x, K (p x) ≤ J x + a) :
    value K ≤ value J + a := by
  have bound : value K - a ≤ value J := by
    apply le_csInf
    · obtain ⟨x⟩ := nx
      exact ⟨J x,x,rfl⟩
    · rintro _ ⟨x,rfl⟩
      have h := (value_le_cost bk (p x)).trans (hp x)
      linarith
  linarith

theorem infimum_sandwich {J : X → ℝ} {K : Y → ℝ} {a b : ℝ}
    (nx : Nonempty X) (ny : Nonempty Y)
    (bj : BddBelow (Set.range J)) (bk : BddBelow (Set.range K))
    (p : X → Y) (f : Y → X)
    (hp : ∀ x, K (p x) ≤ J x + a) (hf : ∀ y, J (f y) ≤ K y + b) :
    value K - a ≤ value J ∧ value J ≤ value K + b := by
  have h := projected_value nx bk p hp
  exact ⟨by linarith, projected_value ny bj f hf⟩

theorem exact_infimum {J : X → ℝ} {K : Y → ℝ}
    (nx : Nonempty X) (ny : Nonempty Y)
    (bj : BddBelow (Set.range J)) (bk : BddBelow (Set.range K))
    (p : X → Y) (f : Y → X) (hp : ∀ x, K (p x) ≤ J x)
    (hf : ∀ y, J (f y) ≤ K y) : value J = value K := by
  have h := infimum_sandwich (a:=0) (b:=0) nx ny bj bk p f
    (by simpa using hp) (by simpa using hf)
  exact le_antisymm (by simpa using h.2) (by simpa using h.1)

/-- Partial-lift variant. One returned point and its checked feasible
reconstruction suffice for its regret guarantee. A global sandwich does not follow. -/
theorem candidate_regret {J : X → ℝ} {K : Y → ℝ} {a b ε : ℝ}
    (bj : BddBelow (Set.range J)) (bk : BddBelow (Set.range K))
    (p : X → Y) (hp : ∀ x, K (p x) ≤ J x + a)
    (y : Y) (x : X) (hy : K y ≤ value K + ε) (hx : J x ≤ K y + b) :
    0 ≤ J x - value J ∧ J x - value J ≤ a + b + ε := by
  have h := projected_value ⟨x⟩ bk p hp
  exact ⟨sub_nonneg.mpr (value_le_cost bj x), by linarith⟩

theorem global_regret {J : X → ℝ} {K : Y → ℝ} {a b ε : ℝ}
    (bj : BddBelow (Set.range J)) (bk : BddBelow (Set.range K))
    (p : X → Y) (f : Y → X)
    (hp : ∀ x, K (p x) ≤ J x + a) (hf : ∀ y, J (f y) ≤ K y + b)
    (y : Y) (hy : K y ≤ value K + ε) :
    0 ≤ J (f y) - value J ∧ J (f y) - value J ≤ a + b + ε :=
  candidate_regret bj bk p hp y (f y) hy (hf y)

def Stage (J : X → ℝ) (S : Set X) (b : ℝ) := ∃ x ∈ S, J x ≤ b

theorem nested_stage {J : X → ℝ} {S : ℕ → Set X} (h : Monotone S)
    {k l : ℕ} (hkl : k ≤ l) {b : ℝ} (u : Stage J (S k) b) :
    Stage J (S l) b := by
  obtain ⟨x,hx,hc⟩ := u
  exact ⟨x,h hkl hx,hc⟩

theorem final_stage (J : X → ℝ) (S : ℕ → Set X) (last : ℕ)
    (h : S last = Set.univ) (b : ℝ) : Stage J (S last) b ↔ AtMost J b := by
  simp [Stage, AtMost, h]

/-- The validated fallback or previous incumbent persists if the trial is absent. -/
noncomputable def retain (J : X → ℝ) (old : X) (trial : Option X) : X :=
  match trial with
  | none => old
  | some x => if J x < J old then x else old

theorem retained_cost (J : X → ℝ) (old : X) (trial : Option X) :
    J (retain J old trial) ≤ J old := by
  cases trial with
  | none => exact le_rfl
  | some x =>
    simp only [retain]
    split_ifs with h
    · exact h.le
    · exact le_rfl

theorem combined_lower {J : X → ℝ} {L M : ℝ}
    (hl : ∀ x, L ≤ J x) (hm : ∀ x, M ≤ J x) :
    ∀ x, max L M ≤ J x := fun x => max_le (hl x) (hm x)

theorem gap_contract {J : X → ℝ} (x : X) {L : ℝ} (lower : ∀ u, L ≤ J u) :
    0 ≤ J x - value J ∧ J x - value J ≤ J x - L := by
  have h : ∀ v ∈ Set.range J, L ≤ v := by
    rintro _ ⟨u,rfl⟩
    exact lower u
  have hv : L ≤ value J := le_csInf ⟨J x,x,rfl⟩ h
  exact ⟨sub_nonneg.mpr (value_le_cost ⟨L,h⟩ x),by linarith⟩

theorem stop_with_tolerance {J : X → ℝ} (x : X) {L ε : ℝ}
    (lower : ∀ u, L ≤ J u) (stop : J x - L ≤ ε) :
    J x - value J ≤ ε := (gap_contract x lower).2.trans stop

/-- The cost infimum zero in both models coexists with an orphan reduced optimizer.
Both Bool and Unit are feasible point types, and the interface must equal false. -/
theorem equal_values_bad_optimizer :
    value (fun _ : Unit => (0:ℝ)) = value (fun _ : Bool => (0:ℝ)) ∧
    Optimal (fun _ : Bool => (0:ℝ)) true ∧
    ¬ ∃ x : Unit, (fun _ : Unit => false) x = true := by
  have hx := attained_value (J:=fun _ : Unit => (0:ℝ)) () (fun _ => le_rfl)
  have hy := attained_value (J:=fun _ : Bool => (0:ℝ)) true (fun _ => le_rfl)
  exact ⟨hx.trans hy.symm, fun _ => le_rfl, by simp⟩

/-- An open ray and a closed ray have equal infima but different threshold
attainment at zero, even though both sets are nonempty and bounded below. -/
theorem open_closed_infima :
    sInf (Set.Ioi (0:ℝ)) = sInf (Set.Ici (0:ℝ)) ∧
    (¬ ∃ x ∈ Set.Ioi (0:ℝ), x ≤ 0) ∧ ∃ y ∈ Set.Ici (0:ℝ), y ≤ 0 := by
  refine ⟨by simp, ?_, ⟨0,by simp,le_rfl⟩⟩
  rintro ⟨x,hx,h⟩
  exact (not_le_of_gt hx) h

end W04
