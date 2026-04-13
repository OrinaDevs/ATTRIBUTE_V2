from django.db import models
from django.conf import settings
import uuid


class Client(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    client_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_profile')
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_clients'
    )
    company_name = models.CharField(max_length=200, blank=True)
    kra_pin = models.CharField(max_length=30, blank=True, verbose_name='KRA PIN')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.client_id} – {self.user.full_name}'

    def save(self, *args, **kwargs):
        if not self.client_id:
            self.client_id = f'CLT-{str(uuid.uuid4()).upper()[:6]}'
        super().save(*args, **kwargs)

    @property
    def active_projects(self):
        return self.projects.filter(status='in_progress').count()

    @property
    def total_projects(self):
        return self.projects.count()
