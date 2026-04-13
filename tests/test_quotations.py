"""
tests/test_quotations.py — Quotation model, request, review, accept/reject lifecycle
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from quotations.models import Quotation
from clients.models import Client
from projects.models import Project
from payments.models import Invoice
from tests.helpers import (
    make_client_user, make_staff_user, make_admin_user,
    make_service, make_quotation, make_reviewed_quotation,
    StaffLoginMixin, ClientLoginMixin,
)


# ── MODEL ─────────────────────────────────────────────────────────────────────

class QuotationModelTest(TestCase):

    def setUp(self):
        self.user = make_client_user()
        self.service = make_service()

    def test_ref_auto_generated(self):
        q = make_quotation(self.user, self.service)
        self.assertIsNotNone(q.ref)
        self.assertEqual(len(q.ref), 8)

    def test_ref_unique(self):
        q1 = make_quotation(self.user, self.service)
        q2 = make_quotation(self.user, self.service)
        self.assertNotEqual(q1.ref, q2.ref)

    def test_str_contains_ref_and_service(self):
        q = make_quotation(self.user, self.service)
        self.assertIn(q.ref, str(q))
        self.assertIn(self.service.name, str(q))

    def test_default_status_is_pending(self):
        q = make_quotation(self.user, self.service)
        self.assertEqual(q.status, Quotation.STATUS_PENDING)

    def test_can_respond_true_when_awaiting_client(self):
        q = make_quotation(self.user, self.service, status='awaiting_client')
        self.assertTrue(q.can_respond)

    def test_can_respond_false_when_pending(self):
        q = make_quotation(self.user, self.service, status='pending')
        self.assertFalse(q.can_respond)

    def test_can_respond_false_when_already_accepted(self):
        q = make_quotation(self.user, self.service, status='accepted')
        self.assertFalse(q.can_respond)

    def test_status_badge_mapping(self):
        q = make_quotation(self.user, self.service, status='pending')
        self.assertEqual(q.status_badge, 'warning')
        q.status = 'accepted'
        self.assertEqual(q.status_badge, 'success')
        q.status = 'rejected'
        self.assertEqual(q.status_badge, 'danger')


# ── CLIENT: REQUEST QUOTATION ─────────────────────────────────────────────────

class QuotationRequestViewTest(ClientLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.service = make_service()

    def test_request_page_loads(self):
        response = self.client.get(reverse('request_quotation'))
        self.assertEqual(response.status_code, 200)

    def test_request_page_with_service_slug_loads(self):
        response = self.client.get(
            reverse('request_quotation_for_service', args=[self.service.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.service.name)

    def test_submit_quotation_request(self):
        response = self.client.post(
            reverse('request_quotation_for_service', args=[self.service.slug]),
            {
                'service': self.service.pk,
                'property_location': 'Karen, Nairobi',
                'property_size': '2 acres',
                'description': 'Need a boundary survey.',
                'urgency': 'normal',
                'additional_notes': '',
            }
        )
        self.assertEqual(Quotation.objects.count(), 1)
        q = Quotation.objects.first()
        self.assertRedirects(response, reverse('quotation_detail', args=[q.pk]))

    def test_submitted_quotation_belongs_to_logged_in_user(self):
        self.client.post(
            reverse('request_quotation_for_service', args=[self.service.slug]),
            {
                'service': self.service.pk,
                'property_location': 'Westlands',
                'description': 'Survey needed.',
                'urgency': 'normal',
            }
        )
        q = Quotation.objects.first()
        self.assertEqual(q.user, self.client_user)

    def test_quotation_request_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('request_quotation'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('request_quotation')}")


# ── CLIENT: VIEW QUOTATIONS ───────────────────────────────────────────────────

class QuotationListViewTest(ClientLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.service = make_service()

    def test_quotation_list_loads(self):
        response = self.client.get(reverse('quotation_list'))
        self.assertEqual(response.status_code, 200)

    def test_quotation_list_shows_own_quotations(self):
        q = make_quotation(self.client_user, self.service)
        response = self.client.get(reverse('quotation_list'))
        self.assertContains(response, q.ref)

    def test_quotation_list_hides_other_users_quotations(self):
        other = make_client_user(email='other@example.com')
        q = make_quotation(other, self.service)
        response = self.client.get(reverse('quotation_list'))
        self.assertNotContains(response, q.ref)

    def test_quotation_detail_loads(self):
        q = make_quotation(self.client_user, self.service)
        response = self.client.get(reverse('quotation_detail', args=[q.pk]))
        self.assertEqual(response.status_code, 200)

    def test_quotation_detail_of_other_user_returns_404(self):
        other = make_client_user(email='other2@example.com')
        q = make_quotation(other, self.service)
        response = self.client.get(reverse('quotation_detail', args=[q.pk]))
        self.assertEqual(response.status_code, 404)

    def test_quotation_detail_shows_accept_reject_when_awaiting(self):
        q = make_reviewed_quotation(self.client_user, self.service)
        response = self.client.get(reverse('quotation_detail', args=[q.pk]))
        self.assertContains(response, 'accept')
        self.assertContains(response, 'reject')

    def test_quotation_detail_hides_respond_when_pending(self):
        q = make_quotation(self.client_user, self.service, status='pending')
        response = self.client.get(reverse('quotation_detail', args=[q.pk]))
        self.assertNotContains(response, 'action="')


# ── CLIENT: ACCEPT / REJECT ───────────────────────────────────────────────────

class QuotationRespondViewTest(ClientLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.service = make_service()

    def test_accept_quotation_creates_client(self):
        q = make_reviewed_quotation(self.client_user, self.service, quoted_amount=50000)
        self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'accept'})
        self.assertTrue(Client.objects.filter(user=self.client_user).exists())

    def test_accept_quotation_creates_invoice(self):
        q = make_reviewed_quotation(self.client_user, self.service, quoted_amount=50000)
        self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'accept'})
        self.assertTrue(Invoice.objects.filter(client__user=self.client_user).exists())

    def test_accept_quotation_creates_project(self):
        q = make_reviewed_quotation(self.client_user, self.service, quoted_amount=50000)
        self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'accept'})
        self.assertTrue(Project.objects.filter(client__user=self.client_user).exists())

    def test_accept_quotation_creates_default_stages(self):
        q = make_reviewed_quotation(self.client_user, self.service, quoted_amount=50000)
        self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'accept'})
        project = Project.objects.get(client__user=self.client_user)
        self.assertEqual(project.stages.count(), 6)

    def test_accept_quotation_redirects_to_payment(self):
        q = make_reviewed_quotation(self.client_user, self.service, quoted_amount=50000)
        response = self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'accept'})
        invoice = Invoice.objects.get(client__user=self.client_user)
        self.assertRedirects(response, reverse('payment_detail', args=[invoice.pk]))

    def test_accept_sets_quotation_status_to_accepted(self):
        q = make_reviewed_quotation(self.client_user, self.service, quoted_amount=50000)
        self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'accept'})
        q.refresh_from_db()
        self.assertEqual(q.status, Quotation.STATUS_ACCEPTED)

    def test_reject_quotation_sets_status_to_rejected(self):
        q = make_reviewed_quotation(self.client_user, self.service)
        self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'reject'})
        q.refresh_from_db()
        self.assertEqual(q.status, Quotation.STATUS_REJECTED)

    def test_reject_redirects_to_quotation_list(self):
        q = make_reviewed_quotation(self.client_user, self.service)
        response = self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'reject'})
        self.assertRedirects(response, reverse('quotation_list'))

    def test_reject_does_not_create_client(self):
        q = make_reviewed_quotation(self.client_user, self.service)
        self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'reject'})
        self.assertFalse(Client.objects.filter(user=self.client_user).exists())

    def test_accept_without_quoted_amount_shows_error(self):
        q = make_quotation(self.client_user, self.service, status='awaiting_client', quoted_amount=None)
        response = self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'accept'})
        self.assertRedirects(response, reverse('quotation_detail', args=[q.pk]))
        self.assertFalse(Client.objects.filter(user=self.client_user).exists())

    def test_respond_to_pending_quotation_blocked(self):
        q = make_quotation(self.client_user, self.service, status='pending')
        response = self.client.post(reverse('quotation_respond', args=[q.pk]), {'action': 'accept'})
        self.assertRedirects(response, reverse('quotation_detail', args=[q.pk]))
        q.refresh_from_db()
        self.assertEqual(q.status, 'pending')

    def test_second_accept_reuses_existing_client(self):
        q1 = make_reviewed_quotation(self.client_user, self.service, quoted_amount=50000)
        self.client.post(reverse('quotation_respond', args=[q1.pk]), {'action': 'accept'})
        service2 = make_service(name='Topographic Survey', slug='topo-survey')
        q2 = make_reviewed_quotation(self.client_user, service2, quoted_amount=60000)
        self.client.post(reverse('quotation_respond', args=[q2.pk]), {'action': 'accept'})
        self.assertEqual(Client.objects.filter(user=self.client_user).count(), 1)


# ── STAFF: REVIEW QUOTATION ───────────────────────────────────────────────────

class StaffReviewQuotationTest(StaffLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.service = make_service()
        self.client_user = make_client_user()
        self.quotation = make_quotation(self.client_user, self.service)

    def test_review_page_loads(self):
        response = self.client.get(reverse('review_quotation', args=[self.quotation.pk]))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_approve_and_set_amount(self):
        self.client.post(reverse('review_quotation', args=[self.quotation.pk]), {
            'quoted_amount': '75000',
            'staff_notes': 'Site is accessible.',
            'status': 'awaiting_client',
            'valid_until': '2026-12-31',
        })
        self.quotation.refresh_from_db()
        self.assertEqual(self.quotation.status, 'awaiting_client')
        self.assertEqual(self.quotation.quoted_amount, Decimal('75000'))

    def test_staff_can_reject_quotation(self):
        self.client.post(reverse('review_quotation', args=[self.quotation.pk]), {
            'quoted_amount': '',
            'staff_notes': 'Out of service area.',
            'status': 'rejected',
            'valid_until': '',
        })
        self.quotation.refresh_from_db()
        self.assertEqual(self.quotation.status, 'rejected')

    def test_review_sets_reviewed_by(self):
        self.client.post(reverse('review_quotation', args=[self.quotation.pk]), {
            'quoted_amount': '50000',
            'staff_notes': 'OK.',
            'status': 'awaiting_client',
            'valid_until': '',
        })
        self.quotation.refresh_from_db()
        self.assertEqual(self.quotation.reviewed_by, self.staff_user)

    def test_client_cannot_access_review_page(self):
        client_user = make_client_user(email='c2@example.com')
        self.client.logout()
        self.client.login(username='c2@example.com', password='testpass123')
        response = self.client.get(reverse('review_quotation', args=[self.quotation.pk]))
        self.assertNotEqual(response.status_code, 200)
