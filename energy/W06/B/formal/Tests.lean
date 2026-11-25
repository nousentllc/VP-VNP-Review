import COA
import BoxDual

namespace W06.Tests

theorem equalityTarget : (10:ℝ)-9 ≤ 1 ∧ (1:ℝ) ≤ 10-9 := by norm_num

theorem nonattainment : sInf (Set.Ioi (0:ℝ)) = 0 ∧
    (∀ x ∈ Set.Ioi (0:ℝ), 1-x < 1) := by
  exact ⟨csInf_Ioi, fun x hx => by change 0 < x at hx; linarith⟩

/-- The only feasible cost is five; a valid zero floor creates a positive ceiling. -/
theorem slackBound : ((0:ℝ) ≤ 5 ∧ 0 < (5:ℝ)-0) ∧ ((5:ℝ)-5 = 0) := by norm_num

/-- Same service and stock can be produced at radically different costs. -/
theorem serviceEconomics (v : ℝ) (hv : 0 < v) :
    ∃ (service cost : Bool → ℝ), service true = service false ∧ cost false-cost true = v ∧
    0 < cost false-cost true :=
  ⟨fun _ => 1, fun a => if a then 0 else v, rfl, by simp, by simpa⟩

/-- A positive apparent saving can correspond to a risk-contract violation. -/
theorem reliabilityCost : ∃ (cost risk : Bool → ℝ), cost true < cost false ∧
    ¬risk true ≤ risk false :=
  ⟨fun a => if a then 0 else 2, fun a => if a then 1 else 0, by norm_num, by norm_num⟩

/-- For two equiprobable losses the upper-half CVaR is their maximum. -/
theorem meanTail : ((0:ℝ)+80)/2 < (50+50)/2 ∧ max (50:ℝ) 50 < max 0 80 := by norm_num

theorem restriction : (∀ x ∈ ({1}:Set ℝ), (1:ℝ) ≤ x) ∧
    (0:ℝ) ∈ ({0,1}:Set ℝ) ∧ ¬(1:ℝ) ≤ 0 := by simp

theorem infeasibleIncumbent : (∀ x ∈ ({1}:Set ℝ), (1:ℝ) ≤ x) ∧
    (0:ℝ) ∉ ({1}:Set ℝ) ∧ (0:ℝ)-1 < 0 := by norm_num

theorem wrongMultiplier : (0:ℝ) ≤ 1 ∧ 0 ≤ (0:ℝ) ∧
    ¬(1:ℝ)*1 + min ((0-1)*0) ((0-1)*0) ≤ 0 := by norm_num

theorem omittedCase : ((0:ℝ) < 1) ∧ ¬(((0:ℝ)+4)/2 < 1) := by norm_num

theorem negativeWeight : (1:ℝ) ≤ 2 ∧ ¬((-1:ℝ)*1 ≤ (-1)*2) := by norm_num

/-- Separate scenarios have symmetric costs x and 1-x; both independently reach zero.
    A shared x has cost 1/2. Centered penalties collapse both augmented costs to 1/2. -/
theorem infoExample (x : ℝ) :
    ((x + (1-x))/2 = 1/2) ∧
    (((1/2-x) + (x-1/2))/2 = 0) ∧
    (x + (1/2-x) = 1/2) ∧ ((1-x)+(x-1/2) = 1/2) := by exact ⟨by ring, by ring, by ring, by ring⟩

theorem independentActions : ∃ x y : ℝ, 0 ≤ x ∧ x ≤ 1 ∧ 0 ≤ y ∧ y ≤ 1 ∧
    (x+(1-y))/2 = 0 ∧ x ≠ y := ⟨0,1,by norm_num,by norm_num,by norm_num,by norm_num,by norm_num,by norm_num⟩

theorem positivePenaltyFails : (1:ℝ) ≤ 0+1 ∧ ¬(1:ℝ) ≤ 0 := by norm_num

theorem unboundedRejection : Dual.floorTerm (.lower 0) (-1) = none ∧
    Dual.floorTerm (.upper 0) 1 = none ∧ Dual.floorTerm .free 1 = none ∧
    Dual.floorTerm .free 0 = some 0 := by norm_num [Dual.floorTerm]

theorem roundingFails : ∀ δ : ℝ, 0 < δ → ∃ x : ℝ, |x| ≤ δ ∧ x ≠ 0 := by
  intro δ h
  exact ⟨δ, by simp [abs_of_pos h], ne_of_gt h⟩

theorem incompatibleGains : ∀ (b : Bool),
    ¬ ((if b then (1:ℝ) else 0) = 1 ∧ (if b then (0:ℝ) else 1) = 1) := by
  intro b
  cases b <;> norm_num

end W06.Tests
