from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from functools import wraps
from quotations.models import Quotation
from quotations.forms import QuotationReviewForm
from projects.models import Project, ProjectStage
from projects.forms import ProjectStageForm
from clients.models import Client


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('staff_login')
        if not request.user.is_staff_member:
            messages.error(request, 'Staff access only.')
            return redirect('home')
        if not request.session.get('staff_authenticated'):
            messages.warning(request, 'Please complete staff authentication.')
            return redirect('staff_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_required
def staff_dashboard(request):
    user = request.user
    # Admin sees all; staff sees only assigned
    if user.is_admin_member:
        projects = Project.objects.all().order_by('-created_at')
        quotations = Quotation.objects.all().order_by('-created_at')
        clients = Client.objects.all()
    else:
        projects = Project.objects.filter(assigned_staff=user).order_by('-created_at')
        client_ids = projects.values_list('client_id', flat=True)
        clients = Client.objects.filter(id__in=client_ids)
        quotations = Quotation.objects.filter(status='pending').order_by('-created_at')

    context = {
        'projects': projects[:8],
        'pending_quotations': quotations.filter(status='pending')[:5],
        'active_projects': projects.filter(status='in_progress').count(),
        'total_clients': clients.count(),
        'completed_projects': projects.filter(status='completed').count(),
        'total_projects': projects.count(),
        'recent_quotations': quotations[:5],
    }
    return render(request, 'staff/dashboard.html', context)


@staff_required
def staff_quotations(request):
    user = request.user
    if user.is_admin_member:
        quotations = Quotation.objects.all().order_by('-created_at')
    else:
        quotations = Quotation.objects.filter(status='pending').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        quotations = quotations.filter(status=status_filter)

    return render(request, 'staff/quotations.html', {'quotations': quotations, 'status_filter': status_filter})


@staff_required
def review_quotation(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    if request.method == 'POST':
        form = QuotationReviewForm(request.POST, instance=quotation)
        if form.is_valid():
            q = form.save(commit=False)
            q.reviewed_by = request.user
            q.reviewed_at = timezone.now()
            if q.status == 'approved':
                q.status = 'awaiting_client'
            q.save()
            # Notify user by email
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                subject='Your Quotation Has Been Reviewed – Attribute Land Survey',
                message=(
                    f'Dear {quotation.user.first_name},\n\n'
                    f'Your quotation for "{quotation.service.name}" has been reviewed.\n'
                    f'Status: {q.get_status_display()}\n'
                    f'Amount: KES {q.quoted_amount:,.2f}\n\n'
                    f'Please log in to your dashboard to view and respond to the quotation.\n\n'
                    f'Attribute Land Survey & Consultants'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[quotation.user.email],
                fail_silently=True,
            )
            messages.success(request, f'Quotation reviewed. Status set to: {q.get_status_display()}')
            return redirect('staff_quotations')
    else:
        form = QuotationReviewForm(instance=quotation)
    return render(request, 'staff/review_quotation.html', {'form': form, 'quotation': quotation})


@staff_required
def staff_projects(request):
    user = request.user
    if user.is_admin_member:
        projects = Project.objects.all().order_by('-created_at')
    else:
        projects = Project.objects.filter(assigned_staff=user).order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        projects = projects.filter(status=status_filter)

    return render(request, 'staff/projects.html', {'projects': projects, 'status_filter': status_filter})


@staff_required
def staff_project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    stages = project.stages.all().order_by('order')
    form = ProjectStageForm()
    return render(request, 'staff/project_detail.html', {
        'project': project, 'stages': stages, 'form': form
    })


@staff_required
def update_project_stage(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        stage_id = request.POST.get('stage_id')
        if stage_id:
            # Update existing stage
            stage = get_object_or_404(ProjectStage, pk=stage_id, project=project)
            form = ProjectStageForm(request.POST, instance=stage)
        else:
            # Create new stage
            form = ProjectStageForm(request.POST)

        if form.is_valid():
            stage = form.save(commit=False)
            stage.project = project
            stage.updated_by = request.user
            if stage.status == 'completed' and not stage.completed_at:
                stage.completed_at = timezone.now()
            stage.save()

            # Update overall project progress
            stages = project.stages.all()
            if stages.exists():
                completed = stages.filter(status='completed').count()
                project.progress_percentage = int((completed / stages.count()) * 100)
                if project.progress_percentage == 100:
                    project.status = 'completed'
                elif project.progress_percentage > 0:
                    project.status = 'in_progress'
                project.save()

            messages.success(request, 'Project stage updated.')
        else:
            messages.error(request, 'Error updating stage.')
    return redirect('staff_project_detail', pk=pk)


@staff_required
def staff_clients(request):
    user = request.user
    if user.is_admin_member:
        clients = Client.objects.all().order_by('-created_at')
    else:
        project_clients = Project.objects.filter(assigned_staff=user).values_list('client_id', flat=True)
        clients = Client.objects.filter(id__in=project_clients)
    return render(request, 'staff/clients.html', {'clients': clients})
