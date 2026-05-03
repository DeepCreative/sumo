# Bravo Zero Formal Verification Program

This repo is a fork of [`ontologyportal/sumo`](https://github.com/ontologyportal/sumo). On top of upstream SUMO, Bravo Zero adds a small body of domain-specific axioms (in `bravozero-extensions.kif`) and paired theorem-prover tests (in `tests/`) that formalize properties of BZ subsystems where getting the rule wrong has real cost.

This document describes the program: where the artifacts live, how a scenario is structured, how to add one, and how to verify the proofs locally.

## What's here

| Path | Purpose |
|---|---|
| `bravozero-extensions.kif` | All BZ-specific axioms, organized as named blocks with header comments |
| `tests/BZ-*.kif`, `tests/BZ-*.kif.tq` | Paired source-and-test files in the SigmaKEE convention |
| `tests/local-vampire/` | Self-contained TPTP reductions runnable directly with `vampire`, plus `run-all.sh` and saved `proofs/` |
| `tests/local-vampire/README.md` | Operational guide for the local Vampire harness |
| `.github/workflows/sumo-ci.yml` | Existing upstream-style CI that loads `bravozero-extensions.kif` as a SigmaKEE constituent and runs the KB consistency check on every push |
| `.github/workflows/tqsp-ci.yml` | Existing test-matrix workflow that runs Vampire against per-scenario `.kif.tq` files via SigmaKEE; manual trigger today |

## Current scenarios

| Block | System | Inference pattern |
|---|---|---|
| `MeshIdentity` | PERSONA | transitive closure over consented service hops |
| `RbacScope` | PERSONA | scoped negative result; reflexive scope axiom only |
| `AuditTenantIsolation` | Athena | time-windowed exception predicate |
| `AriaModelProvenance` | ARIA | status-governed admissibility with classical negation |
| `FilingQuorum` | GovRelations | variable-binding constraint with classical inequality |
| `FoundationAttestation` | Foundation | four-way conjunction of equally load-bearing predicates |
| `RulesOfEngagement` | JOSHUA | normative-attribute rules with temporal precondition (originally seeded the BZ extensions; acceptance test was added later under `tests/BZ-RulesOfEngagement-01.kif.tq`) |

Narrative pages for each scenario, with the proposition each one proves and the LLM blind spot each one catches, live in `cognitive-architecture-docs` under `systems/<owner>/ontology-example-*.md`.

## How a scenario is structured

Every scenario ships three artifacts.

### 1. Axiom block in `bravozero-extensions.kif`

Each block is delimited by a banner comment and follows a fixed structure:

```lisp
;; ========================================================================
;; <BlockName> - <One-line description>
;; ========================================================================
;;
;; Requesting system: <which BZ system needs this>
;; Discovery: PASSES - <why no existing SUMO term covers it>
;; Classification: <what kind of additions are being made>
;;
;; Step 0 inference (acceptance test):
;;   <plain-English statement of the conjecture and its negative control>
;;
;; Why this matters: <real-world stakes, including the LLM/intuition
;;                    failure mode this rule catches>

(subclass <NewClass> <SUMOParent>)
(documentation <NewClass> EnglishLanguage "...")

(instance <newPredicate> BinaryPredicate)
(domain <newPredicate> 1 <SomeClass>)
(domain <newPredicate> 2 <SomeClass>)
(documentation <newPredicate> EnglishLanguage "...")

;; ... more declarations ...

;; <Rule name>.
;; <Comment explaining what makes the rule load-bearing>
(=>
  (and ...)
  ...)
```

Reuse SUMO terms (`Organization`, `CognitiveAgent`, `Process`, `ContentBearingObject`, etc.) wherever possible. Only introduce new classes when no existing SUMO term fits, and document why in the Discovery line.

### 2. Paired `.kif` + `.kif.tq` test files

Two files per test, in `tests/`:

- `BZ-<Name>-NN.kif` is the editable scratch version with the `(query ...)` and `(answer ...)` lines commented out.
- `BZ-<Name>-NN.kif.tq` is the runnable test, identical content but with the query and answer uncommented.

Each scenario also has a negative-control test: `BZ-<Name>-NN-neg.kif.tq`, byte-for-byte identical to the positive test except for one critical fact (typically the load-bearing conjunct), with `(answer no)` instead of `(answer yes)`. The positive-and-negative pair is what makes the test a regression for the reasoning, not just a demo.

### 3. Self-contained TPTP reduction in `tests/local-vampire/`

Hand-translated TPTP version of the same axioms and conjecture, with `.p` extension. Lives alongside a saved proof artifact under `tests/local-vampire/proofs/`. Lets anyone verify the BZ axioms in isolation from the full SUMO KB, without SigmaKEE setup.

The harness script `tests/local-vampire/run-all.sh` runs every `.p` file and asserts each verdict matches expectations (positive cases must produce `Theorem`, files ending in `-neg.p` must produce `CounterSatisfiable`).

## Adding a new scenario

1. **Identify the property.** A formal scenario is worth writing when (a) the property matters operationally or for compliance, (b) the wrong intuition is common (LLMs and engineers both reproduce it), and (c) the property is expressible in first-order logic. If you cannot articulate a one-sentence acceptance test, it is not ready.

2. **Append a new block** to `bravozero-extensions.kif` matching the structure above. Reuse SUMO terms where possible; introduce new classes only when justified.

3. **Write the paired test files** in `tests/`. Always include a negative control. Verify both predicates and rules under the new block load cleanly into the existing SUMO KB by running:

   ```sh
   .github/workflows/sumo-ci.yml  # the consistency check runs automatically on push
   ```

4. **Hand-translate the conjecture to TPTP** under `tests/local-vampire/`. Save the proof output to `tests/local-vampire/proofs/`. Run `./run-all.sh` and confirm your new scenario appears in the pass list.

5. **Write a narrative page** in cognitive-architecture-docs under `systems/<owner>/ontology-example-<name>.md`. The existing pages (`ontology-example-mesh-identity.md`, etc.) are templates worth copying verbatim.

6. **Open the PR.** Update the existing scenarios PR if one is in flight, otherwise open a new one. PR description should include the `run-all.sh` output as evidence.

## Verifying locally

The fastest path:

```sh
brew install vampire             # one-time
cd tests/local-vampire && ./run-all.sh
```

Reports `N passed, 0 failed` in well under a second for the full set.

For verification against the full SUMO knowledge base, push to a branch. The existing `sumo-ci.yml` workflow loads `bravozero-extensions.kif` as a SigmaKEE constituent, translates the combined KB to TPTP, and runs Vampire. If your additions create any inconsistency with SUMO's ~5,000 axioms, that workflow fails.

## Why we do this

LLMs (and engineers reasoning informally) consistently get a class of authorization, provenance, and isolation properties wrong. The failures are predictable and the consequences are real, especially for regulated buyers. A formal proof says nothing more than the ground-truth rule itself, but it says it in a form that cannot be skimmed past, cannot drift silently, and can be re-verified by a third party in seconds.

For Bravo Zero, that capability is differentiated commercially in regulated-industry procurement, and worth the engineering hygiene cost of maintaining the axiom set.
