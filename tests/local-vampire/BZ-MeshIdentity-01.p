%--------------------------------------------------------------------
% BZ-MeshIdentity-01 — positive case
%
% Self-contained TPTP reduction of tests/BZ-MeshIdentity-01.kif.tq.
% Proves that CarouselApi can observe Jane as the original principal
% of Req-42 across a well-formed 2-hop IUCT chain.
%
% Expected verdict: Theorem.
%--------------------------------------------------------------------

%----- base case: origin service makes one allowlisted hop
fof(rule_base, axiom,
    ! [A, B, R, U] :
      ( ( originatesRequest(A, R)
        & originalPrincipal(R, U)
        & iuctChainHop(A, B)
        & principalAllowlisted(A, B) )
      => visiblePrincipal(B, R, U) ) ).

%----- inductive step: visibility propagates one more hop iff
%       both the hop and the allowlist entry exist
fof(rule_inductive, axiom,
    ! [B, C, R, U] :
      ( ( visiblePrincipal(B, R, U)
        & iuctChainHop(B, C)
        & principalAllowlisted(B, C) )
      => visiblePrincipal(C, R, U) ) ).

%----- ground facts: well-formed 2-hop chain
%       hydra -> athenaApi -> carouselApi
%       request req42 originated at hydra by user jane
fof(fact_origin,     axiom, originatesRequest(hydra, req42)).
fof(fact_principal,  axiom, originalPrincipal(req42, jane)).
fof(fact_hop1,       axiom, iuctChainHop(hydra, athenaApi)).
fof(fact_hop2,       axiom, iuctChainHop(athenaApi, carouselApi)).
fof(fact_allow1,     axiom, principalAllowlisted(hydra, athenaApi)).
fof(fact_allow2,     axiom, principalAllowlisted(athenaApi, carouselApi)).

%----- conjecture: carouselApi sees jane as the principal of req42
fof(conjecture_visibility, conjecture,
    visiblePrincipal(carouselApi, req42, jane)).
