import Information
import Viability
import Witnesses

#check @W07.Info.strengthen
#print axioms W07.Info.strengthen
#check @W07.Info.projection
#print axioms W07.Info.projection
#check @W07.Info.lower_transfer
#print axioms W07.Info.lower_transfer
#check @W07.Info.restrict_value
#print axioms W07.Info.restrict_value
#check @W07.Info.nested_information
#print axioms W07.Info.nested_information
#check @W07.Info.max_floor
#print axioms W07.Info.max_floor
#check @W07.Info.strict_stop
#print axioms W07.Info.strict_stop
#check @W07.Info.equality_stop_nonattained
#print axioms W07.Info.equality_stop_nonattained
#check @W07.Info.covered_weight
#print axioms W07.Info.covered_weight
#check @W07.Info.penalty_transfer
#print axioms W07.Info.penalty_transfer
#check @W07.Info.history_centering
#print axioms W07.Info.history_centering
#check @W07.Info.accumulated_centering
#print axioms W07.Info.accumulated_centering
#check @W07.Info.penalty_debit
#print axioms W07.Info.penalty_debit
#check @W07.Info.history_upper
#print axioms W07.Info.history_upper
#check @W07.Game.strategy_to_kernel
#print axioms W07.Game.strategy_to_kernel
#check @W07.Game.kernel_to_strategy
#print axioms W07.Game.kernel_to_strategy
#check @W07.Game.causal_equivalence
#print axioms W07.Game.causal_equivalence
#check @W07.Game.budget_shrink
#print axioms W07.Game.budget_shrink
#check @W07.Game.decrement_order
#print axioms W07.Game.decrement_order
#check @W07.Control.perfect_witness
#print axioms W07.Control.perfect_witness
#check @W07.Control.partial_root_floor
#print axioms W07.Control.partial_root_floor
#check @W07.Control.partial_root_attained
#print axioms W07.Control.partial_root_attained
#check @W07.Control.causal_floor
#print axioms W07.Control.causal_floor
#check @W07.Control.causal_attained
#print axioms W07.Control.causal_attained
#check @W07.Control.false_merge_floor
#print axioms W07.Control.false_merge_floor
#check @W07.Control.baseline_cost
#print axioms W07.Control.baseline_cost
#check @W07.Control.threshold_equality
#print axioms W07.Control.threshold_equality
#check @W07.Control.weight_omission
#print axioms W07.Control.weight_omission
#check @W07.Control.negative_mass
#print axioms W07.Control.negative_mass
#check @W07.Control.missing_baseline
#print axioms W07.Control.missing_baseline
#check @W07.Control.act_order
#print axioms W07.Control.act_order

open Lean in
run_cmd do
  let env ← getEnv
  let own (n : Name) := (`W07).isPrefixOf n
  let names := ((env.constants.toList.map Prod.fst).filter own).mergeSort Name.quickLt
  for n in names do
    if let some c := env.find? n then
      let refs := (c.getUsedConstantsAsSet.toList.filter own).mergeSort Name.quickLt
      logInfo m!"LOCAL-EDGES {n} {refs}"
