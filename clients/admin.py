from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['client_id', 'user', 'company_name', 'assigned_staff', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['client_id', 'user__email', 'user__first_name', 'company_name']
    raw_id_fields = ['user', 'assigned_staff']
    readonly_fields = ['client_id', 'created_at']
