# ads/admin.py
from django.contrib import admin
from .models import AdPlacement, Ad

@admin.register(AdPlacement)
class AdPlacementAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'width', 'height')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ('name', 'placement', 'is_active', 'start_date', 'end_date', 'views', 'clicks')
    list_filter = ('placement', 'is_active', 'start_date', 'end_date')
    search_fields = ('name', 'code', 'target_url', 'alt_text')
    raw_id_fields = ('placement',) # Use a raw ID field for ForeignKey for better performance with many placements
    fieldsets = (
        (None, {
            'fields': ('name', 'placement', 'is_active')
        }),
        ('Content', {
            'fields': ('image', 'alt_text', 'target_url', 'code'),
            'description': 'Provide either an image/target URL or direct HTML/JavaScript code.'
        }),
        ('Scheduling & Tracking', {
            'fields': ('start_date', 'end_date', 'views', 'clicks'),
            'classes': ('collapse',), # Makes this section collapsible in the admin
        }),
    )
