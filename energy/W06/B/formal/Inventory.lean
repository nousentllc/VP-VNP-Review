import Tests
import Closing

#check @W06.pointCeiling
#print axioms W06.pointCeiling
#check @W06.strictStop
#print axioms W06.strictStop
#check @W06.weakStop
#print axioms W06.weakStop
#check @W06.minInterval
#print axioms W06.minInterval
#check @W06.maxInterval
#print axioms W06.maxInterval
#check @W06.maxStops
#print axioms W06.maxStops
#check @W06.feasibleGain
#print axioms W06.feasibleGain
#check @W06.transferBound
#print axioms W06.transferBound
#check @W06.nestedInf
#print axioms W06.nestedInf
#check @W06.totalMono
#print axioms W06.totalMono
#check @W06.weightedPanel
#print axioms W06.weightedPanel
#check @W06.partialPanel
#print axioms W06.partialPanel
#check @W06.centeredPenalty
#print axioms W06.centeredPenalty
#check @W06.riskCeiling
#print axioms W06.riskCeiling
#check @W06.netBound
#print axioms W06.netBound
#check @W06.netStop
#print axioms W06.netStop
#check @W06.discountedNet
#print axioms W06.discountedNet
#check @W06.ignoreInformation
#print axioms W06.ignoreInformation
#check @W06.operationalChain
#print axioms W06.operationalChain
#check @W06.contractCost
#print axioms W06.contractCost
#check @W06.strictAtNonattainment
#print axioms W06.strictAtNonattainment
#check @W06.enclosureCeiling
#print axioms W06.enclosureCeiling
#check @W06.infoPanelInf
#print axioms W06.infoPanelInf
#check @W06.Dual.finiteEndpoint
#print axioms W06.Dual.finiteEndpoint
#check @W06.Dual.floorTermSound
#print axioms W06.Dual.floorTermSound
#check @W06.Dual.transposePair
#print axioms W06.Dual.transposePair
#check @W06.Dual.mixedRowDual
#print axioms W06.Dual.mixedRowDual
#check @W06.Dual.boxedDual
#print axioms W06.Dual.boxedDual
#check @W06.Tests.equalityTarget
#print axioms W06.Tests.equalityTarget
#check @W06.Tests.nonattainment
#print axioms W06.Tests.nonattainment
#check @W06.Tests.slackBound
#print axioms W06.Tests.slackBound
#check @W06.Tests.serviceEconomics
#print axioms W06.Tests.serviceEconomics
#check @W06.Tests.reliabilityCost
#print axioms W06.Tests.reliabilityCost
#check @W06.Tests.meanTail
#print axioms W06.Tests.meanTail
#check @W06.Tests.restriction
#print axioms W06.Tests.restriction
#check @W06.Tests.infeasibleIncumbent
#print axioms W06.Tests.infeasibleIncumbent
#check @W06.Tests.wrongMultiplier
#print axioms W06.Tests.wrongMultiplier
#check @W06.Tests.omittedCase
#print axioms W06.Tests.omittedCase
#check @W06.Tests.negativeWeight
#print axioms W06.Tests.negativeWeight
#check @W06.Tests.infoExample
#print axioms W06.Tests.infoExample
#check @W06.Tests.independentActions
#print axioms W06.Tests.independentActions
#check @W06.Tests.positivePenaltyFails
#print axioms W06.Tests.positivePenaltyFails
#check @W06.Tests.unboundedRejection
#print axioms W06.Tests.unboundedRejection
#check @W06.Tests.roundingFails
#print axioms W06.Tests.roundingFails
#check @W06.Tests.incompatibleGains
#print axioms W06.Tests.incompatibleGains

#check @W06.Closing.telescope
#print axioms W06.Closing.telescope
#check @W06.Closing.creditDifference
#print axioms W06.Closing.creditDifference
#check @W06.Closing.terminalPremium
#print axioms W06.Closing.terminalPremium
#check @W06.Closing.noCapacityOnlyMoneyBound
#print axioms W06.Closing.noCapacityOnlyMoneyBound

open Lean in
run_cmd do
  let env ← getEnv
  let own (n : Name) := (`W06).isPrefixOf n
  let names := ((env.constants.toList.map Prod.fst).filter own).mergeSort Name.quickLt
  for n in names do
    if let some c := env.find? n then
      let refs := (c.getUsedConstantsAsSet.toList.filter own).mergeSort Name.quickLt
      logInfo m!"LOCAL-EDGES {n} {refs}"
