from django.db import models
from django.conf import settings
from clients.models import Client
from services.models import Service


class Project(models.Model):
    STATUS_NOT_STARTED = 'not_started'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_ON_HOLD = 'on_hold'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NOT_STARTED, 'Not Started'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_ON_HOLD, 'On Hold'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='projects')
    quotation = models.OneToOneField(
        'quotations.Quotation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='project'
    )
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_projects'
    )

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    property_location = models.CharField(max_length=300, blank=True)
    property_size = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_NOT_STARTED)
    progress_percentage = models.PositiveSmallIntegerField(default=0)

    start_date = models.DateField(null=True, blank=True)
    expected_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)

    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} [{self.client.client_id}]'

    @property
    def status_badge(self):
        badges = {
            'not_started': 'secondary',
            'in_progress': 'primary',
            'on_hold': 'warning',
            'completed': 'success',
            'cancelled': 'danger',
        }
        return badges.get(self.status, 'secondary')

    @property
    def current_stage(self):
        return self.stages.filter(status='in_progress').first() or self.stages.filter(status='pending').first()


class ProjectStage(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_SKIPPED = 'skipped'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_SKIPPED, 'Skipped'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stages')
    order = models.PositiveSmallIntegerField(default=1)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True, verbose_name='Staff Update Notes')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='updated_stages'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['project', 'order']

    def __str__(self):
        return f'{self.project.title} – Stage {self.order}: {self.name}'

    @property
    def status_badge(self):
        badges = {
            'pending': 'secondary',
            'in_progress': 'primary',
            'completed': 'success',
            'skipped': 'warning',
        }
        return badges.get(self.status, 'secondary')

    @property
    def status_icon(self):
        icons = {
            'pending': 'bi-circle',
            'in_progress': 'bi-arrow-right-circle-fill',
            'completed': 'bi-check-circle-fill',
            'skipped': 'bi-dash-circle',
        }
        return icons.get(self.status, 'bi-circle')


class ProjectDocument(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='project_docs/')
    description = models.CharField(max_length=300, blank=True)
    is_public = models.BooleanField(default=False, help_text='Visible to client')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.project.title} – {self.name}'
