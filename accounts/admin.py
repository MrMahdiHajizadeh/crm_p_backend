from django.contrib import admin
from accounts.models import Account, AccountEmail, AccountEmailLog

admin.site.register(Account)
admin.site.register(AccountEmail)
admin.site.register(AccountEmailLog)
