# Static AC-OPF and conventional unit commitment

Read freeze.json for the 1% target and source_lock.json for input revisions, Git blob IDs, SHA-256 digests and source links. All selections were fixed before opening the new data. The six AC snapshots comprise three networks with a base and an active-power-increase variant. The four UC horizons use two different dates and their original initial histories. Outputs use original benchmark objective units. Treat time on the shared host as descriptive. Sector-level dollars, contingencies, AC security-constrained UC and actual dispatch outcomes are outside these model contracts.

## Evidence and replay

Use Python 3.12 with the root requirements. Run the following in this directory with new external output paths. Set OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1 and PYTHONDONTWRITEBYTECODE=1. The first two commands re-solve primary models with the dispatch/commitment engines. The audit commands re-evaluate the stored certificates.

    python ac.py run /tmp/w06-ac-new
    python commitment.py run /tmp/w06-uc-new
    python ac.py audit ac_results
    python commitment.py audit uc_results
    python independent.py ac_results uc_results /tmp/w06-c-physics.json
    python clique.py audit ac_results exploratory/results
    python uc_tree.py audit uc_results exploratory/uc_results

Replace audit with run and supply a fresh third argument directory to regenerate either follow-up. The 31-node commitment follow-up consumes an external directory of the primary records; if new solver clocks change the incumbent, the eligible case set can change. Independent input parsing, original Pyomo expressions and lifted-cut algebra checks have separate entrypoints in independent_review/README.md.

## Qualification of bounds

network.py uses full polar constraints and two IPOPT starts. Inside original bounds we reserve small margins to permit an existence certificate. ac_witness.py switches to rectangular coordinates, fixes the reference phase, and selects a square, nonsingular Jacobian column subset. At 160-bit precision, Arb encloses the tip-to-tip tap, shunt and line admittances derived from the input decimals. A preconditioned residual and interval-Jacobian norm map the chosen radius ball into itself and imply an exact solution. Interval checks cover balance through the zero existence proof, both-end current-derived thermal flows, ordered bus phase differences, voltage, the unsquared generator bounds and the cost envelope. Fixed generator outputs are retained as exact inputs. The upper endpoint bounds the cost of the certified local witness, irrespective of global optimality.

ac_bound.py first prices total demand using nonnegative line losses and bus conductances. Each second-tier cut is valid for every physical network voltage. Lifted flow identities with tap angles use rounded coefficients plus an outward error allowance over the whole variable box. Exact rational cuts bound convex quadratic epigraphs, thermal disks and 2-by-2 voltage submatrices. Upper and lower row multipliers suggested by HiGHS are priced with exact residual endpoint charges in linear.py. A cut remains valid even when discovered using a local solve. The exploratory clique follow-up adds outward angle wedges plus quadratic forms from rational Hermitian test vectors. Dual objectives only can establish a floor, and test-vector separation samples part of the full positive-semidefinite cone.

commitment.py uses the pinned upstream Pyomo reference constraints with literal JSON decimals. Bounds on production, reserve and nonbaseline fuel cost follow from the reference convex weights, nameplate and reserve equations. The continuous model drops integrality; neither maintenance nor grouping constraints are added. The primary stronger certificate covers both branches of a selected binary. The post hoc search uses all leaves of a disjunctive tree. HiGHS solves unrestricted MILPs and LPs. With the incumbent commitments, Z3 searches for a rational schedule, subject to its cost within a cent (and four decimal places of rounding) of the numerical candidate. Every exact variable bound, source constraint, integer and cost is tested. HiGHS native tree gaps carry its numerical tolerances. Physical replay also rechecks initial state, MW, startup class, ramp, reserve and period cost. No monetary integration-cost or unit accreditation model is assumed.

## Preserved failures

diagnostics/uc_first_attempt stores the initial rational transport failure: combining many different multiplier denominators exceeded Python's integer-to-string limit. The final validator uses a common 1e-9 decimal grid for suggestions. diagnostics/uc_float_rhs contains the run where the Pyomo lower/upper property coerced exact decimal right-hand sides to binary64. diagnostics/uc_index_order contains the subsequent run in which independent-process column ordering prevented vector replay. Only uc_results uses exact row endpoints, canonical sorted row/column keys and checks those keys on read-back. The old folders contain diagnostic records rather than primary certificates for the final model. No holdout was replaced. Re-runs can change deadline-limited incumbents.

Source attribution: IEEE PES PGLib-OPF and PGLib-UC, including the libraries' shipped data/model licences in inputs. The SOC and copperplate precedents are Coffrin, Hijazi and Van Hentenryck (arXiv:1502.07847 and 1506.05202). The official UC formulation follows Morales-España, Latorre and Ramos with piecewise production costs. Robust checking of numerical root and dual suggestions is established in the interval-arithmetic and safe LP-bound literature. See the technical report and B/LITERATURE.md.
