%--------------------------------------------------------------------
% BZ-RbacScope-01-neg — negative control
%
% Self-contained TPTP reduction of tests/BZ-RbacScope-01-neg.kif.tq.
% IDENTICAL to BZ-RbacScope-01.p EXCEPT the conjecture asks about
% permission for Acme-Subsidiary instead of Acme.  No scopeIncludes
% relationship between Acme and Acme-Subsidiary is asserted, so the
% chain breaks: Jane's role at Acme does NOT propagate downward.
%
% LLMs asked this question almost always answer yes ("she's a
% compliance officer at the parent, of course she can sign for the
% subsidiary").  The formalism does not agree.  An LLM's intuition
% conflates "having a role at the parent organization" with "having
% authority over child organizations" — which is a frequent
% real-world authorization bug.
%
% Expected verdict: CounterSatisfiable.  If Vampire returns Theorem
% here, the rules are over-permissive and need tightening.
%--------------------------------------------------------------------

%----- reflexive scope
fof(rule_scope_reflexive, axiom,
    ! [O] : ( organization(O) => scopeIncludes(O, O) ) ).

%----- permission derivation
fof(rule_permission, axiom,
    ! [P, R, S, Perm, T] :
      ( ( holdsRole(P, R, S)
        & roleGrants(R, Perm)
        & scopeIncludes(S, T) )
      => permitted(P, Perm, T) ) ).

%----- ground facts (identical to positive case)
fof(fact_acme,    axiom, organization(acme)).
fof(fact_acmeSub, axiom, organization(acmeSubsidiary)).

fof(fact_role,    axiom, holdsRole(jane, complianceOfficer, acme)).
fof(fact_grant,   axiom, roleGrants(complianceOfficer, filingSign)).

% NOTE: no scopeIncludes(acme, acmeSubsidiary) is asserted.

%----- conjecture: jane can sign filings FOR acmeSubsidiary
%                  (this should NOT be provable)
fof(conjecture_subsidiary, conjecture,
    permitted(jane, filingSign, acmeSubsidiary)).
