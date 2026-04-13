from django.contrib import admin
from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'amount', 'amount_paid', 'status', 'due_date', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['invoice_number', 'client__user__email', 'client__client_id']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at']
