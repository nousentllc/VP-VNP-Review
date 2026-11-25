import Information

namespace W07.Extra

/-- The candidate may be a certified floor of a relaxed program, or its true real
infimum if its penalized costs have a lower bound on the relaxed class. -/
theorem penalized_infimum {P Q : Type*} (C : Set P) (R : Set Q) (f : P → Q)
    (J : P → ℝ) (F M : Q → ℝ) (η : ℝ) (nonempty : C.Nonempty)
    (proj : ∀ p ∈ C, f p ∈ R) (cost : ∀ p ∈ C, F (f p) ≤ J p)
    (residual : ∀ p ∈ C, M (f p) ≤ η)
    (finiteFloor : BddBelow ((fun z => F z + M z) '' R)) :
    W07.Info.value (fun z => F z + M z) R - η ≤ W07.Info.value J C := by
  apply W07.Info.lower_transfer J nonempty
  apply W07.Info.penalty_debit C R f J F M _ _ proj cost residual
  intro z hz
  exact csInf_le finiteFloor ⟨z,hz,rfl⟩

theorem unbounded_image :
    (fun z : ℝ => (-1 : ℝ) + z) '' Set.Iic 0 = Set.Iic (-1 : ℝ) := by
  ext y
  constructor
  · rintro ⟨z,hz,rfl⟩
    change z ≤ 0 at hz
    change -1 + z ≤ -1
    linarith
  · intro h
    change y ≤ -1 at h
    refine ⟨y+1,?_,by linarith⟩
    change y+1 ≤ 0
    linarith

theorem no_finite_lower_bound : ¬ BddBelow (Set.Iic (-1 : ℝ)) := by
  rintro ⟨b,hb⟩
  have hh : min b (-1 : ℝ)-1 ∈ Set.Iic (-1 : ℝ) := by
    change min b (-1 : ℝ)-1 ≤ -1
    linarith [min_le_right b (-1 : ℝ)]
  have v := hb hh
  linarith [min_le_left b (-1 : ℝ)]

theorem real_infimum_trap :
    ¬ W07.Info.value (fun z : ℝ => (-1 : ℝ) + z) (Set.Iic 0) ≤ (-1 : ℝ) := by
  unfold W07.Info.value
  rw [unbounded_image, Real.sInf_of_not_bddBelow no_finite_lower_bound]
  norm_num

end W07.Extra

#print axioms W07.Extra.penalized_infimum
#print axioms W07.Extra.unbounded_image
#print axioms W07.Extra.no_finite_lower_bound
#print axioms W07.Extra.real_infimum_trap

open Lean in
run_cmd do
  let env ← getEnv
  for n in [`W07.Extra.penalized_infimum, `W07.Extra.unbounded_image, `W07.Extra.no_finite_lower_bound, `W07.Extra.real_infimum_trap] do
    if let some c := env.find? n then
      let refs := (c.getUsedConstantsAsSet.toList.filter (fun d => (`W07).isPrefixOf d)).mergeSort Name.quickLt
      logInfo m!"LOCAL-EDGES {n} {refs}"
