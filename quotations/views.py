from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Quotation
from .forms import QuotationRequestForm, ClientResponseForm
from services.models import Service
from clients.models import Client
from clients.utils import create_client_from_quotation
from django.core.mail import EmailMessage
from django.conf import settings


@login_required
def request_quotation(request, slug=None):
    service = get_object_or_404(Service, slug=slug, is_active=True) if slug else None
    if request.method == 'POST':
        form = QuotationRequestForm(request.POST, service=service)
        if form.is_valid():
            q = form.save(commit=False)
            q.user = request.user
            q.save()

            EmailMessage(
                subject=f'New Quotation Request - {q.service.name}',
                body=(
                    f'A new quotation request has been submitted.\n\n'
                    f'Client: {q.user.get_full_name() or q.user.email}\n'
                    f'Email: {q.user.email}\n'
                    f'Service: {q.service.name}\n'
                    f'Notes: {q.notes or "None"}'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.COMPANY_EMAIL],
                reply_to=[q.user.email],
            ).send(fail_silently=True)

            messages.success(request, 'Your quotation request has been submitted. We will review it and get back to you.')
            return redirect('quotation_detail', pk=q.pk)
    else:
        form = QuotationRequestForm(service=service)
    return render(request, 'quotations/request.html', {'form': form, 'service': service})


@login_required
def quotation_list(request):
    quotations = Quotation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'quotations/list.html', {'quotations': quotations})


@login_required
def quotation_detail(request, pk):
    q = get_object_or_404(Quotation, pk=pk, user=request.user)
    response_form = ClientResponseForm() if q.can_respond else None
    return render(request, 'quotations/detail.html', {'quotation': q, 'response_form': response_form})


@login_required
def quotation_respond(request, pk):
    q = get_object_or_404(Quotation, pk=pk, user=request.user)
    if not q.can_respond:
        messages.error(request, 'This quotation is not awaiting your response.')
        return redirect('quotation_detail', pk=pk)

    action = request.POST.get('action')
    notes = request.POST.get('client_response_notes', '')

    if action == 'accept':
        if not q.quoted_amount:
            messages.error(request, 'This quotation has no quoted amount set. Please contact us.')
            return redirect('quotation_detail', pk=pk)
        q.status = Quotation.STATUS_ACCEPTED
        q.client_response_notes = notes
        q.client_responded_at = timezone.now()
        q.save()
        # Create client + invoice
        client, invoice = create_client_from_quotation(q)
        messages.success(request, 'Quotation accepted! Your client profile and invoice have been created.')
        return redirect('payment_detail', pk=invoice.pk)

    elif action == 'reject':
        q.status = Quotation.STATUS_REJECTED
        q.client_response_notes = notes
        q.client_responded_at = timezone.now()
        q.save()
        messages.info(request, 'Quotation rejected. You can request a new quotation at any time.')
        return redirect('quotation_list')

    messages.error(request, 'Invalid action.')
    return redirect('quotation_detail', pk=pk)