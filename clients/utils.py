from django.utils import timezone
from clients.models import Client
from payments.models import Invoice


def create_client_from_quotation(quotation):
    """
    When a user accepts a quotation:
    1. Create or fetch their Client profile
    2. Create an Invoice linked to the quotation
    3. Create a Project skeleton
    Returns (client, invoice)
    """
    user = quotation.user

    # Create or get client
    client, created = Client.objects.get_or_create(
        user=user,
        defaults={
            'company_name': '',
            'status': Client.STATUS_ACTIVE,
        }
    )

    # Create invoice
    amount = quotation.quoted_amount or 0
    invoice = Invoice.objects.create(
        client=client,
        quotation=quotation,
        amount=amount,
        description=f'Professional services: {quotation.service.name}\nLocation: {quotation.property_location}',
        due_date=timezone.now().date() + timezone.timedelta(days=14),
        status=Invoice.STATUS_UNPAID,
    )

    # Create project
    from projects.models import Project, ProjectStage
    project = Project.objects.create(
        client=client,
        service=quotation.service,
        quotation=quotation,
        title=f'{quotation.service.name} – {quotation.property_location}',
        description=quotation.description,
        status=Project.STATUS_NOT_STARTED,
        property_location=quotation.property_location,
        property_size=quotation.property_size,
    )

    # Seed stages from service's defined stages, or fall back to defaults
    from projects.models import Project, ProjectStage
    from services.models import ServiceStage
 
    service_stages = list(ServiceStage.objects.filter(service=quotation.service).order_by('order'))
 
    if service_stages:
        stages_to_create = [
            (s.order, s.name, s.description) for s in service_stages
        ]
    else:
        stages_to_create = [
            (1, 'Initial Site Visit & Assessment', 'Staff visits the site for measurements and assessment.'),
            (2, 'Data Collection & Survey', 'Field data collection and surveying work.'),
            (3, 'Data Processing & Analysis', 'Processing collected data in the office.'),
            (4, 'Draft Report / Plan Preparation', 'Preparation of draft documents and plans.'),
            (5, 'Client Review & Approval', 'Client reviews and approves the draft outputs.'),
            (6, 'Final Document Submission', 'Final certified documents submitted to client and relevant authorities.'),
        ]
    for order, name, desc in stages_to_create:
        ProjectStage.objects.create(
            project=project,
            order=order,
            name=name,
            description=desc,
            status='pending',
        )

    return client, invoice