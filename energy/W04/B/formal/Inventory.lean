import Lean.Util.FoldConsts
import Controls
import StorageContract
import Sharpness

set_option pp.universes false

#check @W04.transport_threshold
#print axioms W04.transport_threshold
#check @W04.threshold_iff
#print axioms W04.threshold_iff
#check @W04.empty_threshold
#print axioms W04.empty_threshold
#check @W04.single_optimal_lift
#print axioms W04.single_optimal_lift
#check @W04.value_le_cost
#print axioms W04.value_le_cost
#check @W04.attained_value
#print axioms W04.attained_value
#check @W04.projected_value
#print axioms W04.projected_value
#check @W04.infimum_sandwich
#print axioms W04.infimum_sandwich
#check @W04.exact_infimum
#print axioms W04.exact_infimum
#check @W04.candidate_regret
#print axioms W04.candidate_regret
#check @W04.global_regret
#print axioms W04.global_regret
#check @W04.nested_stage
#print axioms W04.nested_stage
#check @W04.final_stage
#print axioms W04.final_stage
#check @W04.retained_cost
#print axioms W04.retained_cost
#check @W04.combined_lower
#print axioms W04.combined_lower
#check @W04.gap_contract
#print axioms W04.gap_contract
#check @W04.stop_with_tolerance
#print axioms W04.stop_with_tolerance
#check @W04.equal_values_bad_optimizer
#print axioms W04.equal_values_bad_optimizer
#check @W04.open_closed_infima
#print axioms W04.open_closed_infima
#check @W04.StorageContract.projection_bound
#print axioms W04.StorageContract.projection_bound
#check @W04.StorageContract.recovery_cost
#print axioms W04.StorageContract.recovery_cost
#check @W04.StorageContract.threshold_from_contract
#print axioms W04.StorageContract.threshold_from_contract
#check @W04.Controls.missing_lift
#print axioms W04.Controls.missing_lift
#check @W04.Controls.incompatible_labels
#print axioms W04.Controls.incompatible_labels
#check @W04.Controls.unbalanced_start
#print axioms W04.Controls.unbalanced_start
#check @W04.Controls.restricted_bound
#print axioms W04.Controls.restricted_bound
#check @W04.Controls.positive_terminal_tolerance
#print axioms W04.Controls.positive_terminal_tolerance
#check @W04.Controls.history_omission
#print axioms W04.Controls.history_omission
#check @W04.Controls.integrality_gap
#print axioms W04.Controls.integrality_gap
#check @W04.Controls.returned_cost_can_worsen
#print axioms W04.Controls.returned_cost_can_worsen
#check @W04.Sharpness.sharp
#print axioms W04.Sharpness.sharp

#check @W04.Controls.partial_lift_no_sandwich
#print axioms W04.Controls.partial_lift_no_sandwich

open Lean in
run_cmd do
  let env ← getEnv
  let localName (n : Name) := (`W03).isPrefixOf n || (`W04).isPrefixOf n
  let names := ((env.constants.toList.map Prod.fst).filter localName).mergeSort Name.quickLt
  for n in names do
    if let some c := env.find? n then
      let refs := (c.getUsedConstantsAsSet.toList.filter localName).mergeSort Name.quickLt
      logInfo m!"LOCAL-EDGES {n} {refs}"
