from django.contrib import admin
from opportunity.models import Opportunity, OpportunityLineItem, StageAgingConfig, SalesGoal

admin.site.register(Opportunity)
admin.site.register(OpportunityLineItem)
admin.site.register(StageAgingConfig)
admin.site.register(SalesGoal)
