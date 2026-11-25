import Obstructions

#check @W05.need_le_iff
#print axioms W05.need_le_iff
#check @W05.rowNeed_iff
#print axioms W05.rowNeed_iff
#check @W05.need_unit
#print axioms W05.need_unit
#check @W05.minimal_fraction
#print axioms W05.minimal_fraction
#check @W05.empty_rows
#print axioms W05.empty_rows
#check @W05.boundary_fallback
#print axioms W05.boundary_fallback
#check @W05.envelope
#print axioms W05.envelope
#check @W05.uniform_fraction
#print axioms W05.uniform_fraction
#check @W05.affine_mix
#print axioms W05.affine_mix
#check @W05.objective_identity
#print axioms W05.objective_identity
#check @W05.feasible_anchor
#print axioms W05.feasible_anchor
#check @W05.equality_obstruction
#print axioms W05.equality_obstruction
#check @W05.lipschitz_loss
#print axioms W05.lipschitz_loss
#check @W05.uniform_loss
#print axioms W05.uniform_loss
#check @W05.equality_repair
#print axioms W05.equality_repair
#check @W05.right_inverse_repair
#print axioms W05.right_inverse_repair
#check @W05.corner_bound
#print axioms W05.corner_bound
#check @W05.affine_box_support
#print axioms W05.affine_box_support
#check @W05.projection_support
#print axioms W05.projection_support
#check @W05.outer_embedding
#print axioms W05.outer_embedding
#check @W05.cost_mismatch
#print axioms W05.cost_mismatch
#check @W05.aipc_from_repair
#print axioms W05.aipc_from_repair
#check @W05.uniform_affine_beta
#print axioms W05.uniform_affine_beta
#check @W05.Terminal.row_headroom
#print axioms W05.Terminal.row_headroom
#check @W05.Terminal.single_slot_iff
#print axioms W05.Terminal.single_slot_iff
#check @W05.Terminal.signed_slot_iff
#print axioms W05.Terminal.signed_slot_iff
#check @W05.Terminal.suffix_shift
#print axioms W05.Terminal.suffix_shift
#check @W05.Terminal.adjacent_ramps
#print axioms W05.Terminal.adjacent_ramps
#check @W05.Terminal.soc_increment
#print axioms W05.Terminal.soc_increment
#check @W05.Terminal.charge_cost
#print axioms W05.Terminal.charge_cost
#check @W05.Terminal.no_single_slot_can_be_insufficient
#print axioms W05.Terminal.no_single_slot_can_be_insufficient
#check @W05.Obstructions.unverified_anchor
#print axioms W05.Obstructions.unverified_anchor
#check @W05.Obstructions.integral_midpoint
#print axioms W05.Obstructions.integral_midpoint
#check @W05.Obstructions.nonconvex_voltage
#print axioms W05.Obstructions.nonconvex_voltage
#check @W05.Obstructions.equality_after_mixing
#print axioms W05.Obstructions.equality_after_mixing
#check @W05.Obstructions.inverse_can_break_bounds
#print axioms W05.Obstructions.inverse_can_break_bounds
#check @W05.Obstructions.box_gap_over_true_gap
#print axioms W05.Obstructions.box_gap_over_true_gap
#check @W05.Obstructions.bound_scope
#print axioms W05.Obstructions.bound_scope
#check @W05.Obstructions.arbitrarily_small_violation
#print axioms W05.Obstructions.arbitrarily_small_violation
#check @W05.Obstructions.mixture_of_anchors
#print axioms W05.Obstructions.mixture_of_anchors

open Lean in
run_cmd do
  let env ← getEnv
  let localName (n : Name) := (`W05).isPrefixOf n || (`W04).isPrefixOf n
  let names := ((env.constants.toList.map Prod.fst).filter localName).mergeSort Name.quickLt
  for n in names do
    if let some c := env.find? n then
      let refs := (c.getUsedConstantsAsSet.toList.filter localName).mergeSort Name.quickLt
      logInfo m!"LOCAL-EDGES {n} {refs}"
