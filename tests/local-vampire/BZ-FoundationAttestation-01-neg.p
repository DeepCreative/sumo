%--------------------------------------------------------------------
% BZ-FoundationAttestation-01-neg - negative control
%
% Self-contained TPTP reduction of tests/BZ-FoundationAttestation-01-neg.kif.tq.
% Same event, written to the DB and attested on chain with a valid
% signature, BUT the attestation appeared OUTSIDE the configured time
% window. The naive intuition ("the chain has it, that's attested")
% is what most LLMs reproduce. The formalism does not agree: the
% attestation rule requires withinAttestationWindow as a conjunct.
%
% This catches a real dual-write failure mode: when chain attestation
% lags far behind the database write, treating the event as attested
% conflates "eventually written" with "verifiably written within the
% trust window." Regulatory frameworks that depend on attestation
% latency bounds (financial reporting, audit logs with retention
% guarantees) need this distinction enforced, not assumed.
%
% Expected verdict: CounterSatisfiable.
%--------------------------------------------------------------------

%----- attestation rule (identical to positive case)
fof(rule_attestation, axiom,
    ! [E] :
      ( ( eventWritten(E)
        & eventAttestedOnChain(E)
        & withinAttestationWindow(E)
        & chainSignatureValid(E) )
      => attested(E) ) ).

%----- ground facts: written, on chain, signature valid, but NOT in window
fof(fact_written,    axiom, eventWritten(event42)).
fof(fact_on_chain,   axiom, eventAttestedOnChain(event42)).
fof(fact_sig_valid,  axiom, chainSignatureValid(event42)).
% fof(fact_in_window, axiom, withinAttestationWindow(event42)).
%                          ^^^ INTENTIONALLY OMITTED

%----- conjecture: should NOT be provable
fof(conjecture_attested, conjecture,
    attested(event42)).
