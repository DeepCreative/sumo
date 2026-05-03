%--------------------------------------------------------------------
% BZ-FoundationAttestation-01 - positive case
%
% Self-contained TPTP reduction of tests/BZ-FoundationAttestation-01.kif.tq.
% Proves that an event with a complete dual-write chain (database write
% PLUS in-window blockchain attestation PLUS valid chaincode signature)
% is considered attested.
%
% Setup:
%   event42 was written to the database
%   event42 was attested on the blockchain
%   the attestation appeared within the required window of the DB write
%   the chaincode receipt signature is valid
%
% Expected verdict: Theorem.
%--------------------------------------------------------------------

%----- attestation rule: an event is attested iff it has been written
%       AND chain-attested AND the attestation is within the configured
%       window AND the chaincode signature is valid. ALL FOUR are
%       load-bearing; drop any one and attestation is not derivable.
fof(rule_attestation, axiom,
    ! [E] :
      ( ( eventWritten(E)
        & eventAttestedOnChain(E)
        & withinAttestationWindow(E)
        & chainSignatureValid(E) )
      => attested(E) ) ).

%----- ground facts (all four conjuncts present)
fof(fact_written,    axiom, eventWritten(event42)).
fof(fact_on_chain,   axiom, eventAttestedOnChain(event42)).
fof(fact_in_window,  axiom, withinAttestationWindow(event42)).
fof(fact_sig_valid,  axiom, chainSignatureValid(event42)).

%----- conjecture: event42 is attested
fof(conjecture_attested, conjecture,
    attested(event42)).
