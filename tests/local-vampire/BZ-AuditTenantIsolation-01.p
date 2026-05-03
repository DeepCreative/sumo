%--------------------------------------------------------------------
% BZ-AuditTenantIsolation-01 - positive case
%
% Self-contained TPTP reduction of tests/BZ-AuditTenantIsolation-01.kif.tq.
% Proves that a support engineer with an active, in-window support case
% covering tenant A can legitimately query an audit event emitted by A.
%
% Setup:
%   sarah is staff on supportCase42
%   supportCase42 covers tenant acme
%   auditE-99 was emitted by acme
%   auditE-99 is timestamped WITHIN supportCase42's window
%
% Expected verdict: Theorem.
%--------------------------------------------------------------------

%----- same-tenant rule: a user in tenant T may query audit events
%       emitted by T
fof(rule_same_tenant, axiom,
    ! [U, E, T] :
      ( ( userTenant(U, T)
        & auditEventTenant(E, T) )
      => visibleAudit(U, E) ) ).

%----- support-case exception: a support engineer staffed on case C
%       may query audit events from a tenant the case covers, BUT
%       only if the event is timestamped within the case's active
%       window. Drop withinCaseWindow and the exception does not fire.
fof(rule_support_window, axiom,
    ! [U, E, T, C] :
      ( ( staffOf(U, C)
        & caseIncludesTenant(C, T)
        & auditEventTenant(E, T)
        & withinCaseWindow(C, E) )
      => visibleAudit(U, E) ) ).

%----- ground facts
fof(fact_sarah_tenant,    axiom, userTenant(sarah, supportTenant)).
fof(fact_event_tenant,    axiom, auditEventTenant(auditE99, acme)).
fof(fact_sarah_staff,     axiom, staffOf(sarah, supportCase42)).
fof(fact_case_covers,     axiom, caseIncludesTenant(supportCase42, acme)).
fof(fact_within_window,   axiom, withinCaseWindow(supportCase42, auditE99)).

%----- conjecture: sarah can legitimately query auditE99
fof(conjecture_visible, conjecture,
    visibleAudit(sarah, auditE99)).
