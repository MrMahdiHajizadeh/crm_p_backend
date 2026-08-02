from django.contrib import admin
from cases.models import (
    Case,
    CaseWatcher,
    CsatSurvey,
    Solution,
    CasePipeline,
    CaseStage,
    ReopenPolicy,
    EscalationPolicy,
    InboundMailbox,
    EmailMessage,
    TimeEntry,
    ApprovalRule,
    Approval,
)

admin.site.register(Case)
admin.site.register(CaseWatcher)
admin.site.register(CsatSurvey)
admin.site.register(Solution)
admin.site.register(CasePipeline)
admin.site.register(CaseStage)
admin.site.register(ReopenPolicy)
admin.site.register(EscalationPolicy)
admin.site.register(InboundMailbox)
admin.site.register(EmailMessage)
admin.site.register(TimeEntry)
admin.site.register(ApprovalRule)
admin.site.register(Approval)
