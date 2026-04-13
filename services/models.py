from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-geo-alt', help_text='Bootstrap icon class')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Service Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='services')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text='Starting price (KES)')
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    duration_estimate = models.CharField(max_length=100, blank=True, help_text='e.g. 2-4 weeks')
    deliverables = models.TextField(blank=True, help_text='Bullet points of what client receives')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_price_display(self):
        if self.base_price:
            return f'From KES {self.base_price:,.0f}'
        return 'Request Quote'

    def get_deliverables_list(self):
        return [d.strip() for d in self.deliverables.split('\n') if d.strip()]

class ServiceStage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='default_stages')
    order = models.PositiveSmallIntegerField(default=1)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['order']
        unique_together = ['service', 'order']
    
    def __str__(self):
        return f'{self.service.name} - Stage {self.order}: {self.name}'