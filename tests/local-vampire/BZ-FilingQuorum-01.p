%--------------------------------------------------------------------
% BZ-FilingQuorum-01 - positive case
%
% Self-contained TPTP reduction of tests/BZ-FilingQuorum-01.kif.tq.
% Proves that two distinct ComplianceOfficers, BOTH at the filing's
% organization, can together satisfy the filing's quorum requirement.
%
% Setup:
%   filing77 is for organization acme
%   jane is ComplianceOfficer at acme
%   bob is ComplianceOfficer at acme
%   both signed filing77
%   jane and bob are distinct individuals (must be asserted)
%
% Expected verdict: Theorem.
%--------------------------------------------------------------------

%----- quorum rule: a filing has quorum iff there exist TWO DISTINCT
%       signers, each holding ComplianceOfficer at the SAME organization
%       as the filing. The distinctness conjunct is essential; without
%       it, one signer could "count twice."
fof(rule_quorum, axiom,
    ! [F, O, P1, P2] :
      ( ( filingFor(F, O)
        & signedBy(F, P1)
        & signedBy(F, P2)
        & holdsRole(P1, complianceOfficer, O)
        & holdsRole(P2, complianceOfficer, O)
        & P1 != P2 )
      => quorumSatisfied(F) ) ).

%----- ground facts
fof(fact_filing,        axiom, filingFor(filing77, acme)).
fof(fact_signed_jane,   axiom, signedBy(filing77, jane)).
fof(fact_signed_bob,    axiom, signedBy(filing77, bob)).
fof(fact_jane_role,     axiom, holdsRole(jane, complianceOfficer, acme)).
fof(fact_bob_role,      axiom, holdsRole(bob,  complianceOfficer, acme)).

%----- distinctness assertion: jane and bob are different individuals.
%       Without this, the prover cannot rule out the possibility that
%       jane and bob refer to the same person, and the quorum rule's
%       distinctness conjunct fails.
fof(fact_distinct,      axiom, jane != bob).

%----- conjecture: filing77 has quorum
fof(conjecture_quorum, conjecture,
    quorumSatisfied(filing77)).
