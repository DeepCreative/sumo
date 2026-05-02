%--------------------------------------------------------------------
% BZ-RbacScope-01 — positive case
%
% Self-contained TPTP reduction of tests/BZ-RbacScope-01.kif.tq.
% Proves that Jane, who holds ComplianceOfficer at Acme, is permitted
% to perform FilingSign FOR Acme.  This works because scopeIncludes
% is reflexive: every organization includes itself in its own scope.
%
% Expected verdict: Theorem.
%--------------------------------------------------------------------

%----- reflexive scope: every organization is in its own scope
fof(rule_scope_reflexive, axiom,
    ! [O] : ( organization(O) => scopeIncludes(O, O) ) ).

%----- permission derivation: holding a role within scope S grants the
%       role's permissions for any target T included in S
fof(rule_permission, axiom,
    ! [P, R, S, Perm, T] :
      ( ( holdsRole(P, R, S)
        & roleGrants(R, Perm)
        & scopeIncludes(S, T) )
      => permitted(P, Perm, T) ) ).

%----- ground facts
fof(fact_acme,    axiom, organization(acme)).
fof(fact_acmeSub, axiom, organization(acmeSubsidiary)).

fof(fact_role,    axiom, holdsRole(jane, complianceOfficer, acme)).
fof(fact_grant,   axiom, roleGrants(complianceOfficer, filingSign)).

%----- conjecture: jane can sign filings FOR acme
fof(conjecture_acme, conjecture,
    permitted(jane, filingSign, acme)).
