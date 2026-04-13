"""
tests/test_payments.py — Invoice model, payment confirmation, PDF download
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from payments.models import Invoice
from projects.models import Project
from tests.helpers import (
    make_client_user, make_service, make_client,
    make_invoice, make_project, make_reviewed_quotation,
    ClientLoginMixin,
)


# ── INVOICE MODEL ─────────────────────────────────────────────────────────────

class InvoiceModelTest(TestCase):

    def setUp(self):
        self.user = make_client_user()
        self.client_obj = make_client(self.user)

    def test_invoice_number_auto_generated(self):
        inv = make_invoice(self.client_obj, amount=50000)
        self.assertIsNotNone(inv.invoice_number)
        self.assertIn(str(timezone.now().year), inv.invoice_number)

    def test_invoice_numbers_are_sequential(self):
        inv1 = make_invoice(self.client_obj, amount=10000)
        inv2 = make_invoice(self.client_obj, amount=20000)
        num1 = int(inv1.invoice_number.split('-')[1])
        num2 = int(inv2.invoice_number.split('-')[1])
        self.assertEqual(num2, num1 + 1)

    def test_str_contains_invoice_number_and_client(self):
        inv = make_invoice(self.client_obj)
        self.assertIn(inv.invoice_number, str(inv))

    def test_balance_due_calculation(self):
        inv = make_invoice(self.client_obj, amount=50000)
        inv.amount_paid = Decimal('20000')
        inv.save()
        self.assertEqual(inv.balance_due, Decimal('30000'))

    def test_balance_due_zero_when_fully_paid(self):
        inv = make_invoice(self.client_obj, amount=50000)
        inv.amount_paid = Decimal('50000')
        inv.save()
        self.assertEqual(inv.balance_due, Decimal('0'))

    def test_vat_amount_is_16_percent(self):
        inv = make_invoice(self.client_obj, amount=100000)
        self.assertEqual(inv.vat_amount, Decimal('16000'))

    def test_total_with_vat(self):
        inv = make_invoice(self.client_obj, amount=100000)
        self.assertEqual(inv.total_with_vat, Decimal('116000'))

    def test_status_badge_mapping(self):
        inv = make_invoice(self.client_obj, status='unpaid')
        self.assertEqual(inv.status_badge, 'danger')
        inv.status = 'paid'
        self.assertEqual(inv.status_badge, 'success')
        inv.status = 'partial'
        self.assertEqual(inv.status_badge, 'warning')
        inv.status = 'cancelled'
        self.assertEqual(inv.status_badge, 'secondary')

    def test_default_status_is_unpaid(self):
        inv = make_invoice(self.client_obj)
        self.assertEqual(inv.status, Invoice.STATUS_UNPAID)


# ── PAYMENT VIEWS ─────────────────────────────────────────────────────────────

class PaymentListViewTest(ClientLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.client_obj = make_client(self.client_user)
        self.invoice = make_invoice(self.client_obj, amount=50000)

    def test_payment_list_loads(self):
        response = self.client.get(reverse('payment_list'))
        self.assertEqual(response.status_code, 200)

    def test_payment_list_shows_own_invoices(self):
        response = self.client.get(reverse('payment_list'))
        self.assertContains(response, self.invoice.invoice_number)

    def test_payment_list_hides_other_users_invoices(self):
        other = make_client_user(email='other@example.com')
        other_client = make_client(other)
        other_inv = make_invoice(other_client, amount=30000)
        response = self.client.get(reverse('payment_list'))
        self.assertNotContains(response, other_inv.invoice_number)

    def test_payment_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('payment_list'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('payment_list')}")


class PaymentDetailViewTest(ClientLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.client_obj = make_client(self.client_user)
        self.invoice = make_invoice(self.client_obj, amount=50000)

    def test_payment_detail_loads(self):
        response = self.client.get(reverse('payment_detail', args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)

    def test_payment_detail_shows_invoice_number(self):
        response = self.client.get(reverse('payment_detail', args=[self.invoice.pk]))
        self.assertContains(response, self.invoice.invoice_number)

    def test_payment_detail_shows_amount(self):
        response = self.client.get(reverse('payment_detail', args=[self.invoice.pk]))
        self.assertContains(response, '50,000')

    def test_payment_detail_of_other_user_returns_404(self):
        other = make_client_user(email='other3@example.com')
        other_client = make_client(other)
        other_inv = make_invoice(other_client)
        response = self.client.get(reverse('payment_detail', args=[other_inv.pk]))
        self.assertEqual(response.status_code, 404)

    def test_download_link_present_on_detail(self):
        response = self.client.get(reverse('payment_detail', args=[self.invoice.pk]))
        self.assertContains(response, reverse('download_invoice', args=[self.invoice.pk]))


class PaymentConfirmViewTest(ClientLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.service = make_service()
        self.quotation = make_reviewed_quotation(self.client_user, self.service, quoted_amount=50000)
        self.client_obj = make_client(self.client_user)
        self.invoice = make_invoice(self.client_obj, quotation=self.quotation, amount=50000)
        self.project = make_project(self.client_obj, self.service, status='not_started')
        # Link quotation → project
        self.project.quotation = self.quotation
        self.project.save()

    def test_payment_confirm_page_loads(self):
        response = self.client.get(reverse('mark_payment', args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)

    def test_valid_payment_marks_invoice_paid(self):
        self.client.post(reverse('mark_payment', args=[self.invoice.pk]), {
            'payment_method': 'mpesa',
            'payment_reference': 'QHK123ABC9',
        })
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.STATUS_PAID)

    def test_valid_payment_sets_paid_at(self):
        self.client.post(reverse('mark_payment', args=[self.invoice.pk]), {
            'payment_method': 'mpesa',
            'payment_reference': 'QHK123ABC9',
        })
        self.invoice.refresh_from_db()
        self.assertIsNotNone(self.invoice.paid_at)

    def test_valid_payment_stores_reference(self):
        self.client.post(reverse('mark_payment', args=[self.invoice.pk]), {
            'payment_method': 'mpesa',
            'payment_reference': 'REF123XYZ',
        })
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.payment_reference, 'REF123XYZ')

    def test_payment_without_reference_stays_on_form(self):
        response = self.client.post(reverse('mark_payment', args=[self.invoice.pk]), {
            'payment_method': 'mpesa',
            'payment_reference': '',
        })
        self.assertRedirects(response, reverse('payment_detail', args=[self.invoice.pk]))
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.STATUS_UNPAID)

    def test_payment_activates_project(self):
        self.client.post(reverse('mark_payment', args=[self.invoice.pk]), {
            'payment_method': 'mpesa',
            'payment_reference': 'REF999',
        })
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.STATUS_IN_PROGRESS)

    def test_payment_redirects_to_invoice_detail(self):
        response = self.client.post(reverse('mark_payment', args=[self.invoice.pk]), {
            'payment_method': 'mpesa',
            'payment_reference': 'REF777',
        })
        self.assertRedirects(response, reverse('payment_detail', args=[self.invoice.pk]))


# ── PDF GENERATION ────────────────────────────────────────────────────────────

class InvoicePDFTest(ClientLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.client_obj = make_client(self.client_user)
        self.invoice = make_invoice(self.client_obj, amount=50000)

    def test_pdf_download_returns_200(self):
        response = self.client.get(reverse('download_invoice', args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)

    def test_pdf_download_content_type_is_pdf(self):
        response = self.client.get(reverse('download_invoice', args=[self.invoice.pk]))
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_pdf_download_has_attachment_header(self):
        response = self.client.get(reverse('download_invoice', args=[self.invoice.pk]))
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(self.invoice.invoice_number, response['Content-Disposition'])

    def test_pdf_download_of_other_user_invoice_returns_404(self):
        other = make_client_user(email='other4@example.com')
        other_client = make_client(other)
        other_inv = make_invoice(other_client)
        response = self.client.get(reverse('download_invoice', args=[other_inv.pk]))
        self.assertEqual(response.status_code, 404)

    def test_pdf_content_is_not_empty(self):
        response = self.client.get(reverse('download_invoice', args=[self.invoice.pk]))
        self.assertGreater(len(response.content), 1000)
