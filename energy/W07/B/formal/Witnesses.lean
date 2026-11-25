import Mathlib.Data.Fintype.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.NormNum

namespace W07.Control

/-- A decision forecast bit x at time 0 and bit z at time 1. Time 1 observes x.
The four integer masses 3,1,1,3 are divided by eight for economic interpretation. -/
def loss (x z a b : Bool) : Nat := (if a = x then 0 else 2) + (if b = z then 0 else 4)
def total (a b : Bool → Bool → Bool) : Nat :=
  3*loss false false (a false false) (b false false) +
    loss false true (a false true) (b false true) +
    loss true false (a true false) (b true false) +
  3*loss true true (a true true) (b true true)
def constant (v : Bool) : Bool → Bool → Bool := fun _ _ => v
def react (l h : Bool) : Bool → Bool → Bool := fun x _ => if x then h else l
def forecast (x _ : Bool) := x
def hindsight (_ z : Bool) := z

theorem perfect_witness : total forecast hindsight = 0 := by decide
theorem partial_root_floor : ∀ a b₀₀ b₀₁ b₁₀ b₁₁ : Bool, 8 ≤ total (constant a)
    (fun x z => if x then (if z then b₁₁ else b₁₀) else (if z then b₀₁ else b₀₀)) := by decide
theorem partial_root_attained : total (constant false) hindsight = 8 := by decide
theorem causal_floor : ∀ a l h : Bool, 16 ≤ total (constant a) (react l h) := by decide
theorem causal_attained : total (constant false) forecast = 16 := by decide
theorem false_merge_floor : ∀ a b : Bool, 24 ≤ total (constant a) (constant b) := by decide
theorem baseline_cost : total (constant false) (constant false) = 24 := by decide

theorem threshold_equality : (3:ℚ)-2 = 1 ∧ (1:ℚ) ≤ 3-2 := by norm_num
theorem weight_omission : (9:ℚ)/10*0 + (1:ℚ)/10*100 = 10 := by norm_num
theorem negative_mass : (0:ℚ) ≤ 1 ∧ (-1:ℚ)*1 < (-1:ℚ)*0 := by norm_num
theorem missing_baseline : (0:ℚ) ≤ 0 ∧ (12:ℚ)-0 > 1 := by norm_num
theorem act_order : (∀ c : Bool, ∃ u : Bool, u = c) ∧ ¬(∃ u : Bool, ∀ c : Bool, u = c) := by decide

end W07.Control
