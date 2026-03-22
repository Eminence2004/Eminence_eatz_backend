from django.contrib import admin
from django.utils.html import format_html
from .models import OTPRecord

@admin.register(OTPRecord)
class OTPRecordAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'user_info', 'request_count', 'last_request_at', 'verified_status', 'time_since_last')
    list_filter = ('verified_at', 'last_request_at')
    search_fields = ('phone_number', 'user__email', 'user__username', 'user__phone_number')
    readonly_fields = ('request_count', 'last_request_at', 'verified_at', 'created_at_display')
    date_hierarchy = 'last_request_at'
    
    fieldsets = (
        ('Phone Information', {
            'fields': ('phone_number', 'user')
        }),
        ('Usage Statistics', {
            'fields': ('request_count', 'last_request_at', 'verified_at', 'created_at_display')
        }),
    )
    
    def user_info(self, obj):
        if obj.user:
            return format_html(
                '<strong>{}</strong><br/><small>{}</small>',
                obj.user.get_full_name() or obj.user.username,
                obj.user.email
            )
        return "-"
    user_info.short_description = 'User'
    user_info.admin_order_field = 'user'
    
    def verified_status(self, obj):
        if obj.verified_at:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Verified</span><br/><small>{}</small>',
                obj.verified_at.strftime('%Y-%m-%d %H:%M')
            )
        return format_html('<span style="color: orange;">⏳ Pending</span>')
    verified_status.short_description = 'Verification Status'
    
    def time_since_last(self, obj):
        if obj.last_request_at:
            delta = timezone.now() - obj.last_request_at
            if delta.days > 0:
                return f"{delta.days} days ago"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600} hours ago"
            else:
                return f"{delta.seconds // 60} minutes ago"
        return "-"
    time_since_last.short_description = 'Last Activity'
    
    def created_at_display(self, obj):
        return obj.last_request_at
    created_at_display.short_description = 'First Request'
    created_at_display.admin_order_field = 'last_request_at'
    
    actions = ['mark_as_verified', 'reset_request_count']
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(verified_at=timezone.now())
        self.message_user(request, f'{updated} records marked as verified.')
    mark_as_verified.short_description = "Mark selected as verified"
    
    def reset_request_count(self, request, queryset):
        updated = queryset.update(request_count=0)
        self.message_user(request, f'{updated} records had their request count reset.')
    reset_request_count.short_description = "Reset request count"