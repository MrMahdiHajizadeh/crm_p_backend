from django.contrib import admin
from business_hours.models import BusinessCalendar, BusinessHoliday

@admin.register(BusinessCalendar)
class BusinessCalendarAdmin(admin.ModelAdmin):
    list_display = ("name", "timezone", "is_default", "org", "created_at")
    list_filter = ("is_default", "timezone", "org", "created_at")
    search_fields = ("name",)
    raw_id_fields = ("org",)


@admin.register(BusinessHoliday)
class BusinessHolidayAdmin(admin.ModelAdmin):
    list_display = ("name", "calendar", "date", "created_at")
    list_filter = ("date", "calendar__org")
    search_fields = ("name", "calendar__name")
    raw_id_fields = ("calendar",)
