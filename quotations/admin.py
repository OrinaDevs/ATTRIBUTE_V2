from django.contrib import admin
from .models import Quotation


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['ref', 'user', 'service', 'status', 'quoted_amount', 'reviewed_by', 'created_at']
    list_filter = ['status', 'service', 'created_at']
    search_fields = ['ref', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['ref', 'created_at', 'updated_at']
    ordering = ['-created_at']
