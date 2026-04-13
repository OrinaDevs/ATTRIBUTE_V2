from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.utils import timezone
from .models import Invoice
from .pdf_generator import generate_invoice_pdf


@login_required
def payment_list(request):
    try:
        client = request.user.client_profile
        invoices = Invoice.objects.filter(client=client).order_by('-created_at')
    except Exception:
        invoices = Invoice.objects.none()
    return render(request, 'payments/list.html', {'invoices': invoices})


@login_required
def payment_detail(request, pk):
    try:
        client = request.user.client_profile
        invoice = get_object_or_404(Invoice, pk=pk, client=client)
    except Exception:
        raise Http404
    return render(request, 'payments/detail.html', {'invoice': invoice})


@login_required
def download_invoice_pdf(request, pk):
    try:
        client = request.user.client_profile
        invoice = get_object_or_404(Invoice, pk=pk, client=client)
    except Exception:
        raise Http404

    pdf_bytes = generate_invoice_pdf(invoice)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice-{invoice.invoice_number}.pdf"'
    return response


@login_required
def mark_payment(request, pk):
    """Simulated payment confirmation (replace with real gateway)."""
    try:
        client = request.user.client_profile
        invoice = get_object_or_404(Invoice, pk=pk, client=client)
    except Exception:
        raise Http404

    if request.method == 'POST':
        method = request.POST.get('payment_method', 'mpesa')
        ref = request.POST.get('payment_reference', '').strip()
        if not ref:
            messages.error(request, 'Please enter your payment reference / transaction code.')
            return redirect('payment_detail', pk=pk)
        invoice.status = Invoice.STATUS_PAID
        invoice.amount_paid = invoice.amount
        invoice.paid_at = timezone.now()
        invoice.payment_method = method
        invoice.payment_reference = ref
        invoice.save()

        # Activate project
        try:
            project = invoice.quotation.project
            if project.status == 'not_started':
                project.status = 'in_progress'
                from django.utils import timezone as tz
                project.start_date = tz.now().date()
                project.save()
        except Exception:
            pass

        messages.success(request, 'Payment recorded! Your project is now active. Download your receipt below.')
        return redirect('payment_detail', pk=pk)

    return render(request, 'payments/confirm_payment.html', {'invoice': invoice})
