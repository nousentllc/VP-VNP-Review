import Witnesses

open W07.Control

-- Negative build. Each statement has an explicit numerical or binary countermodel.
example : total forecast hindsight = total (constant false) forecast := by decide
example : total (constant false) (constant false) ≤ total (constant false) forecast := by decide
example : ¬ (1 : Nat) ≤ 3 - 2 := by decide
example : (9:Nat)*0 + 1*100 ≤ 0 := by decide
example : (-1:Int)*0 ≤ (-1:Int)*1 := by decide
example : (12:Nat)-0 ≤ 1 := by decide
example : ∃ u : Bool, ∀ c : Bool, u = c := by decide
-- Cost=0 on both paths, only the fitted action has zero expected penalty.
example : ∀ a : Bool, (if a then (2:Nat) else 0) ≤ 0 := by decide
-- Granting a larger budget an easier terminal requirement can reverse containment.
example : ∀ b : Bool, (if b then True else False) → False := by decide
