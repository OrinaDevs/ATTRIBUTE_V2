from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Client


@login_required
def client_profile(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        client = None
    return render(request, 'clients/profile.html', {'client': client})
