# Local Vampire verification

Minimal self-contained TPTP reductions of the BZ scenario tests in
`tests/`.  Each `.p` file captures the relevant axioms and conjecture
for one scenario without dragging in the full SUMO knowledge base, so
Vampire can be run locally in a second or two without SigmaKEE.

These files are NOT a replacement for the full-KB test pipeline run
by `.github/workflows/tqsp-ci.yml`.  Their purpose is fast, isolated
verification of the BZ-specific axiom logic during development and
review, plus a way for anyone reading the repo to confirm the
scenarios prove without installing Java, Ant, SigmaKEE, or Docker.

## Running

```sh
brew install vampire     # one-time, macOS
vampire BZ-MeshIdentity-01.p
```

Expected output for a positive case includes a line like:

```
% SZS status Theorem for BZ-MeshIdentity-01.p
```

For a negative-control case, expect:

```
% SZS status CounterSatisfiable for BZ-MeshIdentity-01-neg.p
```

Either of those, captured in this directory's `proofs/` output, is
sufficient evidence that the corresponding `.kif.tq` test should
also pass once wired into the SigmaKEE-based CI matrix.

## Files

| File | Mirrors | Expected verdict |
|---|---|---|
| `BZ-MeshIdentity-01.p` | `tests/BZ-MeshIdentity-01.kif.tq` | `Theorem` |
| `BZ-MeshIdentity-01-neg.p` | `tests/BZ-MeshIdentity-01-neg.kif.tq` | `CounterSatisfiable` |
| `BZ-RbacScope-01.p` | `tests/BZ-RbacScope-01.kif.tq` | `Theorem` |
| `BZ-RbacScope-01-neg.p` | `tests/BZ-RbacScope-01-neg.kif.tq` | `CounterSatisfiable` |
