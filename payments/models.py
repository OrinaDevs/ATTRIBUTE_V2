from django.db import models
from clients.models import Client
import uuid


class Invoice(models.Model):
    STATUS_UNPAID = 'unpaid'
    STATUS_PARTIAL = 'partial'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_UNPAID, 'Unpaid'),
        (STATUS_PARTIAL, 'Partially Paid'),
        (STATUS_PAID, 'Paid'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=30, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    quotation = models.OneToOneField(
        'quotations.Quotation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoice'
    )
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNPAID)
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'INV-{self.invoice_number} | {self.client}'

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            year = __import__('datetime').date.today().year
            count = Invoice.objects.filter(created_at__year=year).count() + 1
            self.invoice_number = f'{year}-{count:04d}'
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        return self.amount - self.amount_paid

    @property
    def status_badge(self):
        return {'unpaid': 'danger', 'partial': 'warning', 'paid': 'success', 'cancelled': 'secondary'}.get(self.status, 'secondary')

    @property
    def vat_amount(self):
        return self.amount * 16 / 100

    @property
    def total_with_vat(self):
        return self.amount + self.vat_amount
