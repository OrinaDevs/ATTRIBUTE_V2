from django.shortcuts import render, get_object_or_404
from .models import Service, ServiceCategory


def service_list(request):
    categories = ServiceCategory.objects.prefetch_related('services').filter(services__is_active=True).distinct()
    services = Service.objects.filter(is_active=True)
    featured = services.filter(is_featured=True)
    cat_filter = request.GET.get('category', '')
    if cat_filter:
        services = services.filter(category__slug=cat_filter) if hasattr(ServiceCategory, 'slug') else services.filter(category__name__icontains=cat_filter)
    return render(request, 'services/list.html', {
        'services': services, 'categories': categories,
        'featured': featured, 'cat_filter': cat_filter,
    })


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    related = Service.objects.filter(category=service.category, is_active=True).exclude(pk=service.pk)[:3]
    return render(request, 'services/detail.html', {'service': service, 'related': related})
