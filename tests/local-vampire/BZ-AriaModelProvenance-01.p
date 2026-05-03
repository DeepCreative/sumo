%--------------------------------------------------------------------
% BZ-AriaModelProvenance-01 - positive case
%
% Self-contained TPTP reduction of tests/BZ-AriaModelProvenance-01.kif.tq.
% Proves that an inference produced by an active (non-archived) ARIA
% model is admissible for compliance use.
%
% Setup:
%   inference17 was produced by aria01-gemma3-9b-v13
%   the model has not been archived for any compliance-impacting cause
%
% Expected verdict: Theorem.
%--------------------------------------------------------------------

%----- admissibility rule: an inference is admissible for compliance
%       use iff its source model has NOT been archived for a
%       compliance-impacting cause. The negation is classical: the
%       prover requires either no archival fact OR an explicit
%       not-archived assertion to derive admissibility.
fof(rule_admissibility, axiom,
    ! [P, M] :
      ( ( inferenceFromModel(P, M)
        & ~modelArchivedForCause(M) )
      => admissibleForCompliance(P) ) ).

%----- ground facts
fof(fact_provenance,    axiom,
    inferenceFromModel(inference17, aria01Gemma3v13)).

%----- explicit positive assertion: the model is not under
%       compliance-impacting archival
fof(fact_model_active,  axiom,
    ~modelArchivedForCause(aria01Gemma3v13)).

%----- conjecture: inference17 is admissible
fof(conjecture_admissible, conjecture,
    admissibleForCompliance(inference17)).
