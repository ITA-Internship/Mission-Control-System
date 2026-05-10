from django.contrib import admin

from .models import Mission


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'commander', 'started_at', 'created_by', 'created_at')
    list_filter = ('status', 'result')
    search_fields = ('title', 'location_description')
    readonly_fields = ('created_at', 'updated_at')
