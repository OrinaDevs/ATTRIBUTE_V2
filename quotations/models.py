from django.db import models
from django.conf import settings
from services.models import Service
import uuid


class Quotation(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_UNDER_REVIEW = 'under_review'
    STATUS_AWAITING_CLIENT = 'awaiting_client'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_EXPIRED = 'expired'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_AWAITING_CLIENT, 'Awaiting Client Response'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    ref = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quotations')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='quotations')

    # Client details at time of request
    property_location = models.CharField(max_length=300, verbose_name='Property / Site Location')
    property_size = models.CharField(max_length=100, blank=True, verbose_name='Approximate Size (acres/ha/sqm)')
    description = models.TextField(verbose_name='Project Description / Requirements')
    urgency = models.CharField(max_length=30, choices=[
        ('normal', 'Normal (2–4 weeks)'),
        ('urgent', 'Urgent (within 1 week)'),
        ('flexible', 'Flexible'),
    ], default='normal')
    additional_notes = models.TextField(blank=True)

    # Staff fills in
    quoted_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    staff_notes = models.TextField(blank=True, verbose_name='Staff Review Notes')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_quotations'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Client response
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    client_response_notes = models.TextField(blank=True)
    client_responded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    valid_until = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'QUO-{self.ref} | {self.service.name} | {self.user.full_name}'

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = str(uuid.uuid4()).upper()[:8]
        super().save(*args, **kwargs)

    @property
    def can_respond(self):
        return self.status == self.STATUS_AWAITING_CLIENT

    @property
    def status_badge(self):
        badges = {
            'pending': 'warning',
            'under_review': 'info',
            'awaiting_client': 'primary',
            'accepted': 'success',
            'rejected': 'danger',
            'expired': 'secondary',
        }
        return badges.get(self.status, 'secondary')
