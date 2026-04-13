from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Project, ProjectStage


@login_required
def project_list(request):
    try:
        client = request.user.client_profile
        projects = Project.objects.filter(client=client).order_by('-created_at')
    except Exception:
        projects = Project.objects.none()
    return render(request, 'projects/list.html', {'projects': projects})


@login_required
def project_detail(request, pk):
    try:
        client = request.user.client_profile
        project = get_object_or_404(Project, pk=pk, client=client)
    except Exception:
        from django.http import Http404
        raise Http404
    stages = project.stages.all().order_by('order')
    documents = project.documents.filter(is_public=True)
    return render(request, 'projects/detail.html', {
        'project': project, 'stages': stages, 'documents': documents
    })
