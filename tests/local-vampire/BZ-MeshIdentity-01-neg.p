%--------------------------------------------------------------------
% BZ-MeshIdentity-01-neg — negative control
%
% Self-contained TPTP reduction of tests/BZ-MeshIdentity-01-neg.kif.tq.
% IDENTICAL to BZ-MeshIdentity-01.p EXCEPT one principalAllowlisted
% entry is omitted: principalAllowlisted(athenaApi, carouselApi).
%
% The IUCT hops are still end-to-end; the JWT-forwarding intuition would
% still conclude visibility.  The formalism does not agree: the
% inductive step requires BOTH the hop AND the allowlist entry.  With
% the allowlist missing, the chain breaks at AthenaApi -> CarouselApi.
%
% Expected verdict: CounterSatisfiable (Vampire cannot prove the
% conjecture, and finds a model in which it is false).  If Vampire
% returns Theorem here, the axioms are overclaiming and need to be
% tightened.
%--------------------------------------------------------------------

%----- base case
fof(rule_base, axiom,
    ! [A, B, R, U] :
      ( ( originatesRequest(A, R)
        & originalPrincipal(R, U)
        & iuctChainHop(A, B)
        & principalAllowlisted(A, B) )
      => visiblePrincipal(B, R, U) ) ).

%----- inductive step
fof(rule_inductive, axiom,
    ! [B, C, R, U] :
      ( ( visiblePrincipal(B, R, U)
        & iuctChainHop(B, C)
        & principalAllowlisted(B, C) )
      => visiblePrincipal(C, R, U) ) ).

%----- ground facts: hops still present, ONE allowlist entry omitted
fof(fact_origin,     axiom, originatesRequest(hydra, req42)).
fof(fact_principal,  axiom, originalPrincipal(req42, jane)).
fof(fact_hop1,       axiom, iuctChainHop(hydra, athenaApi)).
fof(fact_hop2,       axiom, iuctChainHop(athenaApi, carouselApi)).
fof(fact_allow1,     axiom, principalAllowlisted(hydra, athenaApi)).
% fof(fact_allow2,   axiom, principalAllowlisted(athenaApi, carouselApi)).
%                    ^^^ INTENTIONALLY OMITTED for negative control

%----- conjecture: should NOT be provable
fof(conjecture_visibility, conjecture,
    visiblePrincipal(carouselApi, req42, jane)).
