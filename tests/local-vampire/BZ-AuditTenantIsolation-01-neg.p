%--------------------------------------------------------------------
% BZ-AuditTenantIsolation-01-neg - negative control
%
% Self-contained TPTP reduction of tests/BZ-AuditTenantIsolation-01-neg.kif.tq.
% IDENTICAL setup to the positive case EXCEPT withinCaseWindow is omitted.
% The audit event is timestamped OUTSIDE the support case's active window.
%
% Sarah is still a support engineer with a case covering acme. The audit
% event is still from acme. The naive intuition ("she's support, she
% can see it") would still conclude visibility. The formalism does not
% agree: the support-case rule requires withinCaseWindow as a conjunct,
% and the same-tenant rule does not apply because sarah's tenant is
% supportTenant, not acme.
%
% LLMs asked this question almost always answer yes. The answer is no
% unless the event is within the support case's time window.
%
% Expected verdict: CounterSatisfiable.
%--------------------------------------------------------------------

%----- same-tenant rule
fof(rule_same_tenant, axiom,
    ! [U, E, T] :
      ( ( userTenant(U, T)
        & auditEventTenant(E, T) )
      => visibleAudit(U, E) ) ).

%----- support-case exception (window required)
fof(rule_support_window, axiom,
    ! [U, E, T, C] :
      ( ( staffOf(U, C)
        & caseIncludesTenant(C, T)
        & auditEventTenant(E, T)
        & withinCaseWindow(C, E) )
      => visibleAudit(U, E) ) ).

%----- ground facts (note: NO withinCaseWindow assertion)
fof(fact_sarah_tenant,    axiom, userTenant(sarah, supportTenant)).
fof(fact_event_tenant,    axiom, auditEventTenant(auditE99, acme)).
fof(fact_sarah_staff,     axiom, staffOf(sarah, supportCase42)).
fof(fact_case_covers,     axiom, caseIncludesTenant(supportCase42, acme)).
% fof(fact_within_window, axiom, withinCaseWindow(supportCase42, auditE99)).
%                                ^^^ INTENTIONALLY OMITTED

%----- conjecture: should NOT be provable
fof(conjecture_visible, conjecture,
    visibleAudit(sarah, auditE99)).
