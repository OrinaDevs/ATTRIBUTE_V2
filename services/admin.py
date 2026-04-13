from django.contrib import admin
from .models import Service, ServiceCategory, ServiceStage

class ServiceSatgeInline(admin.TabularInline):
    model = ServiceStage
    extra = 1
    fields = ['order', 'name', 'description']

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    prepopulated_fields = {}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'base_price', 'is_active', 'is_featured', 'order']
    list_filter = ['is_active', 'is_featured', 'category']
    list_editable = ['is_active', 'is_featured', 'order']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ServiceSatgeInline]
