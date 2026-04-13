from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from services.models import Service, ServiceCategory


def home(request):
    services = Service.objects.filter(is_active=True, is_featured=True)[:6]
    all_services = Service.objects.filter(is_active=True)[:9]
    categories = ServiceCategory.objects.all()
    return render(request, 'core/home.html', {
        'featured_services': services,
        'all_services': all_services,
        'categories': categories,
    })


def about(request):
    return render(request, 'core/about.html')


def contact(request):
    from django.contrib import messages
    from django.core.mail import EmailMessage
    from django.conf import settings 
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', ''). strip()
        phone = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        full_subject = f'Contact Form: {subject}'

        body = (
            f'Name:     {name}\n'
            f'Email:    {email}\n'
            f'Phone:    {phone or "Not provided"}\n\n'
            f'{message}'
        )

        EmailMessage(
            subject=full_subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.COMPANY_EMAIL],
            reply_to=[email],
        ).send(fail_silently=True)
        
        messages.success(request, 'Thank you for your message. We will get back to you shortly.')
        return redirect('contact')
    return render(request, 'core/contact.html')
