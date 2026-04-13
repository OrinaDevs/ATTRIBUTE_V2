"""
Management command: python manage.py seed_data

Creates:
 - Admin user (admin@attributesurvey.co.ke / admin1234)
 - Staff user  (staff@attributesurvey.co.ke / staff1234)
 - Sample client user (client@example.com / client1234)
 - Service categories & services
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from accounts.models import User, StaffProfile
from services.models import Service, ServiceCategory


CATEGORIES = [
    {'name': 'Boundary & Title', 'icon': 'geo-alt-fill', 'order': 1},
    {'name': 'Topographic & Engineering', 'icon': 'map', 'order': 2},
    {'name': 'Valuation & Advisory', 'icon': 'cash-coin', 'order': 3},
    {'name': 'Environmental', 'icon': 'tree', 'order': 4},
]

SERVICES = [
    {
        'category': 'Boundary & Title',
        'name': 'Boundary Survey',
        'description': 'Precise demarcation of property boundaries in accordance with registered deed plans and Survey of Kenya standards. Includes field work, beacon placement, and certified survey report.',
        'short_description': 'Precise property boundary demarcation with certified survey report.',
        'base_price': 25000,
        'duration_estimate': '1–3 weeks',
        'deliverables': 'Deed Plan Copy\nField Notes\nSurvey Report\nBeacon Placement\nRegistry Index Map (RIM)',
        'is_featured': True,
    },
    {
        'category': 'Boundary & Title',
        'name': 'Title Deed Processing',
        'description': 'End-to-end processing of land title deeds including mutation, subdivision, amalgamation, and first registration. We liaise with the Lands Ministry on your behalf.',
        'short_description': 'Full title deed processing — mutation, subdivision, first registration.',
        'base_price': 30000,
        'duration_estimate': '4–12 weeks',
        'deliverables': 'Title Deed\nRegistry Index Map\nMutation Form\nConsent Letters',
        'is_featured': True,
    },
    {
        'category': 'Topographic & Engineering',
        'name': 'Topographic Survey',
        'description': 'Detailed topographic mapping of land using total stations and GPS equipment. Produces contour maps and digital terrain models used for architectural and engineering design.',
        'short_description': 'Detailed contour mapping and digital terrain models for design purposes.',
        'base_price': 35000,
        'duration_estimate': '1–4 weeks',
        'deliverables': 'Topographic Map (PDF & DWG)\nContour Plan\nDigital Terrain Model\nSurvey Report',
        'is_featured': True,
    },
    {
        'category': 'Topographic & Engineering',
        'name': 'Setting Out Survey',
        'description': 'Transfer of architectural or engineering designs onto the ground for construction purposes. Ensures buildings, roads, and infrastructure are constructed in the correct position.',
        'short_description': 'Accurate transfer of construction designs to site.',
        'base_price': 20000,
        'duration_estimate': '1–5 days',
        'deliverables': 'Setting-out Report\nAs-built Survey\nField Records',
        'is_featured': False,
    },
    {
        'category': 'Valuation & Advisory',
        'name': 'Property Valuation',
        'description': 'Professional valuation of land and property for sale, mortgage, insurance, stamp duty, or legal purposes. Conducted by registered valuers in accordance with RICS standards.',
        'short_description': 'Certified property valuation for sale, mortgage, or legal use.',
        'base_price': 15000,
        'duration_estimate': '3–7 days',
        'deliverables': 'Valuation Certificate\nValuation Report\nMarket Analysis',
        'is_featured': True,
    },
    {
        'category': 'Environmental',
        'name': 'Environmental Impact Assessment (EIA)',
        'description': 'Statutory EIA and environmental audits required before development. We prepare full EIA reports in compliance with NEMA regulations and coordinate submission and approval.',
        'short_description': 'NEMA-compliant EIA reports for development projects.',
        'base_price': 80000,
        'duration_estimate': '4–8 weeks',
        'deliverables': 'EIA Study Report\nProject Report\nEnvironmental Management Plan\nNEMA Licence',
        'is_featured': True,
    },
    {
        'category': 'Boundary & Title',
        'name': 'Land Subdivision',
        'description': 'Subdivision of land parcels into smaller plots in compliance with county physical planning regulations. Includes preparation of subdivision scheme, approval, and beacon placement.',
        'short_description': 'Subdivision of land into smaller plots with county approval.',
        'base_price': 50000,
        'duration_estimate': '6–16 weeks',
        'deliverables': 'Subdivision Scheme Plan\nApproval Letters\nNew Title Deeds\nBeacon Placement',
        'is_featured': False,
    },
    {
        'category': 'Topographic & Engineering',
        'name': 'Road & Infrastructure Survey',
        'description': 'Survey services for road design, corridor mapping, and infrastructure projects including power lines, water pipelines, and sewerage systems.',
        'short_description': 'Survey and mapping for roads and infrastructure projects.',
        'base_price': 60000,
        'duration_estimate': '2–6 weeks',
        'deliverables': 'Alignment Plan\nLongitudinal Profile\nCross-Sections\nVolume Calculations',
        'is_featured': False,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample data for development'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding database...'))

        # ── SERVICE CATEGORIES ────────────────────────────────────────────────
        cat_map = {}
        for cat_data in CATEGORIES:
            cat, created = ServiceCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'icon': cat_data['icon'], 'order': cat_data['order']}
            )
            cat_map[cat.name] = cat
            self.stdout.write(f'  {"Created" if created else "Exists"} category: {cat.name}')

        # ── SERVICES ──────────────────────────────────────────────────────────
        for svc_data in SERVICES:
            cat = cat_map.get(svc_data.pop('category'))
            slug = slugify(svc_data['name'])
            svc, created = Service.objects.get_or_create(
                slug=slug,
                defaults={**svc_data, 'category': cat, 'slug': slug, 'is_active': True}
            )
            self.stdout.write(f'  {"Created" if created else "Exists"} service: {svc.name}')

        # ── ADMIN USER ────────────────────────────────────────────────────────
        admin, created = User.objects.get_or_create(
            email='admin@attributesurvey.co.ke',
            defaults={
                'username': 'admin@attributesurvey.co.ke',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'phone': '+254 700 000 000',
            }
        )
        if created:
            admin.set_password('admin1234')
            admin.save()
        self.stdout.write(f'  {"Created" if created else "Exists"} admin: {admin.email} / admin1234')

        # ── STAFF USER ────────────────────────────────────────────────────────
        staff, created = User.objects.get_or_create(
            email='staff@attributesurvey.co.ke',
            defaults={
                'username': 'staff@attributesurvey.co.ke',
                'first_name': 'Jane',
                'last_name': 'Kamau',
                'role': User.ROLE_STAFF,
                'is_staff': True,
                'phone': '+254 711 000 001',
            }
        )
        if created:
            staff.set_password('staff1234')
            staff.save()
            StaffProfile.objects.create(
                user=staff,
                designation='Senior Surveyor',
                department='Field Operations',
                employee_id='EMP-001',
            )
        self.stdout.write(f'  {"Created" if created else "Exists"} staff: {staff.email} / staff1234')

        # ── CLIENT USER ───────────────────────────────────────────────────────
        client_user, created = User.objects.get_or_create(
            email='client@example.com',
            defaults={
                'username': 'client@example.com',
                'first_name': 'John',
                'last_name': 'Mwangi',
                'role': User.ROLE_CLIENT,
                'phone': '+254 722 000 002',
                'id_number': '12345678',
                'address': '123 Westlands, Nairobi',
            }
        )
        if created:
            client_user.set_password('client1234')
            client_user.save()
        self.stdout.write(f'  {"Created" if created else "Exists"} client: {client_user.email} / client1234')

        self.stdout.write(self.style.SUCCESS('\n✓ Database seeded successfully!\n'))
        self.stdout.write('  Login credentials:')
        self.stdout.write('  Admin:  admin@attributesurvey.co.ke / admin1234')
        self.stdout.write('  Staff:  staff@attributesurvey.co.ke / staff1234  (requires OTP)')
        self.stdout.write('  Client: client@example.com / client1234\n')
