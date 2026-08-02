from django.contrib import admin
from leads.models import Lead, LeadPipeline, LeadStage, InteractionLog

admin.site.register(Lead)
admin.site.register(LeadPipeline)
admin.site.register(LeadStage)
admin.site.register(InteractionLog)
