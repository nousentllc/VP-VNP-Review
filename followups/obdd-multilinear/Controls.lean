import SharedOBDD

namespace SharedOBDD.Controls

/-- The root and its high child both use the same x₂ vertex. -/
def diamond : List (Node 3) :=
  [⟨0, .slot 1, .slot 0⟩, ⟨1, .slot 0, .one⟩, ⟨2, .zero, .one⟩]

theorem diamond_ordered : Ordered diamond := by
  norm_num [diamond, Ordered, level, nodeStore, push, Ref.read, Ref.Valid]
example : (compile diamond).length = 9 := by decide
example : Wired (compile diamond) := compile_wired diamond_ordered

private def branch (a b c : Bool) : Fin 3 → Bool := ![a,b,c]

example (a b c : Bool) :
    decision diamond (.slot 0) (branch a b c) = (c || (a && b)) := by
  cases a <;> cases b <;> cases c <;> rfl

/-- With input (2,3,5), the formal multilinear polynomial is 5 + 2*3*(1-5). -/
example : gateStore (![2,3,5] : Fin 3 → Int) (compile diamond) 0 = -19 := by decide

example : (compile ([] : List (Node 0))).length = 0 := rfl
example : (wire (n := 0) 0 .one).Valid 0 := trivial
example : ¬ Ref.Valid 0 (.slot 0) := by simp [Ref.Valid]

/-- Repeating the same test computes x² as a formal polynomial while agreeing with x on bits. -/
def repeated : List (Node 1) := [⟨0, .zero, .slot 0⟩, ⟨0, .zero, .one⟩]
example : ¬ Ordered repeated := by
  norm_num [repeated, Ordered, level, nodeStore, push, Ref.read, Ref.Valid]
example (b : Bool) : decision repeated (.slot 0) (fun _ => b) = b := by cases b <;> rfl
example : gateStore (fun _ : Fin 1 => (2 : Int)) (compile repeated) 0 = 4 := by decide

end SharedOBDD.Controls
#print axioms SharedOBDD.compiler_spec
