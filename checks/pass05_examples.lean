import NS1.Machine

/- Source-language checks for Proposition I.1. The companion enumeration in
   pass05_traces.py tests the pointer-machine side of the comparison. -/
namespace Pass05Examples

open NS1

def weights (name : List Bool) : ℤ := if name = [] then -1 else 0
def missingName : Fm := .theta (.quote (Tree.ofBits [false]))
def missingRun : Run ℤ := ⟨2, 0, [], .nil⟩

theorem missing_eval : Ev weights missingName .nil [missingRun] := by
  exact Ev.theta (Ev.quote _ _)

theorem canonical_missing_run :
    evl weights (Fm.ofTree missingName.code) .nil = [missingRun] := by
  rw [Fm.ofTree_code]
  exact missing_eval.evl

theorem supported_eval :
    Ev weights (.theta (.quote .nil)) .nil [⟨2, -1, [], .nil⟩] := by
  exact Ev.theta (Ev.quote _ _)

theorem duplicate_guess :
    Ev weights (.hd .guess) .nil [Run.det 2 .nil, Run.det 2 .nil] :=
  Ev.hd (Ev.guess _)

theorem empty_name_in_tally :
    Ev weights (.mul (.quote .nil)) .nil [⟨2, 1, [[]], .nil⟩] :=
  Ev.mul (Ev.quote _ _)

theorem noncanonical_opcode :
    Tree.cons Tree.one .nil ≠ Tree.num 1 ∧
    Fm.ofTree (.cons (.cons Tree.one .nil) .nil) = .id :=
  ⟨by decide, by rw [Fm.ofTree]; rfl⟩

#print axioms canonical_missing_run
#print axioms duplicate_guess

end Pass05Examples
