from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Customized User admin with role management."""
    list_display = ['username', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_editable = ['role']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('WriteSphere Profile', {
            'fields': ('role', 'bio', 'avatar', 'website', 'date_of_birth'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('WriteSphere Profile', {
            'fields': ('role', 'email'),
        }),
    )


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    """Admin for viewing OTP records."""
    list_display = ['email', 'otp', 'is_verified', 'is_expired', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['email']
    readonly_fields = ['email', 'otp', 'created_at']
    ordering = ['-created_at']

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired?'
