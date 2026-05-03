%--------------------------------------------------------------------
% BZ-FilingQuorum-01-neg - negative control
%
% Self-contained TPTP reduction of tests/BZ-FilingQuorum-01-neg.kif.tq.
% Same filing, same two signers, BUT bob's ComplianceOfficer role is
% scoped to globex (a different organization), not to acme.
%
% The naive intuition ("two compliance officers signed, that's quorum")
% is what most LLMs reproduce. The formalism does not agree. The quorum
% rule requires both signers to hold ComplianceOfficer AT THE FILING'S
% organization. Bob's role at globex does not count for an acme filing.
%
% This catches a real authorization bug class: counting role holders
% globally instead of per-org. In a multi-tenant policy product,
% getting this wrong means cross-org actors can quietly satisfy
% same-org quorum requirements.
%
% Expected verdict: CounterSatisfiable.
%--------------------------------------------------------------------

%----- quorum rule (identical to positive case)
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

%----- DIFFERENCE FROM POSITIVE CASE: bob holds the role at globex,
%       not at acme. Same role name, different organization.
fof(fact_bob_role_xorg, axiom, holdsRole(bob, complianceOfficer, globex)).

fof(fact_distinct,      axiom, jane != bob).
fof(fact_orgs_distinct, axiom, acme != globex).

%----- conjecture: should NOT be provable
fof(conjecture_quorum, conjecture,
    quorumSatisfied(filing77)).
