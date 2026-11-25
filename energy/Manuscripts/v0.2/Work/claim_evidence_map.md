# CRGC v0.2 claim-evidence map

Confidential. “Measured” refers to local model experiments unless otherwise stated.

## C01 — CRGC is a baseline-relative contract-specific outcome

- Status: definition / definition_only
- Evidence: Author proposal; sec:definition
- Limit: Not an established named resource or new complexity class
- Artifact: See source inventory

## C02 — Anthropic states all-field HC and non-characteristic-two permanent lower bounds

- Status: reported_theorem / qualified
- Evidence: anthropic;anthropicstatement;internalvp; Theorems 1.1/1.4; Statement MainTheorem
- Limit: Full proof not replayed; independent review incomplete
- Artifact: See source inventory

## C03 — VP/VNP separation yields an AC-OPF or SCUC solver

- Status: unsupported / excluded
- Evidence: anthropic;openai; No transfer reduction in reviewed artifacts
- Limit: Different computational models; no measured transfer
- Artifact: E01/E02 proposals

## C04 — Ten percent of Napkin pools is recoverable

- Status: scenario / excluded_from_findings
- Evidence: napkin; Pool calculations
- Limit: No validated causal fraction or nonoverlap
- Artifact: See source inventory

## C05 — Napkin arithmetic yields MISO 8.26 and US 46.87 TWh

- Status: derived / arithmetic_only
- Evidence: napkin;arithmetic_checks.json; 0.1 times 82.6/468.7
- Limit: Inputs remain unvalidated scenario pools
- Artifact: arithmetic_checks.json

## C06 — 46.87 TWh implies firm capacity

- Status: unsupported / firm_claim_excluded
- Evidence: arithmetic_checks.json;elcc; 46.87/8.76 = annual average GW
- Limit: Requires risk equivalence and deliverability
- Artifact: E06 unrun

## C07 — MISO ratings opportunity equals realized solver savings

- Status: unsupported_attribution / excluded
- Evidence: miso; Printed p.68 / PDF p.94 Table11 footnote24
- Limit: Estimated ratings benefit; not solver intervention; shadow-price approximation
- Artifact: See source inventory

## C08 — Solver gap equals realized savings

- Status: unsupported / excluded
- Evidence: Author weak-duality derivation; Eq. gap
- Limit: Bound on same-model improvement; tightening lower bound may change no action
- Artifact: E01

## C09 — Multistart materially improves case3_lmbd

- Status: measured_null / not_observed
- Evidence: pglib;E01; Ten starts results.json
- Limit: One tiny nonsecurity case; unequal total compute
- Artifact: reproducibility/results.json

## C10 — LP beats forecast-aware threshold on synthetic BESS service

- Status: measured_null / not_observed
- Evidence: E05; All four profiles
- Limit: Constructed deterministic profiles; post-hoc ablation
- Artifact: reproducibility/results.json

## C11 — More service necessarily reduces losses

- Status: measured_counterexample / universal_claim_refuted_by_model
- Evidence: E05; Four-hour and alternating profiles
- Limit: Model result; higher throughput increases losses
- Artifact: reproducibility/bess_schedules.csv

## C12 — Exact toy LP witness accepted and four mutations rejected

- Status: measured / limited_demonstration
- Evidence: E04; Fraction checker
- Limit: Checker not formally verified; four controls not exhaustive
- Artifact: reproducibility/results.json

## C13 — Entire Library and Atlas were reviewed

- Status: coverage_claim / not_established
- Evidence: source_inventory_local.csv;search_audit.json; 1451-file bounded inventory;293-PDF screen
- Limit: Native Library and authoritative Atlas not verified
- Artifact: See source inventory

## C14 — Selected internal VP-review diagnostics reproduce

- Status: measured / finite_checks_only
- Evidence: internalvp;VP-checks; Three copied Python scripts
- Limit: Not full Lean replay or proof; internal source lineage
- Artifact: reproducibility/vp_review/

## C15 — Commercial savings or accredited MW are established

- Status: projection / not_established
- Evidence: No field or portfolio study; E06 protocol
- Limit: No operational population, costs or accreditation study
- Artifact: E06 unrun

## C16 — External VP audit reports 18/23 rows and CERTIFIED

- Status: reported_audit / attributed
- Evidence: toledo; Snapshot 2026-11-24 03:15 UTC
- Limit: Own verdict rule; AI-assisted; no human proof review; not rerun
- Artifact: See source inventory

## C17 — OpenAI separate release claims border separation

- Status: reported_theorem / qualified
- Evidence: openai; Theorem1.1;Corollary1.2;README
- Limit: Exact Lean link not proof all border claims replayed
- Artifact: See source inventory

## C18 — GO one-percent/billion-dollar figure is realized savings

- Status: unsupported_attribution / excluded
- Evidence: go; PNNL report pp.4-5
- Limit: Program motivational estimate, not measured outcome
- Artifact: See source inventory

## C19 — LBNL 649 TWh is 2030 realized demand

- Status: projection / projection_only
- Evidence: lbnl; Official 2025 Update published2026 abstract
- Limit: Forecast, uncertain; not recoverable energy
- Artifact: See source inventory

## C20 — 4/8-hour synthetic peaks require at least8/168MWh unserved

- Status: derived_and_measured / model_specific_bound_attained
- Evidence: E05; Deficit minus0.95*(200-40)
- Limit: Fixed energy/import model, no peak charging opportunity
- Artifact: reproducibility/results.json

## C21 — Exact AC solution globally optimal

- Status: unsupported / not_claimed
- Evidence: E01; SLSQP agreement and case comment
- Limit: Neither multistart nor comment is a proof; valid bound retained
- Artifact: See source inventory

## C22 — Internal hallucination-entropy link supports grid recovery

- Status: internal_hypothesis / excluded
- Evidence: internalcompute; Abstract thermodynamic coupling
- Limit: Independent causal evidence not established
- Artifact: See source inventory

## C23 — Formal checking guarantees physical safety

- Status: unsupported_generalization / excluded
- Evidence: leanpep;internalvp;Author analysis; Trust chain and model scope
- Limit: Input semantics, environment and omitted physics remain
- Artifact: See source inventory

## C24 — PGLib UC is full network SCUC

- Status: scope_error / excluded
- Evidence: pglibuc; README formulation
- Limit: Global demand/reserve model is not full contingency network model
- Artifact: See source inventory

## C25 — Published VP lower-bound constant establishes a practical threshold

- Status: derived_conditional / conditional
- Evidence: toledo;arithmetic_checks.json; c=1/1600^2 exponent>2 calculation
- Limit: No explicit m0; algebraic comparison not onset theorem
- Artifact: arithmetic_checks.json
