from django.contrib import admin
from .models import Project, ProjectStage, ProjectDocument


class ProjectStageInline(admin.TabularInline):
    model = ProjectStage
    extra = 0
    fields = ['order', 'name', 'status', 'notes', 'updated_by', 'completed_at']
    readonly_fields = ['updated_by']


class ProjectDocumentInline(admin.TabularInline):
    model = ProjectDocument
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'service', 'assigned_staff', 'status', 'progress_percentage', 'created_at']
    list_filter = ['status', 'service', 'created_at']
    search_fields = ['title', 'client__user__email', 'client__client_id']
    list_editable = ['assigned_staff', 'status']
    raw_id_fields = ['client', 'assigned_staff', 'quotation']
    inlines = [ProjectStageInline, ProjectDocumentInline]
    readonly_fields = ['created_at', 'updated_at']

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, ProjectStage):
                instance.updated_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(ProjectStage)
class ProjectStageAdmin(admin.ModelAdmin):
    list_display = ['project', 'order', 'name', 'status', 'updated_by', 'updated_at']
    list_filter = ['status']
