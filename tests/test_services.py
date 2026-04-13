"""
tests/test_services.py — Service model, list view, detail view
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from services.models import Service, ServiceCategory
from tests.helpers import make_client_user, make_service, make_category


class ServiceCategoryModelTest(TestCase):

    def test_str(self):
        cat = make_category('Boundary & Title')
        self.assertEqual(str(cat), 'Boundary & Title')

    def test_ordering_by_order_field(self):
        ServiceCategory.objects.create(name='Z Cat', order=2)
        ServiceCategory.objects.create(name='A Cat', order=1)
        cats = list(ServiceCategory.objects.all())
        self.assertEqual(cats[0].name, 'A Cat')


class ServiceModelTest(TestCase):

    def test_str(self):
        svc = make_service('Boundary Survey')
        self.assertEqual(str(svc), 'Boundary Survey')

    def test_get_price_display_with_price(self):
        svc = make_service(base_price=25000)
        self.assertIn('25,000', svc.get_price_display())
        self.assertIn('KES', svc.get_price_display())

    def test_get_price_display_without_price(self):
        svc = make_service()
        svc.base_price = None
        svc.save()
        self.assertEqual(svc.get_price_display(), 'Request Quote')

    def test_get_deliverables_list(self):
        svc = make_service()
        svc.deliverables = 'Survey Report\nDeed Plan\nField Notes'
        svc.save()
        result = svc.get_deliverables_list()
        self.assertEqual(len(result), 3)
        self.assertIn('Survey Report', result)

    def test_get_deliverables_list_ignores_blank_lines(self):
        svc = make_service()
        svc.deliverables = 'Survey Report\n\nDeed Plan\n'
        svc.save()
        self.assertEqual(len(svc.get_deliverables_list()), 2)

    def test_inactive_service_not_in_default_queryset(self):
        make_service(name='Active Service')
        inactive = make_service(name='Inactive Service', slug='inactive-service')
        inactive.is_active = False
        inactive.save()
        active = Service.objects.filter(is_active=True)
        self.assertNotIn(inactive, active)


class ServiceListViewTest(TestCase):

    def setUp(self):
        self.user = make_client_user()
        self.client.login(username='client@example.com', password='testpass123')
        self.svc = make_service()

    def test_service_list_loads(self):
        response = self.client.get(reverse('service_list'))
        self.assertEqual(response.status_code, 200)

    def test_service_list_shows_active_services(self):
        response = self.client.get(reverse('service_list'))
        self.assertContains(response, self.svc.name)

    def test_inactive_service_not_shown(self):
        inactive = make_service(name='Hidden Service', slug='hidden-service')
        inactive.is_active = False
        inactive.save()
        response = self.client.get(reverse('service_list'))
        self.assertNotContains(response, 'Hidden Service')

    def test_service_list_accessible_without_login(self):
        self.client.logout()
        response = self.client.get(reverse('service_list'))
        self.assertEqual(response.status_code, 200)


class ServiceDetailViewTest(TestCase):

    def setUp(self):
        self.user = make_client_user()
        self.client.login(username='client@example.com', password='testpass123')
        self.svc = make_service()

    def test_service_detail_loads(self):
        response = self.client.get(reverse('service_detail', args=[self.svc.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.svc.name)

    def test_service_detail_contains_request_quote_link(self):
        response = self.client.get(reverse('service_detail', args=[self.svc.slug]))
        self.assertContains(response, reverse('request_quotation_for_service', args=[self.svc.slug]))

    def test_inactive_service_returns_404(self):
        self.svc.is_active = False
        self.svc.save()
        response = self.client.get(reverse('service_detail', args=[self.svc.slug]))
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_slug_returns_404(self):
        response = self.client.get(reverse('service_detail', args=['does-not-exist']))
        self.assertEqual(response.status_code, 404)
