%--------------------------------------------------------------------
% BZ-AriaModelProvenance-01-neg - negative control
%
% Self-contained TPTP reduction of tests/BZ-AriaModelProvenance-01-neg.kif.tq.
% Same inference, same model, but the model has now been archived for a
% compliance-impacting cause (e.g. a discovered vulnerability that calls
% prior outputs into question).
%
% The naive intuition ("the inference was valid when made, of course it's
% still admissible") is what most LLMs reproduce. The formalism does not
% agree: admissibility is a property of the model's CURRENT compliance
% status, not its status at inference time. If the model has been
% archived for cause, the inference is no longer admissible.
%
% Note: this is the right policy for vulnerability-driven archival
% specifically. Routine performance-driven model rotation is a different
% case and would not assert modelArchivedForCause.
%
% Expected verdict: CounterSatisfiable.
%--------------------------------------------------------------------

%----- admissibility rule (identical to positive case)
fof(rule_admissibility, axiom,
    ! [P, M] :
      ( ( inferenceFromModel(P, M)
        & ~modelArchivedForCause(M) )
      => admissibleForCompliance(P) ) ).

%----- ground facts
fof(fact_provenance,    axiom,
    inferenceFromModel(inference17, aria01Gemma3v13)).

%----- DIFFERENCE FROM POSITIVE CASE: model is now archived for cause
fof(fact_model_archived, axiom,
    modelArchivedForCause(aria01Gemma3v13)).

%----- conjecture: should NOT be provable
fof(conjecture_admissible, conjecture,
    admissibleForCompliance(inference17)).
