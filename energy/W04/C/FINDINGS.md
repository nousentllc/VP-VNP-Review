# W04-C results

Full DC, full with reconstructed generator start, all-pivot elimination, and selective elimination produced 36, 37, 37, and 37 validated on-time solutions out of 40 runs each. All 160 terminal vectors passed an independently implemented sparse-admittance audit. The 147 on-time feasible costs agree with the separately published PowerModels.jl AC references to the precision printed by PGLib. All 36 original W03 replay costs agreed exactly.

| Case | Full DC / matched / all / selective hits out of 5 | Full DC cost per hour | Ratio of all-pivot to matched time | Matched repeats |
| --- | --- | ---: | ---: | ---: |
| pglib_opf_case57_ieee | 5 / 5 / 5 / 5 | 37,589.34 | 0.979 | 5 |
| pglib_opf_case57_ieee__api | 5 / 5 / 5 / 5 | 36,242.46 | 0.999 | 5 |
| pglib_opf_case118_ieee | 4 / 4 / 3 / 4 | 97,213.61 | 1.201 | 2 |
| pglib_opf_case118_ieee__api | 5 / 5 / 5 / 5 | 249,614.52 | 1.110 | 5 |
| pglib_opf_case300_ieee | 5 / 5 / 5 / 5 | 565,219.99 | 0.941 | 5 |
| pglib_opf_case300_ieee__api | 5 / 5 / 5 / 5 | 686,040.71 | 0.996 | 5 |
| pglib_opf_case1354_pegase | 2 / 3 / 4 / 3 | 1,258,844.01 | 1.096 | 3 |
| pglib_opf_case1354_pegase__api | 5 / 5 / 5 / 5 | 1,608,226.89 | 1.013 | 5 |

Neither elimination policy reached the practical 10% median improvement on any case against either full comparator at equal feasible objective within 1e-5 relative. Missing matched repeats are censored. Shared-machine load varied considerably over the run. The 1,354-bus typical case achieved four all-pivot hits and two full DC hits, though its matched-pair timing ratio against full DC was 1.201 on only two comparisons. No general speed attribution follows.

RCM structural fill grew from 99,221 to 107,615 in the largest typical case despite removing 520 variables. For the 300-bus typical case the same metric fell from 16,018 to 14,320. The estimated condition and SuperLU factor time refer to a separately regularized KKT system. The original IPOPT factor time is unavailable. Independent direct dense elimination on 25 small graphs checked the symbolic counter.

The per-case detailed tables retain both local objective and numerical lower floor, dimensions, Jacobian/Hessian nonzeros, peak RSS, iterations, construction, independent validation, factor time and estimated conditioning. The raw initialization diagnostic for reduced arms must be read with the independently reconstructed values in review_verification.json. See review_notes.md for the additional angle-box and linear-cost scope.
