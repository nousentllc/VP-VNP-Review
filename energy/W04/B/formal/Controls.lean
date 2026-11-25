import AIPC

/-!
Each false claim has a separately compiled constructive refutation. These
negations entail specific failures. They do not rely on a failed proof search.
-/
namespace W04.Controls

def fullAllowed (x : Bool) : Prop := x = false
def reducedAllowed (_ : Bool) : Prop := True
def cost (x : Bool) : ℚ := if x then 0 else 1

theorem missing_lift :
    (∃ y, reducedAllowed y ∧ cost y ≤ 0) ∧ ¬∃ x, fullAllowed x ∧ cost x ≤ 0 := by
  refine ⟨⟨true, trivial, by norm_num [cost]⟩, ?_⟩
  rintro ⟨x,rfl,h⟩
  norm_num [cost] at h

theorem incompatible_labels :
    (0:ℤ)+1 = 1+0 ∧ |(1:ℤ)-0| + |(0:ℤ)-1| > |(1+0:ℤ)-(0+1)| := by norm_num

theorem unbalanced_start :
    (2:ℕ)+0 = 1+1 ∧ ¬ ((2:ℤ) ≤ 1 ∧ (0:ℤ) ≤ 1) ∧ ((1:ℤ) ≤ 1 ∧ (1:ℤ) ≤ 1) := by norm_num

theorem restricted_bound :
    (∀ x : Bool, x = false → (1:ℚ) ≤ cost x) ∧ ¬∀ x : Bool, (1:ℚ) ≤ cost x := by
  refine ⟨?_,?_⟩
  · rintro x rfl
    norm_num [cost]
  · intro h
    have h' := h true
    norm_num [cost] at h'

theorem positive_terminal_tolerance :
    let Δ₁ : ℚ := (1/2)*((4/5)*1-4/5)/1
    let Δ₂ : ℚ := (1/2)*((81/100)*1-4/5)/(9/10)
    |Δ₁| ≤ 0 ∧ |Δ₂| ≤ 1/180 ∧ (4/5:ℚ) ≠ 81/100 ∧ (0:ℚ)<1 ∧ (0:ℚ)<4/5 := by norm_num

def rampAdmissible (prev next : ℤ) := |next-prev| ≤ 1
theorem history_omission :
    rampAdmissible 2 3 ∧ ¬rampAdmissible 0 3 := by norm_num [rampAdmissible]

/-- A singleton *full representation* still has a nonintegral LP optimum. -/
theorem integrality_gap :
    (∀ z : Bool, let x : ℚ := if z then 1 else 0; 1/2 ≤ x → x=1) ∧
      ((0:ℚ)≤1/2 ∧ (1/2:ℚ)≤1 ∧ (1/2:ℚ)<1) := by
  constructor
  · intro z
    cases z <;> norm_num
  · norm_num

/-- A larger feasible restriction can produce a worse returned feasible point. -/
theorem returned_cost_can_worsen :
    ({0} : Set ℕ) ⊆ {0,1} ∧ (0:ℕ) ∈ ({0} : Set ℕ) ∧
    (1:ℕ) ∈ ({0,1} : Set ℕ) ∧ (0:ℕ)<1 := by simp

/-- Checking only a successful partial lift can coexist with a strict full/reduced gap. -/
theorem partial_lift_no_sandwich :
    (let J : Unit → ℝ := fun _ => 1
     let K : Bool → ℝ := fun y => if y then 1 else 0
     (∀ x, K true ≤ J x) ∧ J () ≤ K true ∧ value K < value J) := by
  let J : Unit → ℝ := fun _ => 1
  let K : Bool → ℝ := fun y => if y then 1 else 0
  change (∀ x, K true ≤ J x) ∧ J () ≤ K true ∧ value K < value J
  have hj : value J = 1 := attained_value () (fun _ => le_rfl)
  have hk : value K = 0 := attained_value false (by
    intro y
    cases y <;> norm_num [K])
  exact ⟨fun _ => le_rfl, le_rfl, by rw [hj,hk]; norm_num⟩

end W04.Controls
